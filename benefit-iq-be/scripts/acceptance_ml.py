"""Persist synthetic ML training, scoring, and validation evidence locally."""

import csv
import json
import shutil
from pathlib import Path

from benefit_iq.infrastructure.ml.redemption import FEATURES, RedemptionModel, batch_score, train

out = Path(__file__).resolve().parents[2] / "artifacts/e2e/ml"
out.mkdir(parents=True, exist_ok=True)
dataset = out / "synthetic.csv"
rows = []
for i in range(80):
    month = "01" if i < 60 else "03"
    rows.append(dict(sample_id=str(i), customer_id=str(i),
                     observed_at=f"2024-{month}-01T00:00:00+00:00",
                     label_observed_at=f"2024-{month}-20T00:00:00+00:00", redeemed=str(i % 2),
                     utilization_ratio=(i % 10)/10, days_remaining=30, remaining_value=100,
                     prior_redemptions=i % 3, category_spend_90d=i*10))


def write(path, data):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(data)


write(dataset, rows)
model_dir = train(dataset, out / "models", "2024-02-01T00:00:00+00:00", "synthetic")
model = RedemptionModel(model_dir)
output = out / "predictions.jsonl"
manifest = batch_score(dataset, model_dir, output)
before = output.stat().st_mtime_ns
assert batch_score(dataset, model_dir, output) == manifest
assert output.stat().st_mtime_ns == before
predictions = [json.loads(line) for line in output.read_text().splitlines()]
assert len(predictions) == 80 and all(0 <= p["redemption_probability"] <= 1 for p in predictions)
results = [dict(case="Train/reload/score 80 rows",result="PASS",metadata=model.metadata),
           dict(case="Identical scoring retry preserves output",result="PASS",manifest=manifest)]


def reject(name, action):
    try:
        action()
    except (ValueError, KeyError) as error:
        results.append(dict(case=name,result="PASS",expected="validation rejection",response=str(error)))
    else:
        results.append(dict(case=name,result="FAIL",response="Invalid input accepted"))


for value in [-1, float("nan"), 1.1]:
    reject(f"Invalid utilization {value}", lambda v=value: model.predict([{**rows[0],"utilization_ratio":v}]))
reject("Missing feature", lambda: model.predict([{}]))
for name, changed in [("invalid_label", {"redeemed":"2"}),
                       ("outcome_before_snapshot", {"label_observed_at":"2023-01-01T00:00:00+00:00"}),
                       ("naive_timestamp", {"observed_at":"2024-01-01T00:00:00"})]:
    path = out / (name+".csv")
    write(path, [{**rows[0], **changed}, *rows[1:]])
    reject(name, lambda p=path: train(p,out/"invalid-models","2024-02-01T00:00:00+00:00","synthetic"))
corrupt = out / "corrupt-model"
shutil.copytree(model_dir, corrupt, dirs_exist_ok=True)
with (corrupt / "model.json").open("a") as stream:
    stream.write(" ")
reject("Corrupt artifact rejected", lambda: RedemptionModel(corrupt))
(out / "results.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
(out / "model-directory.txt").write_text(str(model_dir),encoding="utf-8")
print(json.dumps(results,indent=2))
assert all(r["result"] == "PASS" for r in results)

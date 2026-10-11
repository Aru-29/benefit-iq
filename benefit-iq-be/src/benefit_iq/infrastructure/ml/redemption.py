"""Reproducible XGBoost training and bounded batch inference from labelled snapshots.

Input CSV: sample_id, customer_id, observed_at, label_observed_at, redeemed,
plus FEATURES. Features must contain only information known at observed_at.
"""

import argparse
import csv
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

FEATURES = [
    "utilization_ratio",
    "days_remaining",
    "remaining_value",
    "prior_redemptions",
    "category_spend_90d",
]
SCHEMA_VERSION = 1


def vector(row):
    values = [float(row[name]) for name in FEATURES]
    if not all(math.isfinite(v) and v >= 0 for v in values) or values[0] > 1:
        raise ValueError("Features must be finite, nonnegative; utilization_ratio must be <=1")
    return values


def timestamp(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("Dataset timestamps must be timezone aware")
    return result.astimezone(UTC)


def train(dataset: Path, output: Path, cutoff: str, provenance: str):
    import numpy as np
    import xgboost as xgb
    from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

    if provenance not in ("synthetic", "observed"):
        raise ValueError("Provenance must be synthetic or observed")
    with dataset.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) < 40 or len({r["sample_id"] for r in rows}) != len(rows):
        raise ValueError("Need at least 40 uniquely identified labelled snapshots")
    split_at = timestamp(cutoff)
    holdout = [r for r in rows if timestamp(r["observed_at"]) >= split_at]
    holdout_customers = {r["customer_id"] for r in holdout}
    training = [
        r
        for r in rows
        if timestamp(r["label_observed_at"]) < split_at
        and r["customer_id"] not in holdout_customers
    ]
    for r in rows:
        if timestamp(r["label_observed_at"]) <= timestamp(r["observed_at"]):
            raise ValueError("Outcome must be observed strictly after the feature snapshot")
        if r["redeemed"] not in ("0", "1"):
            raise ValueError("redeemed must be 0 or 1")
    for partition in (training, holdout):
        if len(partition) < 10 or {r["redeemed"] for r in partition} != {"0", "1"}:
            raise ValueError("Both disjoint temporal partitions need >=10 rows and both labels")
    x_train, y_train = (
        np.array([vector(r) for r in training]),
        np.array([int(r["redeemed"]) for r in training]),
    )
    x_test, y_test = (
        np.array([vector(r) for r in holdout]),
        np.array([int(r["redeemed"]) for r in holdout]),
    )
    model = xgb.XGBClassifier(
        n_estimators=80,
        max_depth=3,
        learning_rate=0.05,
        random_state=42,
        n_jobs=1,
        eval_metric="logloss",
    )
    model.fit(x_train, y_train)
    probabilities = model.predict_proba(x_test)[:, 1]
    baseline = np.full(len(y_test), y_train.mean())
    metrics = {
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
        "average_precision": float(average_precision_score(y_test, probabilities)),
        "brier_score": float(brier_score_loss(y_test, probabilities)),
        "log_loss": float(log_loss(y_test, probabilities)),
        "baseline_log_loss": float(log_loss(y_test, baseline)),
    }
    digest = hashlib.sha256(dataset.read_bytes()).hexdigest()
    version = hashlib.sha256(
        (digest + cutoff + str(SCHEMA_VERSION) + xgb.__version__).encode()
    ).hexdigest()[:16]
    directory = output / version
    directory.mkdir(parents=True, exist_ok=True)
    model_path = directory / "model.json"
    model.save_model(model_path)
    metadata = {
        "version": version,
        "schema_version": SCHEMA_VERSION,
        "features": FEATURES,
        "algorithm": "XGBoost",
        "library_version": xgb.__version__,
        "provenance": provenance,
        "dataset_sha256": digest,
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "train_rows": len(training),
        "test_rows": len(holdout),
        "cutoff": cutoff,
        "split": "temporal, customer-disjoint; training outcomes precede cutoff",
        "metrics": metrics,
        "created_at": datetime.now(UTC).isoformat(),
        "production_validated": False,
    }
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return directory


class RedemptionModel:
    """Loads a locally configured XGBoost native artifact, never pickle."""

    def __init__(self, directory: Path):
        import xgboost as xgb

        self.metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        model_path = directory / "model.json"
        if (
            self.metadata["features"] != FEATURES
            or self.metadata["schema_version"] != SCHEMA_VERSION
        ):
            raise ValueError("Model feature schema mismatch")
        if hashlib.sha256(model_path.read_bytes()).hexdigest() != self.metadata["model_sha256"]:
            raise ValueError("Model artifact integrity check failed")
        self.model = xgb.XGBClassifier()
        self.model.load_model(model_path)

    def predict(self, rows):
        import numpy as np

        if not rows:
            return []
        return self.model.predict_proba(np.array([vector(r) for r in rows]))[:, 1].tolist()


def batch_score(dataset: Path, model_directory: Path, output: Path):
    model = RedemptionModel(model_directory)
    version = model.metadata["version"]
    digest = hashlib.sha256(dataset.read_bytes()).hexdigest()
    manifest_path = output.with_suffix(".manifest.json")
    if output.exists() and manifest_path.exists():
        prior = json.loads(manifest_path.read_text())
        if (
            prior.get("input_sha256") == digest
            and prior.get("model_version") == version
            and prior.get("output_sha256") == hashlib.sha256(output.read_bytes()).hexdigest()
        ):
            return prior
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(".pending")
    count = 0
    try:
        with (
            dataset.open(newline="", encoding="utf-8") as source,
            temp.open("w", encoding="utf-8") as target,
        ):
            reader = csv.DictReader(source)
            while True:
                from itertools import islice

                rows = list(islice(reader, 500))
                if not rows:
                    break
                for row, probability in zip(rows, model.predict(rows), strict=True):
                    target.write(
                        json.dumps(
                            {
                                "sample_id": row["sample_id"],
                                "redemption_probability": probability,
                                "model_version": version,
                                "provenance": model.metadata["provenance"],
                            }
                        )
                        + "\n"
                    )
                    count += 1
        temp.replace(output)
    finally:
        temp.unlink(missing_ok=True)
    manifest = {
        "input_sha256": digest,
        "model_version": version,
        "rows": count,
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "status": "complete",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    training = sub.add_parser("train")
    training.add_argument("dataset", type=Path)
    training.add_argument("output", type=Path)
    training.add_argument("--cutoff", required=True)
    training.add_argument("--provenance", choices=["synthetic", "observed"], required=True)
    scoring = sub.add_parser("score")
    scoring.add_argument("dataset", type=Path)
    scoring.add_argument("model", type=Path)
    scoring.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "train":
        print(train(args.dataset, args.output, args.cutoff, args.provenance))
    else:
        print(json.dumps(batch_score(args.dataset, args.model, args.output)))


if __name__ == "__main__":
    main()

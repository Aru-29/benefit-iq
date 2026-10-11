"""Synthetic smoke checks demonstrate plumbing, not real predictive accuracy."""

import csv

import pytest

from benefit_iq.infrastructure.ml.redemption import FEATURES, RedemptionModel, batch_score, train


def test_training_reload_batch_idempotency_and_integrity(tmp_path):
    pytest.importorskip("xgboost")
    dataset = tmp_path / "synthetic.csv"
    fields = ["sample_id", "customer_id", "observed_at", "label_observed_at", "redeemed"] + FEATURES
    with dataset.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for i in range(80):
            month = "01" if i < 60 else "03"
            writer.writerow(
                {
                    "sample_id": str(i),
                    "customer_id": str(i),
                    "observed_at": f"2024-{month}-01T00:00:00+00:00",
                    "label_observed_at": f"2024-{month}-20T00:00:00+00:00",
                    "redeemed": str(i % 2),
                    "utilization_ratio": (i % 10) / 10,
                    "days_remaining": 30,
                    "remaining_value": 100,
                    "prior_redemptions": i % 3,
                    "category_spend_90d": i * 10,
                }
            )
    directory = train(dataset, tmp_path / "models", "2024-02-01T00:00:00+00:00", "synthetic")
    model = RedemptionModel(directory)
    assert model.metadata["train_rows"] == 60
    assert model.metadata["test_rows"] == 20
    assert not model.metadata["production_validated"]
    output = tmp_path / "predictions.jsonl"
    first = batch_score(dataset, directory, output)
    before = output.stat().st_mtime_ns
    assert batch_score(dataset, directory, output) == first
    assert output.stat().st_mtime_ns == before
    assert len(output.read_text().splitlines()) == 80
    with (directory / "model.json").open("a") as stream:
        stream.write(" ")
    with pytest.raises(ValueError, match="integrity"):
        RedemptionModel(directory)

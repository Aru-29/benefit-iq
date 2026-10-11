"""Entitlement evaluation against independently supplied labelled cases."""

import argparse
import hashlib
import json
from pathlib import Path

from pydantic import TypeAdapter

from benefit_iq.application.benefits.rule_engine import BenefitRuleEngine, RuleEvaluationContext
from benefit_iq.domain.entities.benefit_rule import BenefitRule


def evaluate(dataset: Path):
    payload = json.loads(dataset.read_text(encoding="utf-8"))
    if payload.get("provenance") not in ("synthetic", "human_labelled"):
        raise ValueError("Declare synthetic or human_labelled provenance")
    cases = payload["cases"]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Cases must be nonempty and have unique IDs")
    matrix = {"true_positive": 0, "true_negative": 0, "false_positive": 0, "false_negative": 0}
    mismatches = []
    for case in cases:
        if not isinstance(case["expected_entitled"], bool):
            raise ValueError("Expected labels must be booleans")
        context = TypeAdapter(RuleEvaluationContext).validate_python(case["context"])
        rules = TypeAdapter(list[BenefitRule]).validate_python(case["rules"])
        result = BenefitRuleEngine().evaluate(rules, context)
        expected, actual = case["expected_entitled"], result.is_entitled
        key = ("true_" if actual == expected else "false_") + ("positive" if actual else "negative")
        matrix[key] += 1
        if actual != expected:
            mismatches.append({"id": case["id"], "reason": result.explanation})
    return {
        "provenance": payload["provenance"],
        "dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
        "cases": len(cases),
        "accuracy": (matrix["true_positive"] + matrix["true_negative"]) / len(cases),
        "confusion_matrix": matrix,
        "mismatches": mismatches,
        "interpretation": "Fixture correctness only"
        if payload["provenance"] == "synthetic"
        else "Accuracy on supplied labelled cases only",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(evaluate(args.dataset), indent=2), encoding="utf-8")

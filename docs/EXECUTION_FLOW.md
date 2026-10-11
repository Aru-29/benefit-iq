# Benefit and model execution flow

## Utilization and rules

`GET /analytics/me/utilization` and every redemption request trigger `BenefitUtilizationService`. For each caller-owned card it loads linked benefits, selects active rule versions and builds a `RuleEvaluationContext`. `BenefitRuleEngine` fails closed when a card, benefit effective date, activation requirement, currency, spend requirement or condition is invalid. For policies with the same name, the newest version supersedes older versions. Rules are deterministic: their output includes the applied rule id/version and failed conditions.

The result preserves monetary, count and coverage semantics. Monetary benefits calculate remaining decimal value. Count benefits calculate remaining uses. Insurance and protection coverage are never represented as cash. Period calculation is calendar-based and uses an exclusive end boundary.

## Transaction and redemption flow

The transaction endpoint validates ownership, a non-future timestamp and an active card lifetime, then writes a deterministic ID from customer, card and external transaction ID. Retrying an identical request returns the existing event; changing fields for the same external ID fails. A redemption re-runs utilization under a card-benefit lock, rejects unavailable or exhausted benefits, and rejects monetary redemptions above the remaining allowance.

## Nudge delivery

`POST /analytics/me/nudges` derives a stable nudge ID from customer, card, benefit and benefit period. It persists a pending nudge before delivery. The notification boundary then marks in-app reminders sent/delivered immediately. Email delivery is disabled unless the persisted member preference is exactly `benefit_notifications.email: true`; provider failure becomes `failed` without exposing provider details to the member.

## ML lifecycle

The ML service does not train during an API request. Training is an explicit offline command: `python -m benefit_iq.infrastructure.ml.redemption train <labelled.csv> <output> --cutoff <UTC timestamp> --provenance observed`. The input requires unique snapshots, outcomes observed strictly after features, a temporal holdout and customer-disjoint training partition. The artifact is native XGBoost JSON, accompanied by hashes, feature schema, metrics and provenance. API inference loads only an integrity-checked artifact configured by `ML_MODEL_DIRECTORY`; production startup rejects an artifact not separately marked validated. Without an artifact, the prediction endpoint states that no model is available. The recommendation endpoint intentionally remains a transparent heuristic rather than claiming model confidence.

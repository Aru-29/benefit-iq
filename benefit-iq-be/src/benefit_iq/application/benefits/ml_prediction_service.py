"""Explainable deterministic prioritization; never presented as trained ML."""

from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from benefit_iq.domain.entities.ml_model import Prediction
from benefit_iq.domain.enums.benefit_enums import PredictionType, UtilizationStatus


class MLPredictionService:
    def __init__(
        self,
        ml_model_repository,
        prediction_repository,
        benefit_repository,
        card_repository,
        transaction_repository,
        redemption_model=None,
    ):
        self.predictions = prediction_repository
        self.transactions = transaction_repository
        self.model = redemption_model

    async def predict_underutilization_risk(self, customer_id, utilizations):
        result = []
        for u in utilizations:
            if u.status in (
                UtilizationStatus.NOT_ELIGIBLE,
                UtilizationStatus.FULLY_USED,
                UtilizationStatus.EXPIRED,
            ):
                continue
            days = u.days_until_expiry or 0
            score = round(
                0.6 * (1 - float(u.utilization_percentage) / 100)
                + 0.4 * max(0, 1 - min(days, 90) / 90),
                4,
            )
            now = u.calculated_at or datetime.now(UTC)
            result.append(
                Prediction(
                    id=uuid5(
                        NAMESPACE_URL,
                        f"priority-v1:{customer_id}:{u.card_id}:{u.benefit_id}:{u.period_start.isoformat()}:{u.used_value}:{now.date()}",
                    ),
                    model_id=UUID(int=0),
                    prediction_type=PredictionType.OPPORTUNITY_PRIORITY,
                    customer_id=customer_id,
                    card_id=u.card_id,
                    benefit_id=u.benefit_id,
                    score=float(score),
                    confidence=None,
                    explanation=f"Rule-based priority, not a probability. {u.benefit_name}: {u.remaining_value} {u.currency} cash remaining; {days} days left. {u.eligibility_reason}",
                    features_used={
                        "method": "heuristic-v1",
                        "days_remaining": days,
                        "utilization_pct": str(u.utilization_percentage),
                    },
                    predicted_at=now,
                    expires_at=u.expiry_date,
                    created_at=now,
                )
            )
        return sorted(result, key=lambda p: (-p.score, str(p.benefit_id)))

    async def predict_recommendations(self, customer_id, utilizations, limit=5):
        return (await self.predict_underutilization_risk(customer_id, utilizations))[:limit]

    async def predict_redemption(self, customer_id, utilizations):
        if self.model is None:
            return {
                "available": False,
                "reason": "No trained artifact configured",
                "predictions": [],
            }
        from asyncio import to_thread
        from datetime import timedelta

        category_mcc = {
            "travel_credit": "4511",
            "dining_credit": "5812",
            "streaming_credit": "4899",
        }
        candidates, features = [], []
        for u in utilizations:
            if u.status in (
                UtilizationStatus.NOT_ELIGIBLE,
                UtilizationStatus.FULLY_USED,
                UtilizationStatus.EXPIRED,
            ):
                continue
            now = u.calculated_at
            mcc = category_mcc.get(u.benefit_category)
            spend = (
                await self.transactions.get_customer_spend(
                    customer_id,
                    u.card_id,
                    now - timedelta(days=90),
                    now,
                    merchant_category_code=mcc,
                    currency=u.currency,
                )
                if mcc
                else 0
            )
            features.append(
                {
                    "utilization_ratio": float(u.utilization_percentage) / 100,
                    "days_remaining": u.days_until_expiry or 0,
                    "remaining_value": float(u.remaining_value),
                    "prior_redemptions": u.usage_count,
                    "category_spend_90d": float(spend),
                }
            )
            candidates.append(u)
        probabilities = await to_thread(self.model.predict, features)
        return {
            "available": True,
            "model_version": self.model.metadata["version"],
            "provenance": self.model.metadata["provenance"],
            "production_validated": self.model.metadata["production_validated"],
            "predictions": [
                {
                    "card_id": str(u.card_id),
                    "benefit_id": str(u.benefit_id),
                    "redemption_probability": p,
                    "features": f,
                }
                for u, p, f in zip(candidates, probabilities, features, strict=True)
            ],
        }

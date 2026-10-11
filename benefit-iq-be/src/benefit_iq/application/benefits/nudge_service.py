"""In-app reminders with period-specific IDs and explicit user acknowledgement."""

from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

from benefit_iq.domain.entities.nudge import Nudge
from benefit_iq.domain.enums.benefit_enums import (
    NudgeChannel,
    NudgeStatus,
    NudgeType,
    UtilizationStatus,
)


class NudgeService:
    def __init__(
        self,
        nudge_repository,
        offer_repository,
        benefit_repository,
        card_repository,
        notification_service=None,
    ):
        self.repository = nudge_repository
        self.notifications = notification_service

    async def generate_nudges_for_customer(
        self, customer_id, utilizations, risk_predictions=None, channel=NudgeChannel.IN_APP
    ):
        if channel != NudgeChannel.IN_APP:
            raise ValueError("Only in-app delivery is configured")
        now = datetime.now(UTC)
        result = []
        for u in utilizations:
            if u.status not in (UtilizationStatus.UNUSED, UtilizationStatus.PARTIALLY_USED):
                continue
            identifier = uuid5(
                NAMESPACE_URL,
                f"nudge-v1:{customer_id}:{u.card_id}:{u.benefit_id}:{u.period_start.isoformat()}",
            )
            existing = await self.repository.get_by_id(identifier)
            if existing:
                result.append(existing)
                continue
            nudge = Nudge(
                id=identifier,
                customer_id=customer_id,
                card_id=u.card_id,
                benefit_id=u.benefit_id,
                offer_id=None,
                nudge_type=NudgeType.EXPIRY_WARNING
                if u.at_risk_of_expiry
                else NudgeType.BENEFIT_REMINDER,
                channel=channel,
                status=NudgeStatus.PENDING,
                title=u.benefit_name,
                message=f"Review {u.benefit_name} before {u.expiry_date.date()}. Confirm issuer terms before redemption.",
                unused_value=u.remaining_value,
                currency=u.currency,
                reason=u.eligibility_reason,
                ml_score=None,
                prediction_id=None,
                scheduled_at=now,
                sent_at=None,
                delivered_at=None,
                opened_at=None,
                converted_at=None,
                expires_at=u.expiry_date,
                cooldown_until=u.expiry_date,
                created_at=now,
                updated_at=now,
            )
            nudge = await self.repository.create(nudge)
            if self.notifications:
                delivery = await self.notifications.deliver(nudge)
                if delivery.delivered:
                    nudge.mark_sent(now)
                    nudge.mark_delivered(now)
                else:
                    nudge.mark_failed(now)
            elif nudge.channel == NudgeChannel.IN_APP:
                nudge.mark_sent(now)
                nudge.mark_delivered(now)
            else:
                nudge.mark_failed(now)
            nudge = await self.repository.update(nudge)
            result.append(nudge)
        return result

    async def get_customer_nudges(self, customer_id, status=None):
        return await self.repository.get_by_customer(customer_id, status=status, limit=100)

    async def acknowledge(self, customer_id, nudge_id, status):
        nudge = await self.repository.get_by_id(nudge_id)
        if not nudge or nudge.customer_id != customer_id:
            raise LookupError("Nudge not found")
        if status not in (NudgeStatus.OPENED, NudgeStatus.DISMISSED):
            raise ValueError(
                "Customers may open or dismiss reminders; conversions require redemption evidence"
            )
        if nudge.status == NudgeStatus.DISMISSED:
            return nudge
        now = datetime.now(UTC)
        nudge.status = status
        nudge.updated_at = now
        if status == NudgeStatus.OPENED:
            nudge.opened_at = now
        return await self.repository.update(nudge)

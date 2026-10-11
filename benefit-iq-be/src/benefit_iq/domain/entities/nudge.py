"""Nudge domain entity.

Represents a personalized notification/recommendation sent to a customer
about an unused or underutilized benefit.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from benefit_iq.domain.enums.benefit_enums import NudgeChannel, NudgeStatus, NudgeType


@dataclass
class Nudge:
    """A personalized benefit engagement nudge with lifecycle tracking."""

    id: UUID
    customer_id: UUID
    card_id: UUID | None
    benefit_id: UUID | None
    offer_id: UUID | None
    nudge_type: NudgeType
    channel: NudgeChannel
    status: NudgeStatus
    title: str
    message: str
    unused_value: Decimal | None
    currency: str | None
    reason: str
    ml_score: float | None
    prediction_id: UUID | None
    scheduled_at: datetime | None
    sent_at: datetime | None
    delivered_at: datetime | None
    opened_at: datetime | None
    converted_at: datetime | None
    expires_at: datetime | None
    cooldown_until: datetime | None
    created_at: datetime
    updated_at: datetime

    def mark_sent(self, sent_time: datetime) -> None:
        """Mark nudge as sent."""
        self.status = NudgeStatus.SENT
        self.sent_at = sent_time
        self.updated_at = sent_time

    def mark_delivered(self, delivered_time: datetime) -> None:
        """Mark nudge as delivered."""
        self.status = NudgeStatus.DELIVERED
        self.delivered_at = delivered_time
        self.updated_at = delivered_time

    def mark_converted(self, converted_time: datetime) -> None:
        """Mark nudge as having led to benefit engagement."""
        self.status = NudgeStatus.CONVERTED
        self.converted_at = converted_time
        self.updated_at = converted_time

    def mark_dismissed(self, dismissed_time: datetime) -> None:
        """Mark nudge as dismissed by customer."""
        self.status = NudgeStatus.DISMISSED
        self.updated_at = dismissed_time

    def is_expired(self, current_time: datetime) -> bool:
        """Check if nudge has expired."""
        if self.expires_at and current_time > self.expires_at:
            return True
        return False

    def is_in_cooldown(self, current_time: datetime) -> bool:
        """Check if customer is in nudge cooldown period."""
        if self.cooldown_until and current_time < self.cooldown_until:
            return True
        return False

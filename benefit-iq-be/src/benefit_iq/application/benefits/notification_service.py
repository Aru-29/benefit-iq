"""Consent-first delivery for benefit nudges.

External providers are intentionally not selected by a client request. Email is
used only when a member has opted in through their persisted preferences.
"""

from dataclasses import dataclass

from benefit_iq.domain.enums.benefit_enums import NudgeChannel


@dataclass(frozen=True)
class DeliveryResult:
    """The non-sensitive outcome of a single notification delivery attempt."""

    delivered: bool
    reason: str | None = None


class BenefitNotificationService:
    """Delivers nudge notifications through consented channels only."""

    def __init__(self, users, email_service) -> None:
        self._users = users
        self._email = email_service

    async def deliver(self, nudge) -> DeliveryResult:
        """Deliver a nudge, returning a stable operational outcome for persistence."""
        if nudge.channel == NudgeChannel.IN_APP:
            return DeliveryResult(delivered=True)
        if nudge.channel != NudgeChannel.EMAIL:
            return DeliveryResult(delivered=False, reason="Channel is not configured")

        user = await self._users.get_by_id(nudge.customer_id)
        preferences = (user.preferred_settings or {}) if user else {}
        channels = preferences.get("benefit_notifications", {})
        if not isinstance(channels, dict) or channels.get("email") is not True:
            return DeliveryResult(delivered=False, reason="Member has not opted in to email")
        try:
            await self._email.send_benefit_nudge(
                to_email=user.email,
                title=nudge.title,
                message=nudge.message,
                expires_at=nudge.expires_at,
            )
        except Exception:
            return DeliveryResult(delivered=False, reason="Email provider rejected delivery")
        return DeliveryResult(delivered=True)

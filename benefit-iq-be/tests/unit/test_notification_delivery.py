"""Notification channel behavior is consent-first and does not leak provider failures."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from benefit_iq.application.benefits.notification_service import BenefitNotificationService
from benefit_iq.domain.entities.nudge import Nudge
from benefit_iq.domain.enums.benefit_enums import NudgeChannel, NudgeStatus, NudgeType


def nudge(channel: NudgeChannel) -> Nudge:
    now = datetime.now(UTC)
    return Nudge(
        id=uuid4(), customer_id=uuid4(), card_id=None, benefit_id=None, offer_id=None,
        nudge_type=NudgeType.BENEFIT_REMINDER, channel=channel, status=NudgeStatus.PENDING,
        title="Travel credit", message="Use your benefit", unused_value=None, currency=None,
        reason="unused", ml_score=None, prediction_id=None, scheduled_at=now, sent_at=None,
        delivered_at=None, opened_at=None, converted_at=None, expires_at=None,
        cooldown_until=None, created_at=now, updated_at=now,
    )


class Users:
    def __init__(self, settings):
        self.user = SimpleNamespace(email="member@example.test", preferred_settings=settings)

    async def get_by_id(self, _):
        return self.user


class Email:
    def __init__(self):
        self.calls = 0

    async def send_benefit_nudge(self, **_):
        self.calls += 1


@pytest.mark.asyncio
async def test_email_requires_explicit_member_opt_in():
    email = Email()
    service = BenefitNotificationService(Users({}), email)
    result = await service.deliver(nudge(NudgeChannel.EMAIL))
    assert not result.delivered
    assert email.calls == 0


@pytest.mark.asyncio
async def test_in_app_delivery_never_calls_external_provider():
    email = Email()
    result = await BenefitNotificationService(Users({}), email).deliver(nudge(NudgeChannel.IN_APP))
    assert result.delivered
    assert email.calls == 0


@pytest.mark.asyncio
async def test_opted_in_email_is_delivered():
    email = Email()
    result = await BenefitNotificationService(
        Users({"benefit_notifications": {"email": True}}), email
    ).deliver(nudge(NudgeChannel.EMAIL))
    assert result.delivered
    assert email.calls == 1

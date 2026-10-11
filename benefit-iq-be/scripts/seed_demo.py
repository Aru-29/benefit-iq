"""Idempotent synthetic demo catalogue and customer. Local development only."""

import asyncio
import os
from datetime import UTC, datetime
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from benefit_iq.domain.entities.benefit import Benefit
from benefit_iq.domain.entities.benefit_rule import BenefitRule
from benefit_iq.domain.entities.card_product import CardProduct
from benefit_iq.domain.entities.card_product_benefit import CardProductBenefit
from benefit_iq.domain.entities.user import User
from benefit_iq.domain.enums.auth_provider import AuthProvider
from benefit_iq.domain.enums.benefit_enums import (
    BenefitCategory,
    BenefitFrequency,
    BenefitValueType,
    CardNetwork,
    CardTier,
)
from benefit_iq.infrastructure.dependency_injection.container import init_container
from benefit_iq.infrastructure.persistence.clickhouse.initializer import ClickHouseInitializer


def uid(name):
    return uuid5(NAMESPACE_URL, "benefitiq:synthetic-demo:" + name)


async def seed(container=None):
    c = container or init_container()
    settings = c.config()
    if settings.app_env != "development" or settings.clickhouse.host not in (
        "localhost",
        "127.0.0.1",
    ):
        raise RuntimeError("Demo seeding is restricted to a local development database")
    password = os.environ.get("BENEFITIQ_DEMO_PASSWORD")
    if not password or len(password) < 12:
        raise RuntimeError("Set BENEFITIQ_DEMO_PASSWORD to at least 12 characters")
    db = c.clickhouse()
    db.connect()
    await ClickHouseInitializer(db).initialize()
    now = datetime.now(UTC)
    start = datetime(2020, 1, 1, tzinfo=UTC)
    roles = await db.query_async(
        "SELECT id, name FROM benefitiq.roles FINAL WHERE name IN ('CUSTOMER', 'ADMIN')"
    )
    role_ids = {name: rid for rid, name in roles.result_rows}
    for name, role in [("customer", "CUSTOMER"), ("other", "CUSTOMER"), ("admin", "ADMIN")]:
        if not await c.user_repository().get_by_id(uid(name)):
            await c.user_repository().create(
                User(
                    id=uid(name),
                    username="demo-" + name,
                    first_name="Demo",
                    middle_name=None,
                    last_name=name.title(),
                    email=name + "@example.com",
                    password_hash=c.password_hasher().hash_password(password),
                    role_id=role_ids[role],
                    authentication_provider=AuthProvider.LOCAL,
                    external_provider_id=None,
                    is_active=True,
                    is_email_verified=True,
                    preferred_settings={},
                    created_at=now,
                    updated_at=now,
                    last_login_at=None,
                )
            )
    product = CardProduct(
        id=uid("product"),
        name="Demo Explorer",
        issuer_name="Synthetic issuer",
        network=CardNetwork.VISA,
        tier=CardTier.PLATINUM,
        annual_fee=Decimal("100"),
        currency="USD",
        description="Synthetic fixture. Not an offer from a real issuer.",
        is_active=True,
        effective_from=start,
        effective_to=None,
        created_at=now,
        updated_at=now,
    )
    if not await c.card_product_repository().get_by_id(product.id):
        await c.card_product_repository().create(product)
    fixtures = [
        (
            "travel",
            "Travel credit",
            BenefitCategory.TRAVEL_CREDIT,
            BenefitValueType.MONETARY,
            "200",
            BenefitFrequency.ANNUAL,
            None,
        ),
        (
            "streaming",
            "Streaming credit",
            BenefitCategory.STREAMING_CREDIT,
            BenefitValueType.MONETARY,
            "20",
            BenefitFrequency.MONTHLY,
            None,
        ),
        (
            "lounge",
            "Lounge visits",
            BenefitCategory.LOUNGE_ACCESS,
            BenefitValueType.COUNT,
            "4",
            BenefitFrequency.QUARTERLY,
            4,
        ),
        (
            "protection",
            "Purchase protection",
            BenefitCategory.PURCHASE_PROTECTION,
            BenefitValueType.UNLIMITED,
            "0",
            BenefitFrequency.ANNUAL,
            None,
        ),
    ]
    for key, name, category, value_type, amount, frequency, limit in fixtures:
        benefit = Benefit(
            id=uid(key),
            name=name,
            description="Synthetic demonstration benefit",
            category=category,
            value_type=value_type,
            max_value=Decimal(amount),
            currency="USD",
            frequency=frequency,
            requires_activation=False,
            activation_instructions=None,
            terms_and_conditions="Demo terms only. Coverage is not cash value.",
            is_active=True,
            effective_from=start,
            effective_to=None,
            created_at=now,
            updated_at=now,
        )
        if not await c.benefit_repository().get_by_id(benefit.id):
            await c.benefit_repository().create(benefit)
        mappings = await c.card_product_benefit_repository().get_benefits_for_product(product.id)
        if not any(m.benefit_id == benefit.id for m in mappings):
            await c.card_product_benefit_repository().create(
                CardProductBenefit(uid("map:" + key), product.id, benefit.id, True, now, now)
            )
        if not await c.benefit_rule_repository().get_by_id(uid("rule:" + key)):
            await c.benefit_rule_repository().create(
                BenefitRule(
                    id=uid("rule:" + key),
                    benefit_id=benefit.id,
                    card_product_id=product.id,
                    name="Demo entitlement",
                    description="Synthetic rule v1",
                    version=1,
                    priority=100,
                    usage_limit=limit,
                    effective_from=start,
                    created_at=now,
                    updated_at=now,
                )
            )
    if container is None:
        db.close()
    return uid("customer"), product.id


if __name__ == "__main__":
    asyncio.run(seed())
    print("Synthetic catalogue and demo accounts are ready. Login OTPs go to local Mailpit.")

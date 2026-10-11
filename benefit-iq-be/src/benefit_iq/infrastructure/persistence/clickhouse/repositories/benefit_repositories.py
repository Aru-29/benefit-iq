"""ClickHouse repository implementations for BenefitIQ business entities.

Provides concrete persistence for card products, cards, benefits, benefit rules,
merchants, transactions, benefit usage, offers, nudges, ML models, and predictions.
All repositories use parameterized queries and async execution.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog

from benefit_iq.application.contracts.repositories.benefit_repositories import (
    BenefitRepository,
    BenefitRuleRepository,
    BenefitUsageRepository,
    CardProductBenefitRepository,
    CardProductRepository,
    CardRepository,
    MerchantRepository,
    MLModelRepository,
    NudgeRepository,
    OfferRepository,
    PredictionRepository,
    TransactionRepository,
)
from benefit_iq.domain.entities.benefit import Benefit
from benefit_iq.domain.entities.benefit_rule import BenefitRule, RuleCondition
from benefit_iq.domain.entities.benefit_usage import BenefitUsage
from benefit_iq.domain.entities.card import Card
from benefit_iq.domain.entities.card_product import CardProduct
from benefit_iq.domain.entities.card_product_benefit import CardProductBenefit
from benefit_iq.domain.entities.merchant import Merchant
from benefit_iq.domain.entities.ml_model import MLModel, Prediction
from benefit_iq.domain.entities.nudge import Nudge
from benefit_iq.domain.entities.offer import Offer
from benefit_iq.domain.entities.transaction import Transaction
from benefit_iq.domain.enums.benefit_enums import (
    BenefitCategory,
    BenefitFrequency,
    BenefitValueType,
    CardNetwork,
    CardStatus,
    CardTier,
    ModelStatus,
    NudgeChannel,
    NudgeStatus,
    NudgeType,
    PredictionType,
    TransactionChannel,
    TransactionStatus,
)
from benefit_iq.infrastructure.persistence.clickhouse.database import ClickHouseDatabase

logger = structlog.get_logger(__name__)


def _to_str(val: Any) -> str:
    """Safely convert value to string for ClickHouse insertion."""
    if val is None:
        return ""
    if isinstance(val, UUID):
        return str(val)
    if isinstance(val, Decimal):
        return str(val)
    if isinstance(val, bool):
        return str(int(val))
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    return str(val)


# ─────────────────────────────────────────────────────────────────────────
# Card Product Repository
# ─────────────────────────────────────────────────────────────────────────
class ClickHouseCardProductRepository(CardProductRepository):
    """ClickHouse implementation of CardProductRepository."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        self.db = database

    async def create(self, product: CardProduct) -> CardProduct:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "card_products",
                [
                    [
                        str(product.id),
                        product.name,
                        product.issuer_name,
                        product.network.value,
                        product.tier.value,
                        product.annual_fee,
                        product.currency,
                        product.description or "",
                        1 if product.is_active else 0,
                        product.effective_from,
                        product.effective_to,
                        product.created_at,
                        product.updated_at,
                    ]
                ],
                column_names=[
                    "id",
                    "name",
                    "issuer_name",
                    "network",
                    "tier",
                    "annual_fee",
                    "currency",
                    "description",
                    "is_active",
                    "effective_from",
                    "effective_to",
                    "created_at",
                    "updated_at",
                ],
            ),
        )
        return product

    async def get_by_id(self, product_id: UUID) -> CardProduct | None:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.card_products FINAL WHERE id = %(id)s LIMIT 1",
            {"id": str(product_id)},
        )
        if not result.result_rows:
            return None
        return self._map(result.result_rows[0])

    async def list_all(self, offset: int, limit: int) -> list[CardProduct]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.card_products FINAL WHERE is_active = 1 "
            "ORDER BY issuer_name, name LIMIT %(limit)s OFFSET %(offset)s",
            {"limit": limit, "offset": offset},
        )
        return [self._map(r) for r in result.result_rows]

    list = list_all

    async def update(self, product: CardProduct) -> CardProduct:
        return await self.create(product)

    @staticmethod
    def _map(row: tuple) -> CardProduct:
        row = _utc_row(row)
        return CardProduct(
            id=row[0],
            name=row[1],
            issuer_name=row[2],
            network=CardNetwork(row[3]),
            tier=CardTier(row[4]),
            annual_fee=Decimal(str(row[5])),
            currency=row[6],
            description=row[7] if row[7] else None,
            is_active=bool(row[8]),
            effective_from=row[9],
            effective_to=row[10] if row[10] else None,
            created_at=row[11],
            updated_at=row[12],
        )


# ─────────────────────────────────────────────────────────────────────────
# Card Repository
# ─────────────────────────────────────────────────────────────────────────
class ClickHouseCardRepository(CardRepository):
    """ClickHouse implementation of CardRepository."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        self.db = database

    async def create(self, card: Card) -> Card:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "cards",
                [
                    [
                        str(card.id),
                        str(card.customer_id),
                        str(card.card_product_id),
                        card.card_last_four,
                        card.card_alias or "",
                        card.status.value,
                        card.issued_at,
                        card.expiry_date,
                        card.activated_at,
                        card.cancelled_at,
                        1 if card.is_primary else 0,
                        card.created_at,
                        card.updated_at,
                    ]
                ],
                column_names=[
                    "id",
                    "customer_id",
                    "card_product_id",
                    "card_last_four",
                    "card_alias",
                    "status",
                    "issued_at",
                    "expiry_date",
                    "activated_at",
                    "cancelled_at",
                    "is_primary",
                    "created_at",
                    "updated_at",
                ],
            ),
        )
        return card

    async def get_by_id(self, card_id: UUID) -> Card | None:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.cards FINAL WHERE id = %(id)s LIMIT 1",
            {"id": str(card_id)},
        )
        if not result.result_rows:
            return None
        return self._map(result.result_rows[0])

    async def get_by_customer(self, customer_id: UUID) -> list[Card]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.cards FINAL WHERE customer_id = %(cid)s "
            "ORDER BY is_primary DESC, created_at DESC",
            {"cid": str(customer_id)},
        )
        return [self._map(r) for r in result.result_rows]

    async def update(self, card: Card) -> Card:
        return await self.create(card)

    async def list_all(self, offset: int, limit: int) -> list[Card]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.cards FINAL ORDER BY created_at DESC "
            "LIMIT %(limit)s OFFSET %(offset)s",
            {"limit": limit, "offset": offset},
        )
        return [self._map(r) for r in result.result_rows]

    @staticmethod
    def _map(row: tuple) -> Card:
        row = _utc_row(row)
        return Card(
            id=row[0],
            customer_id=row[1],
            card_product_id=row[2],
            card_last_four=row[3],
            card_alias=row[4] if row[4] else None,
            status=CardStatus(row[5]),
            issued_at=row[6],
            expiry_date=row[7],
            activated_at=row[8] if row[8] else None,
            cancelled_at=row[9] if row[9] else None,
            is_primary=bool(row[10]),
            created_at=row[11],
            updated_at=row[12],
        )


# ─────────────────────────────────────────────────────────────────────────
# Benefit Repository
# ─────────────────────────────────────────────────────────────────────────
class ClickHouseBenefitRepository(BenefitRepository):
    """ClickHouse implementation of BenefitRepository."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        self.db = database

    async def create(self, benefit: Benefit) -> Benefit:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "benefits",
                [
                    [
                        str(benefit.id),
                        benefit.name,
                        benefit.description or "",
                        benefit.category.value,
                        benefit.value_type.value,
                        benefit.max_value,
                        benefit.currency,
                        benefit.frequency.value,
                        1 if benefit.requires_activation else 0,
                        benefit.activation_instructions or "",
                        benefit.terms_and_conditions or "",
                        1 if benefit.is_active else 0,
                        benefit.effective_from,
                        benefit.effective_to,
                        benefit.created_at,
                        benefit.updated_at,
                    ]
                ],
                column_names=[
                    "id",
                    "name",
                    "description",
                    "category",
                    "value_type",
                    "max_value",
                    "currency",
                    "frequency",
                    "requires_activation",
                    "activation_instructions",
                    "terms_and_conditions",
                    "is_active",
                    "effective_from",
                    "effective_to",
                    "created_at",
                    "updated_at",
                ],
            ),
        )
        return benefit

    async def get_by_id(self, benefit_id: UUID) -> Benefit | None:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.benefits FINAL WHERE id = %(id)s LIMIT 1",
            {"id": str(benefit_id)},
        )
        if not result.result_rows:
            return None
        return self._map(result.result_rows[0])

    async def get_by_card_product(self, card_product_id: UUID) -> list[Benefit]:
        result = await self.db.query_async(
            "SELECT b.* FROM benefitiq.benefits b FINAL "
            "INNER JOIN benefitiq.card_product_benefits cpb FINAL "
            "ON b.id = cpb.benefit_id "
            "WHERE cpb.card_product_id = %(cpid)s AND b.is_active = 1 AND cpb.is_active = 1",
            {"cpid": str(card_product_id)},
        )
        return [self._map(r) for r in result.result_rows]

    async def list_all(self, offset: int, limit: int) -> list[Benefit]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.benefits FINAL WHERE is_active = 1 "
            "ORDER BY category, name LIMIT %(limit)s OFFSET %(offset)s",
            {"limit": limit, "offset": offset},
        )
        return [self._map(r) for r in result.result_rows]

    async def update(self, benefit: Benefit) -> Benefit:
        return await self.create(benefit)

    @staticmethod
    def _map(row: tuple) -> Benefit:
        row = _utc_row(row)
        return Benefit(
            id=row[0],
            name=row[1],
            description=row[2] if row[2] else None,
            category=BenefitCategory(row[3]),
            value_type=BenefitValueType(row[4]),
            max_value=Decimal(str(row[5])),
            currency=row[6],
            frequency=BenefitFrequency(row[7]),
            requires_activation=bool(row[8]),
            activation_instructions=row[9] if row[9] else None,
            terms_and_conditions=row[10] if row[10] else None,
            is_active=bool(row[11]),
            effective_from=row[12],
            effective_to=row[13] if row[13] else None,
            created_at=row[14],
            updated_at=row[15],
        )


# ─────────────────────────────────────────────────────────────────────────
# Benefit Rule Repository
# ─────────────────────────────────────────────────────────────────────────
class ClickHouseBenefitRuleRepository(BenefitRuleRepository):
    """ClickHouse implementation of BenefitRuleRepository."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        self.db = database

    async def create(self, rule: BenefitRule) -> BenefitRule:
        conditions_json = json.dumps(
            [
                {
                    "condition_type": c.condition_type.value,
                    "operator": c.operator.value,
                    "value": c.value,
                    "value_to": c.value_to,
                }
                for c in rule.conditions
            ]
        )
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "benefit_rules",
                [
                    [
                        str(rule.id),
                        str(rule.benefit_id),
                        str(rule.card_product_id) if rule.card_product_id else None,
                        rule.name,
                        rule.description or "",
                        rule.version,
                        rule.priority,
                        conditions_json,
                        rule.min_spend_amount,
                        rule.max_spend_amount,
                        rule.spend_currency,
                        rule.spend_period_days,
                        rule.usage_limit,
                        rule.monthly_limit,
                        rule.quarterly_limit,
                        rule.annual_limit,
                        rule.effective_from,
                        rule.effective_to,
                        1 if rule.is_active else 0,
                        rule.created_at,
                        rule.updated_at,
                    ]
                ],
                column_names=[
                    "id",
                    "benefit_id",
                    "card_product_id",
                    "name",
                    "description",
                    "version",
                    "priority",
                    "conditions",
                    "min_spend_amount",
                    "max_spend_amount",
                    "spend_currency",
                    "spend_period_days",
                    "usage_limit",
                    "monthly_limit",
                    "quarterly_limit",
                    "annual_limit",
                    "effective_from",
                    "effective_to",
                    "is_active",
                    "created_at",
                    "updated_at",
                ],
            ),
        )
        return rule

    async def get_by_id(self, rule_id: UUID) -> BenefitRule | None:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.benefit_rules FINAL WHERE id = %(id)s LIMIT 1",
            {"id": str(rule_id)},
        )
        if not result.result_rows:
            return None
        return self._map(result.result_rows[0])

    async def get_by_benefit(self, benefit_id: UUID) -> list[BenefitRule]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.benefit_rules FINAL "
            "WHERE benefit_id = %(bid)s ORDER BY priority, version DESC",
            {"bid": str(benefit_id)},
        )
        return [self._map(r) for r in result.result_rows]

    async def get_active_rules(
        self,
        benefit_id: UUID,
        card_product_id: UUID | None = None,
    ) -> list[BenefitRule]:
        query = (
            "SELECT * FROM benefitiq.benefit_rules FINAL "
            "WHERE benefit_id = %(bid)s AND is_active = 1"
        )
        params: dict[str, Any] = {"bid": str(benefit_id)}
        if card_product_id:
            query += " AND (card_product_id = %(cpid)s OR card_product_id IS NULL)"
            params["cpid"] = str(card_product_id)
        query += " ORDER BY priority, version DESC"
        result = await self.db.query_async(query, params)
        return [self._map(r) for r in result.result_rows]

    async def update(self, rule: BenefitRule) -> BenefitRule:
        return await self.create(rule)

    async def list_all(self, offset: int, limit: int) -> list[BenefitRule]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.benefit_rules FINAL "
            "ORDER BY benefit_id, priority LIMIT %(limit)s OFFSET %(offset)s",
            {"limit": limit, "offset": offset},
        )
        return [self._map(r) for r in result.result_rows]

    @staticmethod
    def _map(row: tuple) -> BenefitRule:
        from benefit_iq.domain.enums.benefit_enums import RuleConditionType, RuleOperator

        conditions_raw = json.loads(row[7]) if row[7] else []
        conditions = [
            RuleCondition(
                condition_type=RuleConditionType(c["condition_type"]),
                operator=RuleOperator(c["operator"]),
                value=c["value"],
                value_to=c.get("value_to"),
            )
            for c in conditions_raw
        ]
        row = _utc_row(row)
        return BenefitRule(
            id=row[0],
            benefit_id=row[1],
            card_product_id=row[2] if row[2] else None,
            name=row[3],
            description=row[4] if row[4] else None,
            version=row[5],
            priority=row[6],
            conditions=conditions,
            min_spend_amount=Decimal(str(row[8])) if row[8] else None,
            max_spend_amount=Decimal(str(row[9])) if row[9] else None,
            spend_currency=row[10] if row[10] else None,
            spend_period_days=row[11] if row[11] else None,
            usage_limit=row[12] if row[12] else None,
            monthly_limit=row[13] if row[13] else None,
            quarterly_limit=row[14] if row[14] else None,
            annual_limit=row[15] if row[15] else None,
            effective_from=row[16] if row[16] else None,
            effective_to=row[17] if row[17] else None,
            is_active=bool(row[18]),
            created_at=row[19],
            updated_at=row[20],
        )


# ─────────────────────────────────────────────────────────────────────────
# Card Product Benefit Repository
# ─────────────────────────────────────────────────────────────────────────
class ClickHouseCardProductBenefitRepository(CardProductBenefitRepository):
    """ClickHouse implementation of CardProductBenefitRepository."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        self.db = database

    async def create(self, mapping: CardProductBenefit) -> CardProductBenefit:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "card_product_benefits",
                [
                    [
                        str(mapping.id),
                        str(mapping.card_product_id),
                        str(mapping.benefit_id),
                        1 if mapping.is_active else 0,
                        mapping.created_at,
                        mapping.updated_at,
                    ]
                ],
                column_names=[
                    "id",
                    "card_product_id",
                    "benefit_id",
                    "is_active",
                    "created_at",
                    "updated_at",
                ],
            ),
        )
        return mapping

    async def get_benefits_for_product(self, card_product_id: UUID) -> list[CardProductBenefit]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.card_product_benefits FINAL "
            "WHERE card_product_id = %(cpid)s AND is_active = 1",
            {"cpid": str(card_product_id)},
        )
        return [
            CardProductBenefit(
                id=r[0],
                card_product_id=r[1],
                benefit_id=r[2],
                is_active=bool(r[3]),
                created_at=r[4],
                updated_at=r[5],
            )
            for r in result.result_rows
        ]

    async def delete(self, mapping_id: UUID) -> bool:
        # Soft delete via insert with is_active=0
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.card_product_benefits FINAL WHERE id = %(id)s",
            {"id": str(mapping_id)},
        )
        if not result.result_rows:
            return False
        row = result.result_rows[0]
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "card_product_benefits",
                [[str(row[0]), str(row[1]), str(row[2]), 0, row[4], datetime.utcnow()]],
                column_names=[
                    "id",
                    "card_product_id",
                    "benefit_id",
                    "is_active",
                    "created_at",
                    "updated_at",
                ],
            ),
        )
        return True


# ─────────────────────────────────────────────────────────────────────────
# Merchant Repository
# ─────────────────────────────────────────────────────────────────────────
class ClickHouseMerchantRepository(MerchantRepository):
    """ClickHouse implementation of MerchantRepository."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        self.db = database

    async def create(self, merchant: Merchant) -> Merchant:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "merchants",
                [
                    [
                        str(merchant.id),
                        merchant.name,
                        merchant.merchant_category_code,
                        merchant.category_name,
                        merchant.country or "",
                        merchant.city or "",
                        1 if merchant.is_active else 0,
                        merchant.created_at,
                        merchant.updated_at,
                    ]
                ],
                column_names=[
                    "id",
                    "name",
                    "merchant_category_code",
                    "category_name",
                    "country",
                    "city",
                    "is_active",
                    "created_at",
                    "updated_at",
                ],
            ),
        )
        return merchant

    async def get_by_id(self, merchant_id: UUID) -> Merchant | None:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.merchants FINAL WHERE id = %(id)s LIMIT 1",
            {"id": str(merchant_id)},
        )
        if not result.result_rows:
            return None
        return self._map(result.result_rows[0])

    async def get_by_mcc(self, mcc: str) -> list[Merchant]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.merchants FINAL WHERE merchant_category_code = %(mcc)s",
            {"mcc": mcc},
        )
        return [self._map(r) for r in result.result_rows]

    async def list_all(self, offset: int, limit: int) -> list[Merchant]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.merchants FINAL WHERE is_active = 1 "
            "ORDER BY name LIMIT %(limit)s OFFSET %(offset)s",
            {"limit": limit, "offset": offset},
        )
        return [self._map(r) for r in result.result_rows]

    async def update(self, merchant: Merchant) -> Merchant:
        return await self.create(merchant)

    @staticmethod
    def _map(row: tuple) -> Merchant:
        row = _utc_row(row)
        return Merchant(
            id=row[0],
            name=row[1],
            merchant_category_code=row[2],
            category_name=row[3],
            country=row[4] if row[4] else None,
            city=row[5] if row[5] else None,
            is_active=bool(row[6]),
            created_at=row[7],
            updated_at=row[8],
        )


# ─────────────────────────────────────────────────────────────────────────
# Transaction Repository
# ─────────────────────────────────────────────────────────────────────────
class ClickHouseTransactionRepository(TransactionRepository):
    """ClickHouse implementation of TransactionRepository."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        self.db = database

    async def create(self, transaction: Transaction) -> Transaction:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "transactions",
                [self._to_row(transaction)],
                column_names=self._columns(),
            ),
        )
        return transaction

    async def create_batch(self, transactions: list[Transaction]) -> int:
        if not transactions:
            return 0
        loop = asyncio.get_running_loop()
        rows = [self._to_row(t) for t in transactions]
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert("transactions", rows, column_names=self._columns()),
        )
        return len(rows)

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.transactions FINAL WHERE id = %(id)s LIMIT 1",
            {"id": str(transaction_id)},
        )
        if not result.result_rows:
            return None
        return self._map(result.result_rows[0])

    async def get_by_idempotency_key(self, key: str) -> Transaction | None:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.transactions FINAL WHERE idempotency_key = %(key)s LIMIT 1",
            {"key": key},
        )
        if not result.result_rows:
            return None
        return self._map(result.result_rows[0])

    async def get_by_customer(
        self,
        customer_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Transaction]:
        query = "SELECT * FROM benefitiq.transactions FINAL WHERE customer_id = %(cid)s"
        params: dict[str, Any] = {"cid": str(customer_id)}
        if start_date:
            query += " AND transaction_date >= %(start)s"
            params["start"] = start_date
        if end_date:
            query += " AND transaction_date < %(end)s AND currency = %(currency)s"
            params["end"] = end_date
        query += " ORDER BY transaction_date DESC LIMIT %(limit)s OFFSET %(offset)s"
        params["limit"] = limit
        params["offset"] = offset
        result = await self.db.query_async(query, params)
        return [self._map(r) for r in result.result_rows]

    async def get_customer_spend(
        self,
        customer_id: UUID,
        card_id: UUID | None,
        start_date: datetime,
        end_date: datetime,
        merchant_category_code: str | None = None,
        currency: str = "USD",
    ) -> Decimal:
        query = (
            "SELECT sum(amount) FROM benefitiq.transactions FINAL "
            "WHERE customer_id = %(cid)s AND status = 'posted' "
            "AND transaction_date >= %(start)s AND transaction_date < %(end)s AND currency = %(currency)s"
        )
        params: dict[str, Any] = {
            "cid": str(customer_id),
            "start": start_date,
            "end": end_date,
            "currency": currency,
        }
        if card_id:
            query += " AND card_id = %(card_id)s"
            params["card_id"] = str(card_id)
        if merchant_category_code:
            query += " AND merchant_category_code = %(mcc)s"
            params["mcc"] = merchant_category_code
        result = await self.db.query_async(query, params)
        if result.result_rows and result.result_rows[0][0]:
            return Decimal(str(result.result_rows[0][0]))
        return Decimal("0")

    async def list_all(self, offset: int, limit: int) -> list[Transaction]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.transactions FINAL "
            "ORDER BY transaction_date DESC LIMIT %(limit)s OFFSET %(offset)s",
            {"limit": limit, "offset": offset},
        )
        return [self._map(r) for r in result.result_rows]

    @staticmethod
    def _columns() -> list[str]:
        return [
            "id",
            "external_transaction_id",
            "customer_id",
            "card_id",
            "merchant_id",
            "merchant_name",
            "merchant_category_code",
            "amount",
            "currency",
            "transaction_date",
            "posted_date",
            "status",
            "channel",
            "description",
            "country",
            "city",
            "is_recurring",
            "source_system",
            "idempotency_key",
            "created_at",
            "updated_at",
        ]

    @staticmethod
    def _to_row(t: Transaction) -> list:
        return [
            str(t.id),
            t.external_transaction_id,
            str(t.customer_id),
            str(t.card_id),
            str(t.merchant_id) if t.merchant_id else None,
            t.merchant_name or "",
            t.merchant_category_code or "",
            t.amount,
            t.currency,
            t.transaction_date,
            t.posted_date,
            t.status.value,
            t.channel.value,
            t.description or "",
            t.country or "",
            t.city or "",
            1 if t.is_recurring else 0,
            t.source_system,
            t.idempotency_key,
            t.created_at,
            t.updated_at,
        ]

    @staticmethod
    def _map(row: tuple) -> Transaction:
        row = _utc_row(row)
        return Transaction(
            id=row[0],
            external_transaction_id=row[1],
            customer_id=row[2],
            card_id=row[3],
            merchant_id=row[4] if row[4] else None,
            merchant_name=row[5] if row[5] else None,
            merchant_category_code=row[6] if row[6] else None,
            amount=Decimal(str(row[7])),
            currency=row[8],
            transaction_date=row[9],
            posted_date=row[10] if row[10] else None,
            status=TransactionStatus(row[11]),
            channel=TransactionChannel(row[12]),
            description=row[13] if row[13] else None,
            country=row[14] if row[14] else None,
            city=row[15] if row[15] else None,
            is_recurring=bool(row[16]),
            source_system=row[17],
            idempotency_key=row[18],
            created_at=row[19],
            updated_at=row[20],
        )


# ─────────────────────────────────────────────────────────────────────────
# Benefit Usage Repository
# ─────────────────────────────────────────────────────────────────────────
class ClickHouseBenefitUsageRepository(BenefitUsageRepository):
    """ClickHouse implementation of BenefitUsageRepository."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        self.db = database

    async def create(self, usage: BenefitUsage) -> BenefitUsage:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "benefit_usage",
                [
                    [
                        str(usage.id),
                        str(usage.customer_id),
                        str(usage.card_id),
                        str(usage.benefit_id),
                        str(usage.transaction_id) if usage.transaction_id else None,
                        usage.usage_date,
                        usage.value_used,
                        usage.currency,
                        usage.description or "",
                        usage.source_system,
                        usage.created_at,
                    ]
                ],
                column_names=[
                    "id",
                    "customer_id",
                    "card_id",
                    "benefit_id",
                    "transaction_id",
                    "usage_date",
                    "value_used",
                    "currency",
                    "description",
                    "source_system",
                    "created_at",
                ],
            ),
        )
        return usage

    async def get_usage_for_customer_benefit(
        self,
        customer_id: UUID,
        benefit_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[BenefitUsage]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.benefit_usage "
            "WHERE customer_id = %(cid)s AND benefit_id = %(bid)s "
            "AND usage_date >= %(start)s AND usage_date < %(end)s "
            "ORDER BY usage_date DESC LIMIT 1 BY id",
            {"cid": str(customer_id), "bid": str(benefit_id), "start": start_date, "end": end_date},
        )
        return [self._map(r) for r in result.result_rows]

    async def get_usage_summary(
        self,
        customer_id: UUID,
        benefit_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> tuple[int, Decimal]:
        result = await self.db.query_async(
            "SELECT count(), sum(value_used) FROM benefitiq.benefit_usage "
            "WHERE customer_id = %(cid)s AND benefit_id = %(bid)s "
            "AND usage_date >= %(start)s AND usage_date < %(end)s",
            {"cid": str(customer_id), "bid": str(benefit_id), "start": start_date, "end": end_date},
        )
        if result.result_rows:
            count = result.result_rows[0][0] or 0
            total = (
                Decimal(str(result.result_rows[0][1])) if result.result_rows[0][1] else Decimal("0")
            )
            return count, total
        return 0, Decimal("0")

    async def list_all(self, offset: int, limit: int) -> list[BenefitUsage]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.benefit_usage "
            "ORDER BY usage_date DESC LIMIT %(limit)s OFFSET %(offset)s",
            {"limit": limit, "offset": offset},
        )
        return [self._map(r) for r in result.result_rows]

    @staticmethod
    def _map(row: tuple) -> BenefitUsage:
        row = _utc_row(row)
        return BenefitUsage(
            id=row[0],
            customer_id=row[1],
            card_id=row[2],
            benefit_id=row[3],
            transaction_id=row[4] if row[4] else None,
            usage_date=row[5],
            value_used=Decimal(str(row[6])),
            currency=row[7],
            description=row[8] if row[8] else None,
            source_system=row[9],
            created_at=row[10],
        )


# ─────────────────────────────────────────────────────────────────────────
# Offer Repository
# ─────────────────────────────────────────────────────────────────────────
class ClickHouseOfferRepository(OfferRepository):
    """ClickHouse implementation of OfferRepository."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        self.db = database

    async def create(self, offer: Offer) -> Offer:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "offers",
                [
                    [
                        str(offer.id),
                        offer.name,
                        offer.description or "",
                        str(offer.merchant_id) if offer.merchant_id else None,
                        str(offer.card_product_id) if offer.card_product_id else None,
                        str(offer.benefit_id) if offer.benefit_id else None,
                        offer.value_type.value,
                        offer.value_amount,
                        offer.currency,
                        offer.min_transaction_amount,
                        offer.max_redemptions,
                        offer.current_redemptions,
                        offer.coupon_code or "",
                        offer.effective_from,
                        offer.effective_to,
                        1 if offer.is_active else 0,
                        offer.created_at,
                        offer.updated_at,
                    ]
                ],
                column_names=[
                    "id",
                    "name",
                    "description",
                    "merchant_id",
                    "card_product_id",
                    "benefit_id",
                    "value_type",
                    "value_amount",
                    "currency",
                    "min_transaction_amount",
                    "max_redemptions",
                    "current_redemptions",
                    "coupon_code",
                    "effective_from",
                    "effective_to",
                    "is_active",
                    "created_at",
                    "updated_at",
                ],
            ),
        )
        return offer

    async def get_by_id(self, offer_id: UUID) -> Offer | None:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.offers FINAL WHERE id = %(id)s LIMIT 1",
            {"id": str(offer_id)},
        )
        if not result.result_rows:
            return None
        return self._map(result.result_rows[0])

    async def get_active_offers(
        self,
        card_product_id: UUID | None = None,
        merchant_id: UUID | None = None,
    ) -> list[Offer]:
        query = "SELECT * FROM benefitiq.offers FINAL WHERE is_active = 1"
        params: dict[str, Any] = {}
        if card_product_id:
            query += " AND card_product_id = %(cpid)s"
            params["cpid"] = str(card_product_id)
        if merchant_id:
            query += " AND merchant_id = %(mid)s"
            params["mid"] = str(merchant_id)
        result = await self.db.query_async(query, params)
        return [self._map(r) for r in result.result_rows]

    async def update(self, offer: Offer) -> Offer:
        return await self.create(offer)

    async def list_all(self, offset: int, limit: int) -> list[Offer]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.offers FINAL WHERE is_active = 1 "
            "ORDER BY name LIMIT %(limit)s OFFSET %(offset)s",
            {"limit": limit, "offset": offset},
        )
        return [self._map(r) for r in result.result_rows]

    @staticmethod
    def _map(row: tuple) -> Offer:
        row = _utc_row(row)
        return Offer(
            id=row[0],
            name=row[1],
            description=row[2] if row[2] else None,
            merchant_id=row[3] if row[3] else None,
            card_product_id=row[4] if row[4] else None,
            benefit_id=row[5] if row[5] else None,
            value_type=BenefitValueType(row[6]),
            value_amount=Decimal(str(row[7])),
            currency=row[8],
            min_transaction_amount=Decimal(str(row[9])) if row[9] else None,
            max_redemptions=row[10] if row[10] else None,
            current_redemptions=row[11],
            coupon_code=row[12] if row[12] else None,
            effective_from=row[13],
            effective_to=row[14] if row[14] else None,
            is_active=bool(row[15]),
            created_at=row[16],
            updated_at=row[17],
        )


# ─────────────────────────────────────────────────────────────────────────
# Nudge Repository
# ─────────────────────────────────────────────────────────────────────────
class ClickHouseNudgeRepository(NudgeRepository):
    """ClickHouse implementation of NudgeRepository."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        self.db = database

    async def create(self, nudge: Nudge) -> Nudge:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "nudges",
                [
                    [
                        str(nudge.id),
                        str(nudge.customer_id),
                        str(nudge.card_id) if nudge.card_id else None,
                        str(nudge.benefit_id) if nudge.benefit_id else None,
                        str(nudge.offer_id) if nudge.offer_id else None,
                        nudge.nudge_type.value,
                        nudge.channel.value,
                        nudge.status.value,
                        nudge.title,
                        nudge.message,
                        nudge.unused_value,
                        nudge.currency,
                        nudge.reason,
                        nudge.ml_score,
                        str(nudge.prediction_id) if nudge.prediction_id else None,
                        nudge.scheduled_at,
                        nudge.sent_at,
                        nudge.delivered_at,
                        nudge.opened_at,
                        nudge.converted_at,
                        nudge.expires_at,
                        nudge.cooldown_until,
                        nudge.created_at,
                        nudge.updated_at,
                    ]
                ],
                column_names=[
                    "id",
                    "customer_id",
                    "card_id",
                    "benefit_id",
                    "offer_id",
                    "nudge_type",
                    "channel",
                    "status",
                    "title",
                    "message",
                    "unused_value",
                    "currency",
                    "reason",
                    "ml_score",
                    "prediction_id",
                    "scheduled_at",
                    "sent_at",
                    "delivered_at",
                    "opened_at",
                    "converted_at",
                    "expires_at",
                    "cooldown_until",
                    "created_at",
                    "updated_at",
                ],
            ),
        )
        return nudge

    async def get_by_id(self, nudge_id: UUID) -> Nudge | None:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.nudges FINAL WHERE id = %(id)s LIMIT 1",
            {"id": str(nudge_id)},
        )
        if not result.result_rows:
            return None
        return self._map(result.result_rows[0])

    async def get_by_customer(
        self,
        customer_id: UUID,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Nudge]:
        query = "SELECT * FROM benefitiq.nudges FINAL WHERE customer_id = %(cid)s"
        params: dict[str, Any] = {"cid": str(customer_id)}
        if status:
            query += " AND status = %(status)s"
            params["status"] = status
        query += " ORDER BY created_at DESC LIMIT %(limit)s OFFSET %(offset)s"
        params["limit"] = limit
        params["offset"] = offset
        result = await self.db.query_async(query, params)
        return [self._map(r) for r in result.result_rows]

    async def get_recent_nudges(
        self,
        customer_id: UUID,
        benefit_id: UUID | None,
        since: datetime,
    ) -> list[Nudge]:
        query = (
            "SELECT * FROM benefitiq.nudges FINAL "
            "WHERE customer_id = %(cid)s AND created_at >= %(since)s"
        )
        params: dict[str, Any] = {"cid": str(customer_id), "since": since}
        if benefit_id:
            query += " AND benefit_id = %(bid)s"
            params["bid"] = str(benefit_id)
        result = await self.db.query_async(query, params)
        return [self._map(r) for r in result.result_rows]

    async def update(self, nudge: Nudge) -> Nudge:
        return await self.create(nudge)

    async def list_all(self, offset: int, limit: int) -> list[Nudge]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.nudges FINAL "
            "ORDER BY created_at DESC LIMIT %(limit)s OFFSET %(offset)s",
            {"limit": limit, "offset": offset},
        )
        return [self._map(r) for r in result.result_rows]

    list = list_all

    @staticmethod
    def _map(row: tuple) -> Nudge:
        row = _utc_row(row)
        return Nudge(
            id=row[0],
            customer_id=row[1],
            card_id=row[2] if row[2] else None,
            benefit_id=row[3] if row[3] else None,
            offer_id=row[4] if row[4] else None,
            nudge_type=NudgeType(row[5]),
            channel=NudgeChannel(row[6]),
            status=NudgeStatus(row[7]),
            title=row[8],
            message=row[9],
            unused_value=Decimal(str(row[10])) if row[10] else None,
            currency=row[11] if row[11] else None,
            reason=row[12] if row[12] else "",
            ml_score=row[13] if row[13] else None,
            prediction_id=row[14] if row[14] else None,
            scheduled_at=row[15] if row[15] else None,
            sent_at=row[16] if row[16] else None,
            delivered_at=row[17] if row[17] else None,
            opened_at=row[18] if row[18] else None,
            converted_at=row[19] if row[19] else None,
            expires_at=row[20] if row[20] else None,
            cooldown_until=row[21] if row[21] else None,
            created_at=row[22],
            updated_at=row[23],
        )


# ─────────────────────────────────────────────────────────────────────────
# ML Model Repository
# ─────────────────────────────────────────────────────────────────────────
class ClickHouseMLModelRepository(MLModelRepository):
    """ClickHouse implementation of MLModelRepository."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        self.db = database

    async def create(self, model: MLModel) -> MLModel:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "ml_models",
                [
                    [
                        str(model.id),
                        model.name,
                        model.prediction_type.value,
                        model.version,
                        model.algorithm,
                        model.status.value,
                        json.dumps(model.metrics) if model.metrics else None,
                        json.dumps(model.feature_names) if model.feature_names else None,
                        model.training_data_start,
                        model.training_data_end,
                        model.training_samples,
                        model.model_path,
                        model.description or "",
                        model.created_at,
                        model.updated_at,
                    ]
                ],
                column_names=[
                    "id",
                    "name",
                    "prediction_type",
                    "version",
                    "algorithm",
                    "status",
                    "metrics",
                    "feature_names",
                    "training_data_start",
                    "training_data_end",
                    "training_samples",
                    "model_path",
                    "description",
                    "created_at",
                    "updated_at",
                ],
            ),
        )
        return model

    async def get_by_id(self, model_id: UUID) -> MLModel | None:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.ml_models FINAL WHERE id = %(id)s LIMIT 1",
            {"id": str(model_id)},
        )
        if not result.result_rows:
            return None
        return self._map(result.result_rows[0])

    async def get_deployed_model(self, prediction_type: str) -> MLModel | None:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.ml_models FINAL "
            "WHERE prediction_type = %(pt)s AND status = 'deployed' "
            "ORDER BY updated_at DESC LIMIT 1",
            {"pt": prediction_type},
        )
        if not result.result_rows:
            return None
        return self._map(result.result_rows[0])

    async def update(self, model: MLModel) -> MLModel:
        return await self.create(model)

    async def list_all(self, offset: int, limit: int) -> list[MLModel]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.ml_models FINAL "
            "ORDER BY updated_at DESC LIMIT %(limit)s OFFSET %(offset)s",
            {"limit": limit, "offset": offset},
        )
        return [self._map(r) for r in result.result_rows]

    @staticmethod
    def _map(row: tuple) -> MLModel:
        row = _utc_row(row)
        return MLModel(
            id=row[0],
            name=row[1],
            prediction_type=PredictionType(row[2]),
            version=row[3],
            algorithm=row[4],
            status=ModelStatus(row[5]),
            metrics=json.loads(row[6]) if row[6] else None,
            feature_names=json.loads(row[7]) if row[7] else None,
            training_data_start=row[8] if row[8] else None,
            training_data_end=row[9] if row[9] else None,
            training_samples=row[10] if row[10] else None,
            model_path=row[11] if row[11] else None,
            description=row[12] if row[12] else None,
            created_at=row[13],
            updated_at=row[14],
        )


# ─────────────────────────────────────────────────────────────────────────
# Prediction Repository
# ─────────────────────────────────────────────────────────────────────────
class ClickHousePredictionRepository(PredictionRepository):
    """ClickHouse implementation of PredictionRepository."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        self.db = database

    async def create(self, prediction: Prediction) -> Prediction:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "predictions",
                [self._to_row(prediction)],
                column_names=self._columns(),
            ),
        )
        return prediction

    async def create_batch(self, predictions: list[Prediction]) -> int:
        if not predictions:
            return 0
        loop = asyncio.get_running_loop()
        rows = [self._to_row(p) for p in predictions]
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert("predictions", rows, column_names=self._columns()),
        )
        return len(rows)

    async def get_by_customer(
        self,
        customer_id: UUID,
        prediction_type: str | None = None,
    ) -> list[Prediction]:
        query = "SELECT * FROM benefitiq.predictions WHERE customer_id = %(cid)s"
        params: dict[str, Any] = {"cid": str(customer_id)}
        if prediction_type:
            query += " AND prediction_type = %(pt)s"
            params["pt"] = prediction_type
        query += " ORDER BY predicted_at DESC LIMIT 100"
        result = await self.db.query_async(query, params)
        return [self._map(r) for r in result.result_rows]

    async def get_latest(
        self,
        customer_id: UUID,
        prediction_type: str,
        benefit_id: UUID | None = None,
    ) -> Prediction | None:
        query = (
            "SELECT * FROM benefitiq.predictions "
            "WHERE customer_id = %(cid)s AND prediction_type = %(pt)s"
        )
        params: dict[str, Any] = {"cid": str(customer_id), "pt": prediction_type}
        if benefit_id:
            query += " AND benefit_id = %(bid)s"
            params["bid"] = str(benefit_id)
        query += " ORDER BY predicted_at DESC LIMIT 1"
        result = await self.db.query_async(query, params)
        if not result.result_rows:
            return None
        return self._map(result.result_rows[0])

    async def list_all(self, offset: int, limit: int) -> list[Prediction]:
        result = await self.db.query_async(
            "SELECT * FROM benefitiq.predictions "
            "ORDER BY predicted_at DESC LIMIT %(limit)s OFFSET %(offset)s",
            {"limit": limit, "offset": offset},
        )
        return [self._map(r) for r in result.result_rows]

    list = list_all

    @staticmethod
    def _columns() -> list[str]:
        return [
            "id",
            "model_id",
            "prediction_type",
            "customer_id",
            "card_id",
            "benefit_id",
            "score",
            "confidence",
            "explanation",
            "features_used",
            "predicted_at",
            "expires_at",
            "created_at",
        ]

    @staticmethod
    def _to_row(p: Prediction) -> list:
        return [
            str(p.id),
            str(p.model_id),
            p.prediction_type.value,
            str(p.customer_id),
            str(p.card_id) if p.card_id else None,
            str(p.benefit_id) if p.benefit_id else None,
            p.score,
            p.confidence,
            p.explanation,
            json.dumps(p.features_used) if p.features_used else None,
            p.predicted_at,
            p.expires_at,
            p.created_at,
        ]

    @staticmethod
    def _map(row: tuple) -> Prediction:
        row = _utc_row(row)
        return Prediction(
            id=row[0],
            model_id=row[1],
            prediction_type=PredictionType(row[2]),
            customer_id=row[3],
            card_id=row[4] if row[4] else None,
            benefit_id=row[5] if row[5] else None,
            score=float(row[6]),
            confidence=float(row[7]) if row[7] else None,
            explanation=row[8] if row[8] else None,
            features_used=json.loads(row[9]) if row[9] else None,
            predicted_at=row[10],
            expires_at=row[11] if row[11] else None,
            created_at=row[12],
        )


def _utc_row(row):
    return tuple(
        v.replace(tzinfo=UTC) if isinstance(v, datetime) and v.tzinfo is None else v for v in row
    )

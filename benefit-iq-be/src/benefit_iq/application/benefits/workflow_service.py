"""Ownership-checked portfolio writes with serialized idempotency validation."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from benefit_iq.domain.entities.card import Card
from benefit_iq.domain.enums.benefit_enums import CardStatus


class BenefitWorkflowService:
    def __init__(self, cards, products, transactions, usages, utilization, locks):
        self.cards, self.products = cards, products
        self.transactions, self.usages = transactions, usages
        self.utilization, self.locks = utilization, locks

    async def owned_card(self, customer_id, card_id):
        card = await self.cards.get_by_id(card_id)
        if not card or card.customer_id != customer_id:
            raise LookupError("Card not found")
        return card

    async def add_card(self, customer_id, product_id, last_four, alias):
        product = await self.products.get_by_id(product_id)
        if not product or not product.is_active:
            raise LookupError("Card product not found")
        key = f"card:{customer_id}:{product_id}:{last_four}"
        async with self.locks.lock(key):
            identifier = uuid5(NAMESPACE_URL, key)
            existing = await self.cards.get_by_id(identifier)
            if existing:
                return existing
            now = datetime.now(UTC)
            return await self.cards.create(
                Card(
                    id=identifier,
                    customer_id=customer_id,
                    card_product_id=product_id,
                    card_last_four=last_four,
                    card_alias=alias,
                    status=CardStatus.ACTIVE,
                    issued_at=now,
                    expiry_date=now.replace(year=now.year + 4),
                    activated_at=now,
                    cancelled_at=None,
                    is_primary=False,
                    created_at=now,
                    updated_at=now,
                )
            )

    async def ingest(self, transaction):
        card = await self.owned_card(transaction.customer_id, transaction.card_id)
        if transaction.status.value != "posted":
            raise ValueError(
                "Ingest posted transactions; use the reversal endpoint for corrections"
            )
        if not card.issued_at <= transaction.transaction_date < card.expiry_date:
            raise ValueError("Transaction timestamp must be within the card lifetime")
        key = f"tx:{transaction.customer_id}:{transaction.card_id}:{transaction.external_transaction_id}"
        transaction.id = uuid5(NAMESPACE_URL, key)
        transaction.idempotency_key = key
        async with self.locks.lock(key):
            existing = await self.transactions.get_by_id(transaction.id)
            if existing:
                fields = (
                    "amount",
                    "currency",
                    "card_id",
                    "merchant_name",
                    "merchant_category_code",
                    "transaction_date",
                )
                if any(getattr(existing, f) != getattr(transaction, f) for f in fields):
                    raise ValueError("Idempotency key was already used for a different transaction")
                return existing
            return await self.transactions.create(transaction)

    async def reverse(self, customer_id, transaction_id):
        from benefit_iq.domain.enums.benefit_enums import TransactionStatus

        key = f"reversal:{customer_id}:{transaction_id}"
        async with self.locks.lock(key):
            tx = await self.transactions.get_by_id(transaction_id)
            if not tx or tx.customer_id != customer_id:
                raise LookupError("Transaction not found")
            tx.status = TransactionStatus.REVERSED
            tx.updated_at = datetime.now(UTC)
            return await self.transactions.create(tx)

    async def redeem(self, usage, external_id):
        await self.owned_card(usage.customer_id, usage.card_id)
        key = f"usage:{usage.customer_id}:{usage.card_id}:{usage.benefit_id}:{external_id}"
        usage.id = uuid5(NAMESPACE_URL, key)
        async with self.locks.lock(
            f"benefit:{usage.customer_id}:{usage.card_id}:{usage.benefit_id}"
        ):
            existing = await self.usages.get_usage_for_customer_benefit(
                usage.customer_id,
                usage.benefit_id,
                datetime(1970, 1, 1, tzinfo=UTC),
                datetime(2100, 1, 1, tzinfo=UTC),
            )
            prior = next((u for u in existing if u.id == usage.id), None)
            if prior:
                if prior.value_used != usage.value_used or prior.currency != usage.currency:
                    raise ValueError("Idempotency key was already used for different usage")
                return prior
            summary = await self.utilization.calculate_customer_utilization(
                usage.customer_id, currency=usage.currency
            )
            benefit = next(
                (
                    u
                    for u in summary.utilizations
                    if u.card_id == usage.card_id and u.benefit_id == usage.benefit_id
                ),
                None,
            )
            if not benefit or benefit.status.value in ("not_eligible", "fully_used", "expired"):
                raise ValueError("Benefit is not available for redemption")
            if benefit.value_type == "monetary":
                if usage.value_used <= 0 or usage.value_used > benefit.remaining_value:
                    raise ValueError("Redemption exceeds the remaining cash allowance")
            elif usage.value_used != Decimal("0"):
                raise ValueError("Non-monetary benefits record a visit/use with zero cash value")
            return await self.usages.create(usage)

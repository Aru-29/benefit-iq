"""Transaction domain entity.

Represents a financial transaction made by a customer using a card.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from benefit_iq.domain.enums.benefit_enums import TransactionChannel, TransactionStatus


@dataclass
class Transaction:
    """A financial transaction record with full audit and benefit context."""

    id: UUID
    external_transaction_id: str
    customer_id: UUID
    card_id: UUID
    merchant_id: UUID | None
    merchant_name: str | None
    merchant_category_code: str | None
    amount: Decimal
    currency: str
    transaction_date: datetime
    posted_date: datetime | None
    status: TransactionStatus
    channel: TransactionChannel
    description: str | None
    country: str | None
    city: str | None
    is_recurring: bool
    source_system: str
    idempotency_key: str
    created_at: datetime
    updated_at: datetime

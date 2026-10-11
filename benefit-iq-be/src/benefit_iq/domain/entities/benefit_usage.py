"""Benefit Usage domain entity.

Records individual instances of a customer using a benefit.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass
class BenefitUsage:
    """A record of a customer utilizing a specific benefit."""

    id: UUID
    customer_id: UUID
    card_id: UUID
    benefit_id: UUID
    transaction_id: UUID | None
    usage_date: datetime
    value_used: Decimal
    currency: str
    description: str | None
    source_system: str
    created_at: datetime

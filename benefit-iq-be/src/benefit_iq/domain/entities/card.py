"""Card domain entity.

Represents a specific card issued to a customer, linked to a card product.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from benefit_iq.domain.enums.benefit_enums import CardStatus


@dataclass
class Card:
    """A specific card issued to a customer."""

    id: UUID
    customer_id: UUID
    card_product_id: UUID
    card_last_four: str
    card_alias: str | None
    status: CardStatus
    issued_at: datetime
    expiry_date: datetime
    activated_at: datetime | None
    cancelled_at: datetime | None
    is_primary: bool
    created_at: datetime
    updated_at: datetime

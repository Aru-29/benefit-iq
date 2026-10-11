"""Card Product domain entity.

Represents a card product offered by an issuer (e.g., Amex Platinum, Visa Gold).
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from benefit_iq.domain.enums.benefit_enums import CardNetwork, CardTier


@dataclass
class CardProduct:
    """A card product definition from an issuer."""

    id: UUID
    name: str
    issuer_name: str
    network: CardNetwork
    tier: CardTier
    annual_fee: Decimal
    currency: str
    description: str | None
    is_active: bool
    effective_from: datetime
    effective_to: datetime | None
    created_at: datetime
    updated_at: datetime

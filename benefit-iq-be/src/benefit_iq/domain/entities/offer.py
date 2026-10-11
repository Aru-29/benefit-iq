"""Offer domain entity.

Represents a merchant offer or promotional deal available to cardholders.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from benefit_iq.domain.enums.benefit_enums import BenefitValueType


@dataclass
class Offer:
    """A merchant or issuer promotional offer."""

    id: UUID
    name: str
    description: str | None
    merchant_id: UUID | None
    card_product_id: UUID | None
    benefit_id: UUID | None
    value_type: BenefitValueType
    value_amount: Decimal
    currency: str
    min_transaction_amount: Decimal | None
    max_redemptions: int | None
    current_redemptions: int
    coupon_code: str | None
    effective_from: datetime
    effective_to: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

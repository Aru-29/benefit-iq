"""Benefit domain entity.

Represents a benefit definition that can be attached to one or more card products.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from benefit_iq.domain.enums.benefit_enums import (
    BenefitCategory,
    BenefitFrequency,
    BenefitValueType,
)


@dataclass
class Benefit:
    """A benefit that a card product can provide to customers."""

    id: UUID
    name: str
    description: str | None
    category: BenefitCategory
    value_type: BenefitValueType
    max_value: Decimal
    currency: str
    frequency: BenefitFrequency
    requires_activation: bool
    activation_instructions: str | None
    terms_and_conditions: str | None
    is_active: bool
    effective_from: datetime
    effective_to: datetime | None
    created_at: datetime
    updated_at: datetime

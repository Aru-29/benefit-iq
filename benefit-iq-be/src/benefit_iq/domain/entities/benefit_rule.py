"""Benefit Rule domain entity.

Represents a configurable rule that determines when and how a benefit
is entitled to a customer. Rules are data-driven, versioned, and
support priority-based evaluation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from benefit_iq.domain.enums.benefit_enums import RuleConditionType, RuleOperator


@dataclass
class RuleCondition:
    """A single condition within a benefit rule."""

    condition_type: RuleConditionType
    operator: RuleOperator
    value: str
    value_to: str | None = None


@dataclass
class BenefitRule:
    """A versioned, data-driven rule governing benefit entitlement.

    Rules are evaluated in priority order. Conditions are combined with AND logic
    within a single rule. Multiple rules for the same benefit are evaluated independently.
    """

    id: UUID
    benefit_id: UUID
    card_product_id: UUID | None
    name: str
    description: str | None
    version: int
    priority: int
    conditions: list[RuleCondition] = field(default_factory=list)
    min_spend_amount: Decimal | None = None
    max_spend_amount: Decimal | None = None
    spend_currency: str | None = None
    spend_period_days: int | None = None
    usage_limit: int | None = None
    monthly_limit: int | None = None
    quarterly_limit: int | None = None
    annual_limit: int | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

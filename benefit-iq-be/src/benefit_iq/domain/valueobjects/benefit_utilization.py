"""Benefit Utilization value object.

Represents the calculated utilization analysis for a specific customer-card-benefit
combination over a defined period. This is the core business output.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from benefit_iq.domain.enums.benefit_enums import UtilizationStatus


@dataclass(frozen=True)
class BenefitUtilization:
    """Immutable value object representing benefit utilization analysis result.

    Uses Decimal for monetary precision. All values in the specified currency.
    """

    customer_id: UUID
    card_id: UUID
    benefit_id: UUID
    benefit_name: str
    benefit_category: str
    period_start: datetime
    period_end: datetime
    entitled_value: Decimal
    used_value: Decimal
    remaining_value: Decimal
    utilization_percentage: Decimal
    currency: str
    status: UtilizationStatus
    usage_count: int
    usage_limit: int | None
    eligibility_reason: str
    expiry_date: datetime | None
    days_until_expiry: int | None
    at_risk_of_expiry: bool

    rule_id: UUID | None = None
    rule_version: int = 0
    calculated_at: datetime | None = None
    value_type: str = "monetary"

    @property
    def unused_value(self) -> Decimal:
        """Calculate the unrealized/lost value."""
        return max(Decimal("0"), self.entitled_value - self.used_value)

    @property
    def is_fully_utilized(self) -> bool:
        """Check if benefit is fully utilized."""
        return self.status == UtilizationStatus.FULLY_USED

    @property
    def is_unused(self) -> bool:
        """Check if benefit is completely unused."""
        return self.status == UtilizationStatus.UNUSED


@dataclass(frozen=True)
class CustomerBenefitSummary:
    """Aggregated benefit utilization summary for a customer."""

    customer_id: UUID
    period_start: datetime
    period_end: datetime
    total_entitled_value: Decimal
    total_used_value: Decimal
    total_unused_value: Decimal
    overall_utilization_percentage: Decimal
    currency: str
    total_benefits: int
    utilized_benefits: int
    partially_utilized_benefits: int
    unused_benefits: int
    expired_benefits: int
    at_risk_benefits: int
    utilizations: list[BenefitUtilization]

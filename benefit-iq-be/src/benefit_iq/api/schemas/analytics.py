"""Analytics and Benefit Utilization API Pydantic schemas.

Strongly-typed contracts for underutilization analytics, predictions,
nudge lifecycle management, and simulation endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class BenefitUtilizationItemResponse(BaseModel):
    """Single benefit utilization detail."""

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
    status: str
    usage_count: int
    usage_limit: int | None = None
    eligibility_reason: str | None = None
    expiry_date: datetime | None = None
    days_until_expiry: int = 0
    at_risk_of_expiry: bool = False


class CustomerUtilizationSummaryResponse(BaseModel):
    """Aggregate utilization summary for a customer."""

    customer_id: UUID
    total_benefits: int
    entitled_benefits: int
    total_entitled_value: Decimal
    total_used_value: Decimal
    total_remaining_value: Decimal
    overall_utilization_pct: Decimal
    at_risk_count: int
    at_risk_value: Decimal
    currency: str
    utilizations: list[BenefitUtilizationItemResponse]


class PredictionItemResponse(BaseModel):
    """Prediction or recommendation response item."""

    id: UUID
    prediction_type: str
    customer_id: UUID
    card_id: UUID | None = None
    benefit_id: UUID | None = None
    score: float
    confidence: float | None = None
    explanation: str | None = None
    features_used: dict[str, Any] | None = None
    predicted_at: datetime
    expires_at: datetime | None = None


class NudgeResponse(BaseModel):
    """Nudge notification response item."""

    id: UUID
    customer_id: UUID
    card_id: UUID | None = None
    benefit_id: UUID | None = None
    offer_id: UUID | None = None
    nudge_type: str
    channel: str
    status: str
    title: str
    message: str
    unused_value: Decimal | None = None
    currency: str | None = None
    reason: str
    ml_score: float | None = None
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    opened_at: datetime | None = None
    converted_at: datetime | None = None
    expires_at: datetime | None = None
    cooldown_until: datetime | None = None
    created_at: datetime


class UpdateNudgeStatusRequest(BaseModel):
    """Request payload to transition nudge lifecycle state."""

    status: str = Field(
        ..., description="Target status: SENT, DELIVERED, OPENED, CONVERTED, DISMISSED"
    )


class SimulateUsageRequest(BaseModel):
    """Request payload to simulate a benefit redemption."""

    customer_id: UUID
    card_id: UUID
    benefit_id: UUID
    used_value: Decimal = Field(..., gt=0)
    currency: str = "USD"
    notes: str | None = "Manual simulation"


class SimulateTransactionRequest(BaseModel):
    """Request payload to simulate a customer card transaction."""

    customer_id: UUID
    card_id: UUID
    amount: Decimal = Field(..., gt=0)
    currency: str = "USD"
    merchant_name: str
    merchant_category_code: str
    category_name: str
    city: str = "New York"
    country: str = "US"


class SalvageMetricsResponse(BaseModel):
    """Response payload for nudge value salvage metrics."""

    converted_nudge_count: int
    total_salvaged_value: str
    currency: str

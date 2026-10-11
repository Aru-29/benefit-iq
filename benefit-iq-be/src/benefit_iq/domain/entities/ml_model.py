"""ML Model and Prediction domain entities.

Represents ML model metadata, versions, and prediction results.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from benefit_iq.domain.enums.benefit_enums import ModelStatus, PredictionType


@dataclass
class MLModel:
    """ML model version metadata."""

    id: UUID
    name: str
    prediction_type: PredictionType
    version: str
    algorithm: str
    status: ModelStatus
    metrics: dict | None
    feature_names: list[str] | None
    training_data_start: datetime | None
    training_data_end: datetime | None
    training_samples: int | None
    model_path: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class Prediction:
    """An ML prediction result for a customer/benefit combination."""

    id: UUID
    model_id: UUID
    prediction_type: PredictionType
    customer_id: UUID
    card_id: UUID | None
    benefit_id: UUID | None
    score: float
    confidence: float | None
    explanation: str | None
    features_used: dict | None
    predicted_at: datetime
    expires_at: datetime | None
    created_at: datetime

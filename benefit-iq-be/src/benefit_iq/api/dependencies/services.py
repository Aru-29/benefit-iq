"""Dependency Injection service providers for API endpoints."""

from typing import Any

from dependency_injector.wiring import Provide, inject

from benefit_iq.application.benefits.ml_prediction_service import MLPredictionService
from benefit_iq.application.benefits.nudge_service import NudgeService
from benefit_iq.application.benefits.portfolio_service import PortfolioAnalyticsService
from benefit_iq.application.benefits.utilization_service import BenefitUtilizationService
from benefit_iq.application.contracts.repositories.benefit_repositories import (
    BenefitRepository,
    BenefitUsageRepository,
    CardProductRepository,
    CardRepository,
    NudgeRepository,
    TransactionRepository,
)
from benefit_iq.infrastructure.persistence.clickhouse.database import ClickHouseDatabase


@inject
def get_clickhouse_database(
    database: Any = Provide["clickhouse"],
) -> ClickHouseDatabase:
    """Dependency provider for ClickHouseDatabase."""
    return database


@inject
def get_utilization_service(
    service: BenefitUtilizationService = Provide["utilization_service"],
) -> BenefitUtilizationService:
    """Dependency provider for BenefitUtilizationService."""
    return service


@inject
def get_ml_prediction_service(
    service: MLPredictionService = Provide["ml_prediction_service"],
) -> MLPredictionService:
    """Dependency provider for MLPredictionService."""
    return service


@inject
def get_nudge_service(
    service: NudgeService = Provide["nudge_service"],
) -> NudgeService:
    """Dependency provider for NudgeService."""
    return service


@inject
def get_portfolio_analytics_service(
    service: PortfolioAnalyticsService = Provide["portfolio_analytics_service"],
) -> PortfolioAnalyticsService:
    """Dependency provider for PortfolioAnalyticsService."""
    return service


@inject
def get_card_repository(
    repo: CardRepository = Provide["card_repository"],
) -> CardRepository:
    """Dependency provider for CardRepository."""
    return repo


@inject
def get_card_product_repository(
    repo: CardProductRepository = Provide["card_product_repository"],
) -> CardProductRepository:
    """Dependency provider for CardProductRepository."""
    return repo


@inject
def get_benefit_repository(
    repo: BenefitRepository = Provide["benefit_repository"],
) -> BenefitRepository:
    """Dependency provider for BenefitRepository."""
    return repo


@inject
def get_transaction_repository(
    repo: TransactionRepository = Provide["transaction_repository"],
) -> TransactionRepository:
    """Dependency provider for TransactionRepository."""
    return repo


@inject
def get_benefit_usage_repository(
    repo: BenefitUsageRepository = Provide["benefit_usage_repository"],
) -> BenefitUsageRepository:
    """Dependency provider for BenefitUsageRepository."""
    return repo


@inject
def get_nudge_repository(
    repo: NudgeRepository = Provide["nudge_repository"],
) -> NudgeRepository:
    """Dependency provider for NudgeRepository."""
    return repo

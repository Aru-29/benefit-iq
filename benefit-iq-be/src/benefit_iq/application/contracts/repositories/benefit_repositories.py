"""Repository contracts for BenefitIQ business entities."""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from benefit_iq.domain.entities.benefit import Benefit
from benefit_iq.domain.entities.benefit_rule import BenefitRule
from benefit_iq.domain.entities.benefit_usage import BenefitUsage
from benefit_iq.domain.entities.card import Card
from benefit_iq.domain.entities.card_product import CardProduct
from benefit_iq.domain.entities.card_product_benefit import CardProductBenefit
from benefit_iq.domain.entities.merchant import Merchant
from benefit_iq.domain.entities.ml_model import MLModel, Prediction
from benefit_iq.domain.entities.nudge import Nudge
from benefit_iq.domain.entities.offer import Offer
from benefit_iq.domain.entities.transaction import Transaction


class CardProductRepository(ABC):
    """Contract for card product persistence."""

    @abstractmethod
    async def create(self, product: CardProduct) -> CardProduct: ...

    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> CardProduct | None: ...

    @abstractmethod
    async def list_all(self, offset: int, limit: int) -> list[CardProduct]: ...

    @abstractmethod
    async def update(self, product: CardProduct) -> CardProduct: ...


class CardRepository(ABC):
    """Contract for card persistence."""

    @abstractmethod
    async def create(self, card: Card) -> Card: ...

    @abstractmethod
    async def get_by_id(self, card_id: UUID) -> Card | None: ...

    @abstractmethod
    async def get_by_customer(self, customer_id: UUID) -> list[Card]: ...

    @abstractmethod
    async def update(self, card: Card) -> Card: ...

    @abstractmethod
    async def list_all(self, offset: int, limit: int) -> list[Card]: ...


class BenefitRepository(ABC):
    """Contract for benefit persistence."""

    @abstractmethod
    async def create(self, benefit: Benefit) -> Benefit: ...

    @abstractmethod
    async def get_by_id(self, benefit_id: UUID) -> Benefit | None: ...

    @abstractmethod
    async def get_by_card_product(self, card_product_id: UUID) -> list[Benefit]: ...

    @abstractmethod
    async def list_all(self, offset: int, limit: int) -> list[Benefit]: ...

    @abstractmethod
    async def update(self, benefit: Benefit) -> Benefit: ...


class BenefitRuleRepository(ABC):
    """Contract for benefit rule persistence."""

    @abstractmethod
    async def create(self, rule: BenefitRule) -> BenefitRule: ...

    @abstractmethod
    async def get_by_id(self, rule_id: UUID) -> BenefitRule | None: ...

    @abstractmethod
    async def get_by_benefit(self, benefit_id: UUID) -> list[BenefitRule]: ...

    @abstractmethod
    async def get_active_rules(
        self, benefit_id: UUID, card_product_id: UUID | None = None
    ) -> list[BenefitRule]: ...

    @abstractmethod
    async def update(self, rule: BenefitRule) -> BenefitRule: ...

    @abstractmethod
    async def list_all(self, offset: int, limit: int) -> list[BenefitRule]: ...


class CardProductBenefitRepository(ABC):
    """Contract for card product-benefit mapping persistence."""

    @abstractmethod
    async def create(self, mapping: CardProductBenefit) -> CardProductBenefit: ...

    @abstractmethod
    async def get_benefits_for_product(self, card_product_id: UUID) -> list[CardProductBenefit]: ...

    @abstractmethod
    async def delete(self, mapping_id: UUID) -> bool: ...


class MerchantRepository(ABC):
    """Contract for merchant persistence."""

    @abstractmethod
    async def create(self, merchant: Merchant) -> Merchant: ...

    @abstractmethod
    async def get_by_id(self, merchant_id: UUID) -> Merchant | None: ...

    @abstractmethod
    async def get_by_mcc(self, mcc: str) -> list[Merchant]: ...

    @abstractmethod
    async def list_all(self, offset: int, limit: int) -> list[Merchant]: ...

    @abstractmethod
    async def update(self, merchant: Merchant) -> Merchant: ...


class TransactionRepository(ABC):
    """Contract for transaction persistence."""

    @abstractmethod
    async def create(self, transaction: Transaction) -> Transaction: ...

    @abstractmethod
    async def create_batch(self, transactions: list[Transaction]) -> int: ...

    @abstractmethod
    async def get_by_id(self, transaction_id: UUID) -> Transaction | None: ...

    @abstractmethod
    async def get_by_idempotency_key(self, key: str) -> Transaction | None: ...

    @abstractmethod
    async def get_by_customer(
        self,
        customer_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Transaction]: ...

    @abstractmethod
    async def get_customer_spend(
        self,
        customer_id: UUID,
        card_id: UUID | None,
        start_date: datetime,
        end_date: datetime,
        merchant_category_code: str | None = None,
        currency: str = "USD",
    ) -> Decimal: ...

    @abstractmethod
    async def list_all(self, offset: int, limit: int) -> list[Transaction]: ...


class BenefitUsageRepository(ABC):
    """Contract for benefit usage persistence."""

    @abstractmethod
    async def create(self, usage: BenefitUsage) -> BenefitUsage: ...

    @abstractmethod
    async def get_usage_for_customer_benefit(
        self,
        customer_id: UUID,
        benefit_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[BenefitUsage]: ...

    @abstractmethod
    async def get_usage_summary(
        self,
        customer_id: UUID,
        benefit_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> tuple[int, Decimal]: ...

    @abstractmethod
    async def list_all(self, offset: int, limit: int) -> list[BenefitUsage]: ...


class OfferRepository(ABC):
    """Contract for offer persistence."""

    @abstractmethod
    async def create(self, offer: Offer) -> Offer: ...

    @abstractmethod
    async def get_by_id(self, offer_id: UUID) -> Offer | None: ...

    @abstractmethod
    async def get_active_offers(
        self,
        card_product_id: UUID | None = None,
        merchant_id: UUID | None = None,
    ) -> list[Offer]: ...

    @abstractmethod
    async def update(self, offer: Offer) -> Offer: ...

    @abstractmethod
    async def list_all(self, offset: int, limit: int) -> list[Offer]: ...


class NudgeRepository(ABC):
    """Contract for nudge persistence."""

    @abstractmethod
    async def create(self, nudge: Nudge) -> Nudge: ...

    @abstractmethod
    async def get_by_id(self, nudge_id: UUID) -> Nudge | None: ...

    @abstractmethod
    async def get_by_customer(
        self,
        customer_id: UUID,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Nudge]: ...

    @abstractmethod
    async def get_recent_nudges(
        self,
        customer_id: UUID,
        benefit_id: UUID | None,
        since: datetime,
    ) -> list[Nudge]: ...

    @abstractmethod
    async def update(self, nudge: Nudge) -> Nudge: ...

    @abstractmethod
    async def list_all(self, offset: int, limit: int) -> list[Nudge]: ...


class MLModelRepository(ABC):
    """Contract for ML model metadata persistence."""

    @abstractmethod
    async def create(self, model: MLModel) -> MLModel: ...

    @abstractmethod
    async def get_by_id(self, model_id: UUID) -> MLModel | None: ...

    @abstractmethod
    async def get_deployed_model(self, prediction_type: str) -> MLModel | None: ...

    @abstractmethod
    async def update(self, model: MLModel) -> MLModel: ...

    @abstractmethod
    async def list_all(self, offset: int, limit: int) -> list[MLModel]: ...


class PredictionRepository(ABC):
    """Contract for ML prediction persistence."""

    @abstractmethod
    async def create(self, prediction: Prediction) -> Prediction: ...

    @abstractmethod
    async def create_batch(self, predictions: list[Prediction]) -> int: ...

    @abstractmethod
    async def get_by_customer(
        self,
        customer_id: UUID,
        prediction_type: str | None = None,
    ) -> list[Prediction]: ...

    @abstractmethod
    async def get_latest(
        self,
        customer_id: UUID,
        prediction_type: str,
        benefit_id: UUID | None = None,
    ) -> Prediction | None: ...

    @abstractmethod
    async def list_all(self, offset: int, limit: int) -> list[Prediction]: ...


class EnrollmentRepository(ABC):
    @abstractmethod
    async def is_enrolled(
        self, customer_id: UUID, card_id: UUID, benefit_id: UUID, as_of: datetime
    ) -> bool: ...

    @abstractmethod
    async def enroll(
        self, customer_id: UUID, card_id: UUID, benefit_id: UUID, at: datetime
    ) -> None: ...

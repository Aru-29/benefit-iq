"""Business domain exceptions for BenefitIQ analytics entities."""


class BenefitDomainException(Exception):
    """Base exception for benefit domain errors."""


class BenefitNotFoundException(BenefitDomainException):
    """Raised when a benefit cannot be found."""


class BenefitRuleNotFoundException(BenefitDomainException):
    """Raised when a benefit rule cannot be found."""


class InvalidBenefitRuleException(BenefitDomainException):
    """Raised when a benefit rule definition is invalid."""


class CardNotFoundException(BenefitDomainException):
    """Raised when a card cannot be found."""


class CardProductNotFoundException(BenefitDomainException):
    """Raised when a card product cannot be found."""


class InvalidCardOwnershipException(BenefitDomainException):
    """Raised when card ownership validation fails."""


class TransactionDomainException(Exception):
    """Base exception for transaction domain errors."""


class DuplicateTransactionException(TransactionDomainException):
    """Raised when a duplicate transaction is detected via idempotency key."""


class TransactionNotFoundException(TransactionDomainException):
    """Raised when a transaction cannot be found."""


class MerchantNotFoundException(BenefitDomainException):
    """Raised when a merchant cannot be found."""


class OfferNotFoundException(BenefitDomainException):
    """Raised when an offer cannot be found."""


class OfferExpiredException(BenefitDomainException):
    """Raised when an offer has expired."""


class NudgeDomainException(Exception):
    """Base exception for nudge domain errors."""


class NudgeNotFoundException(NudgeDomainException):
    """Raised when a nudge cannot be found."""


class NudgeCooldownActiveException(NudgeDomainException):
    """Raised when attempting to send a nudge during cooldown."""


class MLDomainException(Exception):
    """Base exception for ML domain errors."""


class ModelNotFoundException(MLDomainException):
    """Raised when an ML model cannot be found."""


class ModelTrainingException(MLDomainException):
    """Raised when ML model training fails."""


class InsufficientTrainingDataException(MLDomainException):
    """Raised when there is not enough data to train a model."""

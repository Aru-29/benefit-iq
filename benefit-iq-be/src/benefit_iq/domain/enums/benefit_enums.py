"""Business domain enumerations for BenefitIQ benefit analytics."""

from enum import Enum


class CardNetwork(str, Enum):
    """Card payment network."""

    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"
    DINERS = "diners"
    JCB = "jcb"
    UNIONPAY = "unionpay"
    OTHER = "other"


class CardTier(str, Enum):
    """Card product tier classification."""

    BASIC = "basic"
    CLASSIC = "classic"
    GOLD = "gold"
    PLATINUM = "platinum"
    SIGNATURE = "signature"
    INFINITE = "infinite"
    CENTURION = "centurion"
    BUSINESS = "business"
    CORPORATE = "corporate"
    OTHER = "other"


class CardStatus(str, Enum):
    """Card lifecycle status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class BenefitCategory(str, Enum):
    """Benefit classification category."""

    CASHBACK = "cashback"
    REWARD_POINTS = "reward_points"
    LOUNGE_ACCESS = "lounge_access"
    TRAVEL_CREDIT = "travel_credit"
    DINING_CREDIT = "dining_credit"
    STREAMING_CREDIT = "streaming_credit"
    INSURANCE = "insurance"
    PURCHASE_PROTECTION = "purchase_protection"
    EXTENDED_WARRANTY = "extended_warranty"
    CONCIERGE = "concierge"
    MERCHANT_OFFER = "merchant_offer"
    FEE_WAIVER = "fee_waiver"
    STATEMENT_CREDIT = "statement_credit"
    OTHER = "other"


class BenefitValueType(str, Enum):
    """How benefit value is quantified."""

    MONETARY = "monetary"
    PERCENTAGE = "percentage"
    COUNT = "count"
    UNLIMITED = "unlimited"


class BenefitFrequency(str, Enum):
    """Benefit entitlement frequency period."""

    ONE_TIME = "one_time"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    PER_TRANSACTION = "per_transaction"
    UNLIMITED = "unlimited"


class RuleOperator(str, Enum):
    """Operators for benefit rule conditions."""

    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    CONTAINS = "contains"
    EXISTS = "exists"


class RuleConditionType(str, Enum):
    """Type of condition in a benefit rule."""

    CARD_TIER = "card_tier"
    CARD_NETWORK = "card_network"
    CARD_PRODUCT = "card_product"
    MIN_SPEND = "min_spend"
    MAX_SPEND = "max_spend"
    TRANSACTION_CATEGORY = "transaction_category"
    MERCHANT = "merchant"
    MERCHANT_CATEGORY = "merchant_category"
    GEOGRAPHY = "geography"
    CURRENCY = "currency"
    TIME_PERIOD = "time_period"
    CUSTOMER_TENURE = "customer_tenure"
    ACTIVATION_REQUIRED = "activation_required"
    ACCUMULATED_SPEND = "accumulated_spend"


class TransactionStatus(str, Enum):
    """Transaction processing status."""

    PENDING = "pending"
    POSTED = "posted"
    REVERSED = "reversed"
    DECLINED = "declined"
    REFUNDED = "refunded"


class TransactionChannel(str, Enum):
    """Transaction origin channel."""

    POS = "pos"
    ONLINE = "online"
    ATM = "atm"
    MOBILE = "mobile"
    CONTACTLESS = "contactless"
    RECURRING = "recurring"
    OTHER = "other"


class NudgeStatus(str, Enum):
    """Nudge lifecycle status."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    CONVERTED = "converted"
    DISMISSED = "dismissed"
    EXPIRED = "expired"
    FAILED = "failed"


class NudgeChannel(str, Enum):
    """Communication channel for nudges."""

    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NudgeType(str, Enum):
    """Nudge purpose classification."""

    BENEFIT_REMINDER = "benefit_reminder"
    EXPIRY_WARNING = "expiry_warning"
    UTILIZATION_PROMPT = "utilization_prompt"
    OFFER_RECOMMENDATION = "offer_recommendation"
    SPENDING_INSIGHT = "spending_insight"
    MILESTONE_ALERT = "milestone_alert"


class UtilizationStatus(str, Enum):
    """Benefit utilization status."""

    UNUSED = "unused"
    PARTIALLY_USED = "partially_used"
    FULLY_USED = "fully_used"
    EXPIRED = "expired"
    NOT_ELIGIBLE = "not_eligible"


class ModelStatus(str, Enum):
    """ML model lifecycle status."""

    TRAINING = "training"
    TRAINED = "trained"
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class PredictionType(str, Enum):
    """Type of ML prediction."""

    BENEFIT_ENGAGEMENT = "benefit_engagement"
    NUDGE_RESPONSE = "nudge_response"
    BENEFIT_UTILIZATION = "benefit_utilization"
    OPPORTUNITY_PRIORITY = "opportunity_priority"

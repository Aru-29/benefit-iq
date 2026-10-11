"""ClickHouse schema initialization and runtime verification.

Creates all required tables for BenefitIQ business domain on startup
and seeds essential reference data. Uses ReplacingMergeTree for entities
that support upsert semantics, and MergeTree for append-only fact tables.
"""

from uuid import uuid4

import structlog

from benefit_iq.infrastructure.persistence.clickhouse.database import ClickHouseDatabase

logger = structlog.get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# Schema version tracking table
# ─────────────────────────────────────────────────────────────────────────
_MIGRATION_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.schema_migrations (
    version UInt32,
    name String,
    applied_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(applied_at)
ORDER BY (version);
"""

# ─────────────────────────────────────────────────────────────────────────
# Core identity tables (existing)
# ─────────────────────────────────────────────────────────────────────────
_ROLES_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.roles (
    id UUID,
    name String,
    description Nullable(String),
    is_active UInt8 DEFAULT 1,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (name, id);
"""

_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.users (
    id UUID,
    username String,
    first_name String,
    middle_name Nullable(String),
    last_name String,
    email String,
    password_hash String,
    role_id UUID,
    authentication_provider String DEFAULT 'local',
    external_provider_id Nullable(String),
    is_active UInt8 DEFAULT 1,
    is_email_verified UInt8 DEFAULT 0,
    preferred_settings Nullable(String),
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now(),
    last_login_at Nullable(DateTime)
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (email, id);
"""

_APP_CONFIG_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.app_config (
    id UUID,
    application String,
    environment String,
    config_key String,
    config_value Nullable(String),
    is_secret UInt8 DEFAULT 0,
    secret_path Nullable(String),
    secret_key Nullable(String),
    description Nullable(String),
    is_active UInt8 DEFAULT 1,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (application, environment, config_key, id);
"""

# ─────────────────────────────────────────────────────────────────────────
# Card & product tables
# ─────────────────────────────────────────────────────────────────────────
_CARD_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.card_products (
    id UUID,
    name String,
    issuer_name String,
    network String,
    tier String,
    annual_fee Decimal(18, 4),
    currency String DEFAULT 'USD',
    description Nullable(String),
    is_active UInt8 DEFAULT 1,
    effective_from DateTime DEFAULT now(),
    effective_to Nullable(DateTime),
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (issuer_name, name, id);
"""

_CARDS_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.cards (
    id UUID,
    customer_id UUID,
    card_product_id UUID,
    card_last_four String,
    card_alias Nullable(String),
    status String DEFAULT 'active',
    issued_at DateTime DEFAULT now(),
    expiry_date DateTime,
    activated_at Nullable(DateTime),
    cancelled_at Nullable(DateTime),
    is_primary UInt8 DEFAULT 0,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (customer_id, id);
"""

# ─────────────────────────────────────────────────────────────────────────
# Benefit tables
# ─────────────────────────────────────────────────────────────────────────
_BENEFITS_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.benefits (
    id UUID,
    name String,
    description Nullable(String),
    category String,
    value_type String,
    max_value Decimal(18, 4),
    currency String DEFAULT 'USD',
    frequency String DEFAULT 'annual',
    requires_activation UInt8 DEFAULT 0,
    activation_instructions Nullable(String),
    terms_and_conditions Nullable(String),
    is_active UInt8 DEFAULT 1,
    effective_from DateTime DEFAULT now(),
    effective_to Nullable(DateTime),
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (category, name, id);
"""

_CARD_PRODUCT_BENEFITS_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.card_product_benefits (
    id UUID,
    card_product_id UUID,
    benefit_id UUID,
    is_active UInt8 DEFAULT 1,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (card_product_id, benefit_id, id);
"""

_BENEFIT_RULES_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.benefit_rules (
    id UUID,
    benefit_id UUID,
    card_product_id Nullable(UUID),
    name String,
    description Nullable(String),
    version UInt32 DEFAULT 1,
    priority UInt32 DEFAULT 100,
    conditions String DEFAULT '[]',
    min_spend_amount Nullable(Decimal(18, 4)),
    max_spend_amount Nullable(Decimal(18, 4)),
    spend_currency Nullable(String),
    spend_period_days Nullable(UInt32),
    usage_limit Nullable(UInt32),
    monthly_limit Nullable(UInt32),
    quarterly_limit Nullable(UInt32),
    annual_limit Nullable(UInt32),
    effective_from Nullable(DateTime),
    effective_to Nullable(DateTime),
    is_active UInt8 DEFAULT 1,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (benefit_id, priority, id);
"""

# ─────────────────────────────────────────────────────────────────────────
# Merchant & transaction tables
# ─────────────────────────────────────────────────────────────────────────
_MERCHANTS_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.merchants (
    id UUID,
    name String,
    merchant_category_code String,
    category_name String,
    country Nullable(String),
    city Nullable(String),
    is_active UInt8 DEFAULT 1,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (merchant_category_code, name, id);
"""

_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.transactions (
    id UUID,
    external_transaction_id String,
    customer_id UUID,
    card_id UUID,
    merchant_id Nullable(UUID),
    merchant_name Nullable(String),
    merchant_category_code Nullable(String),
    amount Decimal(18, 4),
    currency String DEFAULT 'USD',
    transaction_date DateTime,
    posted_date Nullable(DateTime),
    status String DEFAULT 'posted',
    channel String DEFAULT 'pos',
    description Nullable(String),
    country Nullable(String),
    city Nullable(String),
    is_recurring UInt8 DEFAULT 0,
    source_system String DEFAULT 'api',
    idempotency_key String,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(transaction_date)
ORDER BY (customer_id, transaction_date, idempotency_key, id);
"""

_BENEFIT_USAGE_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.benefit_usage (
    id UUID,
    customer_id UUID,
    card_id UUID,
    benefit_id UUID,
    transaction_id Nullable(UUID),
    usage_date DateTime,
    value_used Decimal(18, 4),
    currency String DEFAULT 'USD',
    description Nullable(String),
    source_system String DEFAULT 'api',
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(usage_date)
ORDER BY (customer_id, benefit_id, usage_date, id);
"""

# ─────────────────────────────────────────────────────────────────────────
# Offers
# ─────────────────────────────────────────────────────────────────────────
_OFFERS_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.offers (
    id UUID,
    name String,
    description Nullable(String),
    merchant_id Nullable(UUID),
    card_product_id Nullable(UUID),
    benefit_id Nullable(UUID),
    value_type String DEFAULT 'monetary',
    value_amount Decimal(18, 4),
    currency String DEFAULT 'USD',
    min_transaction_amount Nullable(Decimal(18, 4)),
    max_redemptions Nullable(UInt32),
    current_redemptions UInt32 DEFAULT 0,
    coupon_code Nullable(String),
    effective_from DateTime DEFAULT now(),
    effective_to Nullable(DateTime),
    is_active UInt8 DEFAULT 1,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (name, id);
"""

# ─────────────────────────────────────────────────────────────────────────
# Nudge tables
# ─────────────────────────────────────────────────────────────────────────
_NUDGES_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.nudges (
    id UUID,
    customer_id UUID,
    card_id Nullable(UUID),
    benefit_id Nullable(UUID),
    offer_id Nullable(UUID),
    nudge_type String,
    channel String DEFAULT 'in_app',
    status String DEFAULT 'pending',
    title String,
    message String,
    unused_value Nullable(Decimal(18, 4)),
    currency Nullable(String),
    reason String DEFAULT '',
    ml_score Nullable(Float64),
    prediction_id Nullable(UUID),
    scheduled_at Nullable(DateTime),
    sent_at Nullable(DateTime),
    delivered_at Nullable(DateTime),
    opened_at Nullable(DateTime),
    converted_at Nullable(DateTime),
    expires_at Nullable(DateTime),
    cooldown_until Nullable(DateTime),
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (customer_id, created_at, id);
"""

# ─────────────────────────────────────────────────────────────────────────
# ML tables
# ─────────────────────────────────────────────────────────────────────────
_ML_MODELS_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.ml_models (
    id UUID,
    name String,
    prediction_type String,
    version String,
    algorithm String,
    status String DEFAULT 'training',
    metrics Nullable(String),
    feature_names Nullable(String),
    training_data_start Nullable(DateTime),
    training_data_end Nullable(DateTime),
    training_samples Nullable(UInt64),
    model_path Nullable(String),
    description Nullable(String),
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (prediction_type, name, id);
"""

_PREDICTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.predictions (
    id UUID,
    model_id UUID,
    prediction_type String,
    customer_id UUID,
    card_id Nullable(UUID),
    benefit_id Nullable(UUID),
    score Float64,
    confidence Nullable(Float64),
    explanation Nullable(String),
    features_used Nullable(String),
    predicted_at DateTime DEFAULT now(),
    expires_at Nullable(DateTime),
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(predicted_at)
ORDER BY (customer_id, prediction_type, predicted_at, id);
"""

_ENROLLMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS benefitiq.benefit_enrollments (
    customer_id UUID, card_id UUID, benefit_id UUID, enrolled_at DateTime64(6, 'UTC'),
    source String DEFAULT 'self_reported'
) ENGINE = MergeTree() ORDER BY (customer_id, card_id, benefit_id, enrolled_at)
"""

ALL_TABLES = [
    _ENROLLMENTS_TABLE,
    _MIGRATION_TABLE,
    _ROLES_TABLE,
    _USERS_TABLE,
    _APP_CONFIG_TABLE,
    _CARD_PRODUCTS_TABLE,
    _CARDS_TABLE,
    _BENEFITS_TABLE,
    _CARD_PRODUCT_BENEFITS_TABLE,
    _BENEFIT_RULES_TABLE,
    _MERCHANTS_TABLE,
    _TRANSACTIONS_TABLE,
    _BENEFIT_USAGE_TABLE,
    _OFFERS_TABLE,
    _NUDGES_TABLE,
    _ML_MODELS_TABLE,
    _PREDICTIONS_TABLE,
]


class ClickHouseInitializer:
    """Verifies and creates ClickHouse core tables and minimal seed data."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        """Initialize initializer dependencies."""
        self.db = database

    async def initialize(self) -> None:
        """Creates all required tables and seeds essential data."""
        logger.info("clickhouse_initialization_started")

        for ddl in ALL_TABLES:
            await self.db.execute_async(ddl)

        await self._ensure_roles()
        # Demo fixtures are installed explicitly by scripts/seed_demo.py.

        logger.info("clickhouse_initialization_completed")

    async def _ensure_roles(self) -> None:
        """Idempotently ensures essential roles (ADMIN, CUSTOMER) exist."""
        roles = [
            ("ADMIN", "System Administrator Role"),
            ("CUSTOMER", "Standard Customer Role"),
        ]
        for role_name, description in roles:
            result = await self.db.query_async(
                "SELECT id FROM benefitiq.roles FINAL WHERE name = %(name)s",
                {"name": role_name},
            )
            if not result.result_rows:
                role_id = str(uuid4())
                role_sql = (
                    "INSERT INTO benefitiq.roles "
                    "(id, name, description, is_active, created_at, updated_at) "
                    "VALUES (%s, %s, %s, 1, now(), now())"
                )
                await self.db.execute_async(role_sql, [role_id, role_name, description])
                logger.info("seeded_essential_role", role_name=role_name)

    async def _ensure_seed_data(self) -> None:
        """Seeds sample card products and benefits for development."""
        # Check if seed data already exists
        result = await self.db.query_async("SELECT count() FROM benefitiq.card_products FINAL")
        if result.result_rows and result.result_rows[0][0] > 0:
            return

        logger.info("seeding_development_reference_data")

        # Seed card products
        products = [
            (
                str(uuid4()),
                "Platinum Card",
                "American Express",
                "amex",
                "platinum",
                "695.00",
                "USD",
                "Premium card with travel and lifestyle benefits",
            ),
            (
                str(uuid4()),
                "Gold Card",
                "American Express",
                "amex",
                "gold",
                "250.00",
                "USD",
                "Dining and travel rewards card",
            ),
            (
                str(uuid4()),
                "Green Card",
                "American Express",
                "amex",
                "classic",
                "150.00",
                "USD",
                "Everyday rewards card",
            ),
            (
                str(uuid4()),
                "Sapphire Reserve",
                "Chase",
                "visa",
                "signature",
                "550.00",
                "USD",
                "Premium travel card",
            ),
            (
                str(uuid4()),
                "Freedom Unlimited",
                "Chase",
                "visa",
                "classic",
                "0.00",
                "USD",
                "No annual fee cashback card",
            ),
        ]

        for pid, name, issuer, network, tier, fee, currency, desc in products:
            await self.db.execute_async(
                "INSERT INTO benefitiq.card_products "
                "(id, name, issuer_name, network, tier, annual_fee, currency, description) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                [pid, name, issuer, network, tier, fee, currency, desc],
            )

        # Seed benefits
        benefits = [
            (
                str(uuid4()),
                "Airline Fee Credit",
                "Annual credit for airline incidental fees",
                "travel_credit",
                "monetary",
                "200.00",
                "USD",
                "annual",
            ),
            (
                str(uuid4()),
                "Uber Credits",
                "Monthly Uber cash",
                "statement_credit",
                "monetary",
                "15.00",
                "USD",
                "monthly",
            ),
            (
                str(uuid4()),
                "Centurion Lounge Access",
                "Unlimited airport lounge visits",
                "lounge_access",
                "count",
                "0.00",
                "USD",
                "unlimited",
            ),
            (
                str(uuid4()),
                "Dining Cashback",
                "4x points at restaurants",
                "cashback",
                "percentage",
                "4.00",
                "USD",
                "per_transaction",
            ),
            (
                str(uuid4()),
                "Travel Cashback",
                "3x points on travel",
                "cashback",
                "percentage",
                "3.00",
                "USD",
                "per_transaction",
            ),
            (
                str(uuid4()),
                "Streaming Credit",
                "Monthly streaming service credit",
                "streaming_credit",
                "monetary",
                "20.00",
                "USD",
                "monthly",
            ),
            (
                str(uuid4()),
                "Purchase Protection",
                "90-day purchase protection",
                "purchase_protection",
                "monetary",
                "10000.00",
                "USD",
                "annual",
            ),
            (
                str(uuid4()),
                "Travel Insurance",
                "Complimentary travel insurance",
                "insurance",
                "monetary",
                "500000.00",
                "USD",
                "annual",
            ),
        ]

        for bid, name, desc, cat, vtype, val, currency, freq in benefits:
            await self.db.execute_async(
                "INSERT INTO benefitiq.benefits "
                "(id, name, description, category, value_type, max_value, currency, frequency) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                [bid, name, desc, cat, vtype, val, currency, freq],
            )

        # Seed merchants
        merchants = [
            (str(uuid4()), "Uber", "4121", "Transportation", "US", "San Francisco"),
            (str(uuid4()), "Netflix", "4899", "Streaming Services", "US", "Los Gatos"),
            (str(uuid4()), "Delta Airlines", "3058", "Airlines", "US", "Atlanta"),
            (str(uuid4()), "Whole Foods", "5411", "Grocery Stores", "US", "Austin"),
            (str(uuid4()), "The Cheesecake Factory", "5812", "Restaurants", "US", "Calabasas"),
        ]

        for mid, name, mcc, cat_name, country, city in merchants:
            await self.db.execute_async(
                "INSERT INTO benefitiq.merchants "
                "(id, name, merchant_category_code, category_name, country, city) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                [mid, name, mcc, cat_name, country, city],
            )

        logger.info("development_seed_data_complete")

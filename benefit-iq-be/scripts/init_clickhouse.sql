-- Benefit IQ ClickHouse Database Schema Initialization & Seed Script
-- Usage: clickhouse-client --multiquery < scripts/init_clickhouse.sql

CREATE DATABASE IF NOT EXISTS benefitiq;

-- 1. Roles Table
CREATE TABLE IF NOT EXISTS benefitiq.roles (
    id UUID,
    name String,
    description Nullable(String),
    is_active UInt8 DEFAULT 1,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (name, id);

-- 2. Users Table
CREATE TABLE IF NOT EXISTS benefitiq.users (
    id UUID,
    username String,
    email String,
    password_hash String,
    first_name String,
    last_name String,
    role_id UUID,
    is_active UInt8 DEFAULT 1,
    is_email_verified UInt8 DEFAULT 0,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now(),
    last_login_at Nullable(DateTime)
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (email, id);

-- 3. App Config Table
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

-- Seed Initial Roles
INSERT INTO benefitiq.roles (id, name, description, is_active, created_at, updated_at) VALUES
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'ADMIN', 'System Administrator with full access', 1, now(), now()),
('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'CUSTOMER', 'Standard Customer user with benefit view access', 1, now(), now());

-- Seed Initial Admin User (Password: Admin@123!)
INSERT INTO benefitiq.users (id, username, email, password_hash, first_name, last_name, role_id, is_active, is_email_verified, created_at, updated_at) VALUES
('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'admin', 'admin@benefitiq.com', '$argon2id$v=19$m=65536,t=3,p=4$42L+aW92S0yZXZ2MmtJ$mQ+Q+1v4+J5v+J5v+J5v+J5v+J5v+J5v', 'System', 'Admin', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 1, 1, now(), now());

-- Seed Default App Configuration
INSERT INTO benefitiq.app_config (id, application, environment, config_key, config_value, is_secret, secret_path, secret_key, description, is_active, created_at, updated_at) VALUES
(generateUUIDv4(), 'benefit-iq-be', 'development', 'APP_NAME', 'BenefitIQ', 0, NULL, NULL, 'Application display name', 1, now(), now()),
(generateUUIDv4(), 'benefit-iq-be', 'development', 'APP_ENV', 'development', 0, NULL, NULL, 'Current runtime environment', 1, now(), now()),
(generateUUIDv4(), 'benefit-iq-be', 'development', 'JWT_SECRET_KEY', 'change-me-in-production', 1, 'secret/data/benefit-iq-be/jwt_secret_key', 'secret_value', 'JWT signing secret key', 1, now(), now()),
(generateUUIDv4(), 'benefit-iq-be', 'development', 'SMTP_HOST', 'localhost', 0, NULL, NULL, 'SMTP mail server host', 1, now(), now()),
(generateUUIDv4(), 'benefit-iq-be', 'development', 'SMTP_PORT', '1025', 0, NULL, NULL, 'SMTP mail server port', 1, now(), now()),
(generateUUIDv4(), 'benefit-iq-be', 'development', 'SMTP_PASSWORD', 'smtp_secret_pass', 1, 'secret/data/benefit-iq-be/smtp_password', 'secret_value', 'SMTP authentication password', 1, now(), now());

 ("APP_NAME", "BenefitIQ", 0, None, None, "Application display name"),
            ("APP_ENV", "development", 0, None, None, "Current runtime environment name"),
            ("APP_VERSION", "0.1.0", 0, None, None, "Semantic version string of the platform"),
            ("DEBUG", "true", 0, None, None, "Flag enabling verbose debug logging and traceback"),
            ("API_PREFIX", "/api", 0, None, None, "Base URL path prefix for REST API endpoints"),
            ("API_VERSION", "v1", 0, None, None, "API version component"),
            ("CLICKHOUSE_HOST", "localhost", 0, None, None, "ClickHouse database server hostname"),
            ("CLICKHOUSE_PORT", "8123", 0, None, None, "ClickHouse HTTP interface port"),
            ("CLICKHOUSE_USERNAME", "default", 0, None, None, "ClickHouse database user"),
            ("CLICKHOUSE_PASSWORD", "", 0, None, None, "ClickHouse database password"),
            ("CLICKHOUSE_DATABASE", "benefitiq", 0, None, None, "ClickHouse default database schema"),
            ("CLICKHOUSE_SECURE", "false", 0, None, None, "ClickHouse TLS secure connection flag"),
            ("CLICKHOUSE_CONNECT_TIMEOUT", "10", 0, None, None, "ClickHouse connection timeout in seconds"),
            ("CLICKHOUSE_SEND_RECEIVE_TIMEOUT", "30", 0, None, None, "ClickHouse socket timeout in seconds"),
            ("REDIS_HOST", "localhost", 0, None, None, "Redis cache server hostname"),
            ("REDIS_PORT", "6380", 0, None, None, "Redis server listening port"),
            ("REDIS_PASSWORD", "", 0, None, None, "Redis server authentication password"),
            ("REDIS_DATABASE", "0", 0, None, None, "Redis database index"),
            ("REDIS_ENABLED", "true", 0, None, None, "Redis caching layer enabled flag"),
            ("OTEL_ENABLED", "true", 0, None, None, "OpenTelemetry telemetry exporter flag"),
            ("OTEL_SERVICE_NAME", "benefitiq-api", 0, None, None, "OpenTelemetry service identifier"),
            ("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317", 0, None, None, "OTLP gRPC collector endpoint"),
            (
                "JWT_SECRET_KEY",
                "change-me-in-production",
                1,
                "secret/data/benefit-iq-be/jwt_secret_key",
                "secret_value",
                "Cryptographic HMAC key used to sign JWT tokens (Stored in OpenBao)",
            ),
            ("JWT_ALGORITHM", "HS256", 0, None, None, "JWT signature algorithm (e.g. HS256)"),
            ("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15", 0, None, None, "Access token lifetime in minutes"),
            ("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7", 0, None, None, "Refresh token lifetime in days"),
            ("OAUTH_GOOGLE_CLIENT_ID", "", 0, None, None, "Google OAuth2 application client ID"),
            (
                "OAUTH_GOOGLE_CLIENT_SECRET",
                "",
                1,
                "secret/data/benefit-iq-be/google_client_secret",
                "secret_value",
                "Google OAuth2 application client secret (Stored in OpenBao)",
            ),
            ("OAUTH_MICROSOFT_CLIENT_ID", "", 0, None, None, "Microsoft OAuth2 application client ID"),
            (
                "OAUTH_MICROSOFT_CLIENT_SECRET",
                "",
                1,
                "secret/data/benefit-iq-be/microsoft_client_secret",
                "secret_value",
                "Microsoft OAuth2 application client secret (Stored in OpenBao)",
            ),
            ("OAUTH_REDIRECT_BASE_URL", "http://localhost:8080", 0, None, None, "OAuth2 redirect base URL"),
            ("SMTP_ENABLED", "true", 0, None, None, "Email notifications enabled flag"),
            ("SMTP_HOST", "localhost", 0, None, None, "SMTP mail server hostname"),
            ("SMTP_PORT", "1025", 0, None, None, "SMTP mail server port"),
            ("SMTP_USERNAME", "", 0, None, None, "SMTP authentication username"),
            (
                "SMTP_PASSWORD",
                "",
                1,
                "secret/data/benefit-iq-be/smtp_password",
                "secret_value",
                "SMTP authentication password (Stored in OpenBao)",
            ),
            ("SMTP_FROM_ADDRESS", "noreply@benefitiq.com", 0, None, None, "Default sender email address"),
            ("SMTP_USE_TLS", "false", 0, None, None, "SMTP TLS encryption flag"),
            ("SECURITY_RATE_LIMIT_REQUESTS", "100", 0, None, None, "Rate limit max requests per window"),
            ("SECURITY_RATE_LIMIT_WINDOW_SECONDS", "60", 0, None, None, "Rate limit window duration in seconds"),
            ("SECURITY_ENCRYPTION_PRIVATE_KEY_PATH", "", 0, None, None, "RSA private key path"),
            ("INIT_ADMIN_EMAIL", "admin@benefitiq.com", 0, None, None, "System initial admin user email"),
            (
                "INIT_ADMIN_PASSWORD",
                "Admin@123!",
                1,
                "secret/data/benefit-iq-be/init_admin_password",
                "secret_value",
                "System initial admin user password (Stored in OpenBao)",
            ),
            ("LOG_LEVEL", "INFO", 0, None, None, "Structured logging verbosity level"),
            ("LOG_JSON", "false", 0, None, None, "JSON log formatting flag"),
            ("CORS_ORIGINS", "http://localhost:4200,http://localhost:3000", 0, None, None, "Allowed CORS origin URLs"),
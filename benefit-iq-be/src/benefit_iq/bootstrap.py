"""Benefit IQ Application Bootstrap Module.

Initializes the FastAPI application, wires dependency injection containers,
registers middleware pipelines, configures exception handlers, telemetry,
and sets up ClickHouse/Redis lifecycle context handlers.
"""
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from benefit_iq.api.middleware.correlation import (
    CorrelationIdMiddleware,
)
from benefit_iq.api.middleware.exception import (
    generic_exception_handler,
    invalid_role_handler,
    role_conflict_handler,
    role_not_found_handler,
    auth_exception_handler,
    user_exception_handler,
)
from benefit_iq.api.middleware.request_logging import (
    RequestLoggingMiddleware,
)
from benefit_iq.api.middleware.security_headers import (
    SecurityHeadersMiddleware,
)
from benefit_iq.api.middleware.rate_limiting import (
    RateLimitingMiddleware,
)
from benefit_iq.api.routers.v1.health import (
    router as health_router,
)
from benefit_iq.api.routers.v1.roles import (
    router as roles_router,
)
from benefit_iq.api.routers.v1.auth import (
    router as auth_router,
)
from benefit_iq.api.routers.v1.users import (
    router as users_router,
)
from benefit_iq.api.routers.v1.crypto import (
    router as crypto_router,
)
from benefit_iq.api.routers.v1.config import (
    router as config_router,
)
from benefit_iq.api.routers.v1.analytics import (
    router as analytics_router,
)
from benefit_iq.api.routers.v1.secrets import (
    router as secrets_router,
)
from benefit_iq.api.routers.v1.system import (
    router as system_router,
)
from benefit_iq.domain.exceptions.role_exceptions import (
    InvalidRoleNameException,
    RoleAlreadyExistsException,
    RoleNotFoundException,
)
from benefit_iq.domain.exceptions.auth_exceptions import AuthDomainException
from benefit_iq.domain.exceptions.user_exceptions import UserDomainException

from benefit_iq.infrastructure.configuration.settings import (
    get_settings,
)
from benefit_iq.infrastructure.dependency_injection.container import (
    init_container,
)
from benefit_iq.infrastructure.telemetry.logging import (
    configure_logging,
)
from benefit_iq.infrastructure.telemetry.setup import (
    configure_telemetry,
)
from benefit_iq.infrastructure.persistence.clickhouse.initializer import (
    ClickHouseInitializer,
)


logger = structlog.get_logger(__name__)


def create_application() -> FastAPI:
    """Factory function that constructs, configures, and boots the Benefit IQ FastAPI application.

    Sets up:
    - Centralized Settings & Structured Logging
    - Dependency Injection Container Wiring
    - Custom OpenAPI Specification Metadata & Tags
    - Middleware Stack (CORS, Rate Limiting, Security Headers, Request Tracing, Correlation ID)
    - Domain Exception Handlers
    - API v1 Routers (Auth, Users, Roles, Health)
    - ClickHouse & Redis Lifespan Connection Lifecycle

    Returns:
        FastAPI: Fully configured FastAPI application instance ready to serve requests.
    """
    settings = get_settings()

    configure_logging(settings)

    container = init_container()

    openapi_tags = [
        {
            "name": "Health & Diagnostics",
            "description": (
                "System readiness, liveness probes, database connectivity check, "
                "and telemetry health."
            ),
        },
        {
            "name": "Authentication & Session",
            "description": (
                "User registration, Argon2id authentication, JWT issuance, "
                "OAuth2/OIDC (Google/Microsoft), refresh token rotation, and session management."
            ),
        },
        {
            "name": "User Profile & Management",
            "description": (
                "Authenticated user profile retrieval, account updates, "
                "and identity metadata administration."
            ),
        },
        {
            "name": "Roles & Access Control",
            "description": (
                "Granular Role-Based Access Control (RBAC), custom role creation, "
                "updates, and permission policy listing."
            ),
        },
        {
            "name": "Cryptography & Security",
            "description": (
                "RSA asymmetric encryption/decryption, Base32 alphanumeric transport encoding, "
                "and Argon2id password hashing."
            ),
        },
    ]

    openapi_description = """
    ## 🚀 Benefit IQ Enterprise Backend API
    
    Welcome to the official **Benefit IQ Backend Platform** API specification. Benefit IQ is designed following 
    **Clean Architecture**, **CQRS (Command Query Responsibility Segregation)**, and **SOLID enterprise design principles**.

    ### 🛡️ Key Features & Security Design
    - **Password Security:** Powered by `Argon2id` hashing algorithms.
    - **Authentication:** Stateless `JWT` Access Tokens + Stateful `Redis` Refresh Tokens with **Rotation** & **Reuse Detection**.
    - **OAuth2 / OIDC Integration:** Federated single sign-on support for Google and Microsoft accounts.
    - **Persistence Engine:** Scalable columnar datastore powered by **ClickHouse** (`ReplacingMergeTree`) and **Redis** cache.
    - **Observability:** Full OpenTelemetry distributed tracing, Prometheus metrics, and structured JSON logs with Correlation ID propagation.

    ### 🔑 Quickstart Authentication Guide
    1. Register a new user at `POST /api/v1/auth/register` or login at `POST /api/v1/auth/login`.
    2. Copy the returned `access_token`.
    3. Click the **Authorize** button in Swagger UI (top right) and enter `Bearer <your_access_token>`.
    4. Explore protected endpoints such as `/api/v1/users/me` or `/api/v1/roles`.
    """

    app = FastAPI(
        title="Benefit IQ Enterprise API",
        description=openapi_description,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=openapi_tags,
        contact={
            "name": "Benefit IQ Engineering Team",
            "email": "engineering@benefitiq.com",
        },
        license_info={
            "name": "Proprietary / Commercial Enterprise License",
        },
    )

    app.container = container

    container.wire(
        modules=[
            "benefit_iq.api.routers.v1.roles",
            "benefit_iq.api.routers.v1.health",
            "benefit_iq.api.routers.v1.auth",
            "benefit_iq.api.routers.v1.users",
            "benefit_iq.api.routers.v1.crypto",
            "benefit_iq.api.routers.v1.config",
            "benefit_iq.api.dependencies.services",
            "benefit_iq.api.dependencies.auth",
        ]
    )

    app.add_middleware(
        SecurityHeadersMiddleware
    )

    app.add_middleware(
        RateLimitingMiddleware,
        redis_cache=container.redis(),
        max_requests=settings.security.rate_limit_requests,
        window_seconds=60,
    )

    app.add_middleware(
        CorrelationIdMiddleware
    )

    app.add_middleware(
        RequestLoggingMiddleware
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(
        RoleNotFoundException,
        role_not_found_handler,
    )

    app.add_exception_handler(
        RoleAlreadyExistsException,
        role_conflict_handler,
    )

    app.add_exception_handler(
        InvalidRoleNameException,
        invalid_role_handler,
    )

    app.add_exception_handler(
        AuthDomainException,
        auth_exception_handler,
    )

    app.add_exception_handler(
        UserDomainException,
        user_exception_handler,
    )

    app.add_exception_handler(
        Exception,
        generic_exception_handler,
    )

    api_prefix = (
        f"{settings.api_prefix}"
        f"/{settings.api_version}"
    )

    app.include_router(
        health_router,
        prefix=api_prefix,
    )

    app.include_router(
        roles_router,
        prefix=api_prefix,
    )

    app.include_router(
        auth_router,
        prefix=api_prefix,
    )

    app.include_router(
        users_router,
        prefix=api_prefix,
    )

    app.include_router(
        crypto_router,
        prefix=api_prefix,
    )

    app.include_router(
        config_router,
        prefix=api_prefix,
    )

    app.include_router(
        analytics_router,
        prefix=api_prefix,
    )

    app.include_router(
        secrets_router,
        prefix=api_prefix,
    )

    app.include_router(
        system_router,
        prefix=api_prefix,
    )

    configure_telemetry(
        app,
        settings,
    )

    @asynccontextmanager
    async def lifespan(
        _application: FastAPI,
    ):

        """Async function missing docstring."""
        logger.info(
            "application_starting",
            environment=settings.app_env,
        )

        database = (
            container.clickhouse()
        )

        database.connect()

        try:
            initializer = ClickHouseInitializer(database)
            await initializer.initialize()
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception("clickhouse_initialization_failed")

        redis = container.redis()

        try:
            await redis.connect()
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception(
                "redis_connection_failed"
            )

        # Infrastructure Health & Readiness Check on App Startup
        try:
            from benefit_iq.infrastructure.health.infrastructure_health_checker import InfrastructureHealthChecker
            health_checker = InfrastructureHealthChecker(
                clickhouse=database,
                redis_client=redis,
                openbao_manager=container.secret_manager(),
            )
            await health_checker.check_all()
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("startup_infrastructure_health_probe_warning", error=str(e))

        yield

        logger.info(
            "application_shutting_down"
        )

        database.close()

        await redis.close()

        logger.info(
            "application_stopped"
        )

    app.router.lifespan_context = lifespan

    return app

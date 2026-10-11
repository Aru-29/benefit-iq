"""Dependency Injection Container Configuration for Benefit IQ.

Wires infrastructure, repositories, security services, and application command/query handlers.
"""

# pylint: disable=no-member,unused-variable,unused-import,line-too-long,c-extension-no-member
from dependency_injector import containers, providers

from benefit_iq.application.auth.commands.change_password import ChangePasswordHandler
from benefit_iq.application.auth.commands.forgot_password import ForgotPasswordHandler
from benefit_iq.application.auth.commands.login_user import LoginUserHandler
from benefit_iq.application.auth.commands.logout_user import LogoutUserHandler
from benefit_iq.application.auth.commands.oauth_login import OAuthLoginHandler
from benefit_iq.application.auth.commands.refresh_token import RefreshTokenHandler

# New - Handlers
from benefit_iq.application.auth.commands.register_user import RegisterUserHandler
from benefit_iq.application.auth.commands.reset_password import ResetPasswordHandler
from benefit_iq.application.auth.commands.verify_email import VerifyEmailHandler
from benefit_iq.application.auth.queries.get_current_user import GetCurrentUserHandler
from benefit_iq.application.roles.commands.create_role import CreateRoleHandler
from benefit_iq.application.roles.commands.deactivate_role import DeactivateRoleHandler
from benefit_iq.application.roles.commands.update_role import UpdateRoleHandler
from benefit_iq.application.roles.queries.get_role import GetRoleHandler
from benefit_iq.application.roles.queries.list_roles import ListRolesHandler
from benefit_iq.application.users.commands.create_user import CreateUserHandler
from benefit_iq.application.users.commands.update_profile import UpdateProfileHandler
from benefit_iq.application.users.queries.get_user_profile import GetUserProfileHandler
from benefit_iq.infrastructure.authentication.google.google_provider import GoogleIdentityProvider
from benefit_iq.infrastructure.authentication.jwt_service import JWTService
from benefit_iq.infrastructure.authentication.microsoft.microsoft_provider import (
    MicrosoftIdentityProvider,
)
from benefit_iq.infrastructure.authentication.refresh_token_store import RedisRefreshTokenStore
from benefit_iq.infrastructure.cache.redis.redis_cache import RedisCache
from benefit_iq.infrastructure.configuration.app_config_service import AppConfigService
from benefit_iq.infrastructure.configuration.settings import get_settings
from benefit_iq.infrastructure.email.smtp_email_service import SmtpEmailService
from benefit_iq.infrastructure.persistence.clickhouse.database import ClickHouseDatabase
from benefit_iq.infrastructure.persistence.clickhouse.repositories.app_config_repository import (
    ClickHouseAppConfigRepository,
)

# Existing
from benefit_iq.infrastructure.persistence.clickhouse.repositories.role_repository import (
    ClickHouseRoleRepository,
)

# New - Repositories & Auth
from benefit_iq.infrastructure.persistence.clickhouse.repositories.user_repository import (
    ClickHouseUserRepository,
)
from benefit_iq.infrastructure.secrets.openbao_manager import OpenBaoManager
from benefit_iq.infrastructure.security.encryption import PasswordEncryptionService
from benefit_iq.infrastructure.security.otp_service import OtpService
from benefit_iq.infrastructure.security.password_hasher import Argon2PasswordHasher


class Container(containers.DynamicContainer):
    """
    Simplified dynamic DI container wrapper around dependency_injector.
    Supports easy one-line registration.
    """

    def singleton(self, name: str, cls_or_factory, **kwargs) -> providers.Singleton:
        """Function missing docstring."""
        provider = providers.Singleton(cls_or_factory, **kwargs)
        self.set_provider(name, provider)
        return provider

    def transient(self, name: str, cls_or_factory, **kwargs) -> providers.Factory:
        """Function missing docstring."""
        provider = providers.Factory(cls_or_factory, **kwargs)
        self.set_provider(name, provider)
        return provider

    def scoped(self, name: str, cls_or_factory, **kwargs) -> providers.ThreadSafeSingleton:
        """Function missing docstring."""
        provider = providers.ThreadSafeSingleton(cls_or_factory, **kwargs)
        self.set_provider(name, provider)
        return provider


def init_container() -> Container:
    """Function missing docstring."""
    container = Container()

    # Settings
    settings = get_settings()
    container.singleton("config", lambda: settings)

    # Core Infrastructure
    clickhouse = container.singleton("clickhouse", ClickHouseDatabase, settings=settings.clickhouse)
    redis = container.singleton("redis", RedisCache, settings=settings.redis)

    # Repositories
    role_repository = container.singleton(
        "role_repository", ClickHouseRoleRepository, database=clickhouse
    )
    user_repository = container.singleton(
        "user_repository", ClickHouseUserRepository, database=clickhouse
    )
    app_config_repository = container.singleton(
        "app_config_repository", ClickHouseAppConfigRepository, database=clickhouse
    )

    # Secret Manager & App Config Service
    secret_manager = container.singleton(
        "secret_manager",
        OpenBaoManager,
        bao_url=settings.openbao.url,
        bao_token=settings.openbao.token,
    )
    app_config_service = container.singleton(
        "app_config_service",
        AppConfigService,
        repository=app_config_repository,
        redis_client=redis.provided.client,
        secret_manager=secret_manager,
    )

    # Security & Auth Infrastructure
    password_hasher = container.singleton("password_hasher", Argon2PasswordHasher)
    token_service = container.singleton(
        "token_service",
        JWTService,
        secret_key=settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
        access_token_expire_minutes=settings.jwt.access_token_expire_minutes,
        refresh_token_expire_days=settings.jwt.refresh_token_expire_days,
    )
    refresh_token_store = container.singleton(
        "refresh_token_store",
        RedisRefreshTokenStore,
        redis_client=redis.provided.client,
    )

    # Load persistent private key for frontend password decryption
    import os

    candidate_paths = [
        settings.security.encryption_private_key_path,
        os.path.join(os.path.dirname(__file__), "../../../../private_key.pem"),
        os.path.join(os.path.dirname(__file__), "../../../private_key.pem"),
        os.path.abspath("private_key.pem"),
    ]
    private_key_pem = b"placeholder"
    for path in filter(None, candidate_paths):
        if os.path.exists(path):
            with open(path, "rb") as f:
                private_key_pem = f.read()
            break

    password_encryption = container.singleton(
        "password_encryption", PasswordEncryptionService, private_key_pem=private_key_pem
    )

    email_service = container.singleton(
        "email_service",
        SmtpEmailService,
        host=settings.email.host,
        port=settings.email.port,
        username=settings.email.username,
        password=settings.email.password,
        from_address=settings.email.from_address,
        use_tls=settings.email.use_tls,
        config_service=app_config_service,
    )

    # BenefitIQ Core Repositories
    from benefit_iq.application.benefits.ml_prediction_service import MLPredictionService
    from benefit_iq.application.benefits.notification_service import BenefitNotificationService
    from benefit_iq.application.benefits.nudge_service import NudgeService
    from benefit_iq.application.benefits.portfolio_service import PortfolioAnalyticsService
    from benefit_iq.application.benefits.utilization_service import BenefitUtilizationService
    from benefit_iq.infrastructure.persistence.clickhouse.repositories.benefit_repositories import (
        ClickHouseBenefitRepository,
        ClickHouseBenefitRuleRepository,
        ClickHouseBenefitUsageRepository,
        ClickHouseCardProductBenefitRepository,
        ClickHouseCardProductRepository,
        ClickHouseCardRepository,
        ClickHouseMerchantRepository,
        ClickHouseMLModelRepository,
        ClickHouseNudgeRepository,
        ClickHouseOfferRepository,
        ClickHousePredictionRepository,
        ClickHouseTransactionRepository,
    )

    card_product_repo = container.singleton(
        "card_product_repository", ClickHouseCardProductRepository, database=clickhouse
    )
    card_repo = container.singleton(
        "card_repository", ClickHouseCardRepository, database=clickhouse
    )
    benefit_repo = container.singleton(
        "benefit_repository", ClickHouseBenefitRepository, database=clickhouse
    )
    benefit_rule_repo = container.singleton(
        "benefit_rule_repository", ClickHouseBenefitRuleRepository, database=clickhouse
    )
    card_product_benefit_repo = container.singleton(
        "card_product_benefit_repository",
        ClickHouseCardProductBenefitRepository,
        database=clickhouse,
    )
    container.singleton("merchant_repository", ClickHouseMerchantRepository, database=clickhouse)
    transaction_repo = container.singleton(
        "transaction_repository", ClickHouseTransactionRepository, database=clickhouse
    )
    benefit_usage_repo = container.singleton(
        "benefit_usage_repository", ClickHouseBenefitUsageRepository, database=clickhouse
    )
    offer_repo = container.singleton(
        "offer_repository", ClickHouseOfferRepository, database=clickhouse
    )
    nudge_repo = container.singleton(
        "nudge_repository", ClickHouseNudgeRepository, database=clickhouse
    )
    ml_model_repo = container.singleton(
        "ml_model_repository", ClickHouseMLModelRepository, database=clickhouse
    )
    prediction_repo = container.singleton(
        "prediction_repository", ClickHousePredictionRepository, database=clickhouse
    )

    # BenefitIQ Application Services
    from benefit_iq.infrastructure.persistence.clickhouse.enrollments import (
        ClickHouseEnrollmentRepository,
    )

    enrollments = container.singleton(
        "enrollment_repository", ClickHouseEnrollmentRepository, database=clickhouse
    )
    utilization_service = container.singleton(
        "utilization_service",
        BenefitUtilizationService,
        card_repository=card_repo,
        card_product_repository=card_product_repo,
        card_product_benefit_repository=card_product_benefit_repo,
        benefit_repository=benefit_repo,
        benefit_rule_repository=benefit_rule_repo,
        benefit_usage_repository=benefit_usage_repo,
        transaction_repository=transaction_repo,
        enrollment_repository=enrollments,
    )
    from benefit_iq.application.benefits.workflow_service import BenefitWorkflowService

    container.singleton(
        "workflow_service",
        BenefitWorkflowService,
        cards=card_repo,
        products=card_product_repo,
        transactions=transaction_repo,
        usages=benefit_usage_repo,
        utilization=utilization_service,
        locks=redis,
    )
    redemption_model = None
    if settings.ml_model_directory:
        from pathlib import Path

        from benefit_iq.infrastructure.ml.redemption import RedemptionModel

        redemption_model = RedemptionModel(Path(settings.ml_model_directory))
        if settings.app_env == "production" and not redemption_model.metadata.get(
            "production_validated"
        ):
            raise ValueError("Production ML requires a separately validated artifact")
    container.singleton(
        "ml_prediction_service",
        MLPredictionService,
        ml_model_repository=ml_model_repo,
        prediction_repository=prediction_repo,
        benefit_repository=benefit_repo,
        card_repository=card_repo,
        transaction_repository=transaction_repo,
        redemption_model=redemption_model,
    )
    notification_service = container.singleton(
        "benefit_notification_service",
        BenefitNotificationService,
        users=user_repository,
        email_service=email_service,
    )
    container.singleton(
        "nudge_service",
        NudgeService,
        nudge_repository=nudge_repo,
        offer_repository=offer_repo,
        benefit_repository=benefit_repo,
        card_repository=card_repo,
        notification_service=notification_service,
    )
    container.singleton(
        "portfolio_analytics_service",
        PortfolioAnalyticsService,
        card_repository=card_repo,
        utilization_service=utilization_service,
    )

    # OAuth Providers
    google_provider = container.singleton(
        "google_provider",
        GoogleIdentityProvider,
        client_id=settings.oauth.google_client_id,
        client_secret=settings.oauth.google_client_secret,
        redirect_uri=settings.oauth.redirect_base_url + "/api/v1/auth/google/callback",
    )
    microsoft_provider = container.singleton(
        "microsoft_provider",
        MicrosoftIdentityProvider,
        client_id=settings.oauth.microsoft_client_id,
        client_secret=settings.oauth.microsoft_client_secret,
        redirect_uri=settings.oauth.redirect_base_url + "/api/v1/auth/microsoft/callback",
    )

    identity_providers = {"google": google_provider, "microsoft": microsoft_provider}

    # Role Handlers
    container.transient("create_role_handler", CreateRoleHandler, repository=role_repository)
    container.transient("update_role_handler", UpdateRoleHandler, repository=role_repository)
    container.transient(
        "deactivate_role_handler", DeactivateRoleHandler, repository=role_repository
    )
    container.transient("get_role_handler", GetRoleHandler, repository=role_repository)
    container.transient("list_roles_handler", ListRolesHandler, repository=role_repository)

    otp_service = container.singleton("otp_service", OtpService, redis_client=redis.provided.client)

    # Auth Handlers
    container.transient(
        "register_user_handler",
        RegisterUserHandler,
        user_repository=user_repository,
        role_repository=role_repository,
        password_hasher=password_hasher,
        email_service=email_service,
        otp_service=otp_service,
        password_encryption=password_encryption,
        token_service=token_service,
        refresh_token_store=refresh_token_store,
    )
    container.transient(
        "login_user_handler",
        LoginUserHandler,
        user_repository=user_repository,
        password_hasher=password_hasher,
        token_service=token_service,
        refresh_token_store=refresh_token_store,
        email_service=email_service,
        otp_service=otp_service,
        password_encryption=password_encryption,
    )
    container.transient(
        "refresh_token_handler",
        RefreshTokenHandler,
        token_service=token_service,
        refresh_token_store=refresh_token_store,
        user_repository=user_repository,
    )
    container.transient(
        "logout_user_handler",
        LogoutUserHandler,
        token_service=token_service,
        refresh_token_store=refresh_token_store,
    )
    container.transient(
        "forgot_password_handler",
        ForgotPasswordHandler,
        user_repository=user_repository,
        token_service=token_service,
        email_service=email_service,
    )
    container.transient(
        "reset_password_handler",
        ResetPasswordHandler,
        user_repository=user_repository,
        token_service=token_service,
        password_hasher=password_hasher,
        email_service=email_service,
        refresh_token_store=refresh_token_store,
    )
    container.transient(
        "change_password_handler",
        ChangePasswordHandler,
        user_repository=user_repository,
        password_hasher=password_hasher,
        email_service=email_service,
    )
    container.transient(
        "verify_email_handler",
        VerifyEmailHandler,
        user_repository=user_repository,
        token_service=token_service,
    )
    container.transient(
        "oauth_login_handler",
        OAuthLoginHandler,
        user_repository=user_repository,
        role_repository=role_repository,
        token_service=token_service,
        identity_providers=identity_providers,
        refresh_token_store=refresh_token_store,
    )
    container.transient(
        "get_current_user_handler", GetCurrentUserHandler, user_repository=user_repository
    )

    # User Handlers
    container.transient(
        "create_user_handler",
        CreateUserHandler,
        user_repository=user_repository,
        role_repository=role_repository,
        password_hasher=password_hasher,
    )
    container.transient(
        "update_profile_handler", UpdateProfileHandler, user_repository=user_repository
    )
    container.transient(
        "get_user_profile_handler", GetUserProfileHandler, user_repository=user_repository
    )

    container.wire(
        modules=[
            "benefit_iq.api.routers.v1.roles",
            "benefit_iq.api.routers.v1.health",
            "benefit_iq.api.routers.v1.auth",
            "benefit_iq.api.routers.v1.users",
            "benefit_iq.api.routers.v1.crypto",
            "benefit_iq.api.routers.v1.config",
            "benefit_iq.api.routers.v1.analytics",
            "benefit_iq.api.dependencies.services",
            "benefit_iq.api.dependencies.auth",
            "benefit_iq.api.routers.v1.secrets",
            "benefit_iq.api.routers.v1.system",
        ]
    )

    return container

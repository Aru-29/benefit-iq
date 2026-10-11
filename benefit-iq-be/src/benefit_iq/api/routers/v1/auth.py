"""Authentication & Session Router.

Handles user registration with 2-Step OTP email verification, 2-Step 2FA login OTP authentication,
Argon2id password verification, JWT token pair issuance, refresh token rotation, and OAuth2/OIDC SSO.
"""

# pylint: disable=line-too-long
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request, status

from benefit_iq.api.dependencies.auth import get_current_user_id
from benefit_iq.api.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    OAuthLoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
    VerifyOtpRequest,
)
from benefit_iq.api.schemas.common import ApiResponse
from benefit_iq.application.auth.commands.change_password import (
    ChangePasswordCommand,
    ChangePasswordHandler,
)
from benefit_iq.application.auth.commands.forgot_password import (
    ForgotPasswordCommand,
    ForgotPasswordHandler,
)
from benefit_iq.application.auth.commands.login_user import (
    LoginUserCommand,
    LoginUserHandler,
    VerifyLoginOtpCommand,
)
from benefit_iq.application.auth.commands.logout_user import (
    LogoutUserCommand,
    LogoutUserHandler,
)
from benefit_iq.application.auth.commands.oauth_login import (
    OAuthLoginCommand,
    OAuthLoginHandler,
)
from benefit_iq.application.auth.commands.refresh_token import (
    RefreshTokenCommand,
    RefreshTokenHandler,
)
from benefit_iq.application.auth.commands.register_user import (
    RegisterUserCommand,
    RegisterUserHandler,
    VerifyRegistrationOtpCommand,
)
from benefit_iq.application.auth.commands.reset_password import (
    ResetPasswordCommand,
    ResetPasswordHandler,
)
from benefit_iq.application.auth.commands.verify_email import (
    VerifyEmailCommand,
    VerifyEmailHandler,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication & Session"],
)


@router.post("/register", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
@inject
async def register(
    request: RegisterRequest,
    handler: RegisterUserHandler = Depends(Provide["register_user_handler"]),
):
    """Step 1 Registration: Validates details, hashes password, and emails a 6-digit OTP code."""
    res = await handler.handle(RegisterUserCommand(**request.model_dump()))
    return ApiResponse(success=True, data=res)


@router.post("/verify-registration-otp", response_model=ApiResponse[TokenResponse])
@inject
async def verify_registration_otp(
    request: VerifyOtpRequest,
    handler: RegisterUserHandler = Depends(Provide["register_user_handler"]),
):
    """Step 2 Registration: Verifies OTP code, creates user account, and issues JWT tokens."""
    token_pair = await handler.handle_verify_otp(
        VerifyRegistrationOtpCommand(email=request.email, otp=request.otp)
    )
    return ApiResponse(
        success=True,
        data=TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            expires_in=token_pair.expires_in,
        ),
    )


@router.post("/login", response_model=ApiResponse[dict])
@inject
async def login(
    request: LoginRequest,
    req: Request,
    handler: LoginUserHandler = Depends(Provide["login_user_handler"]),
):
    """Step 1 Login: Verifies credentials and emails a 6-digit 2FA login OTP code."""
    res = await handler.handle(
        LoginUserCommand(
            email=request.email,
            password=request.password,
            user_agent=req.headers.get("user-agent"),
            ip_address=req.client.host if req.client else None,
        )
    )
    return ApiResponse(success=True, data=res)


@router.post("/verify-login-otp", response_model=ApiResponse[TokenResponse])
@inject
async def verify_login_otp(
    request: VerifyOtpRequest,
    req: Request,
    handler: LoginUserHandler = Depends(Provide["login_user_handler"]),
):
    """Step 2 Login: Verifies 2FA OTP code and issues JWT access token & refresh token."""
    token_pair = await handler.handle_verify_login_otp(
        VerifyLoginOtpCommand(
            email=request.email,
            otp=request.otp,
            user_agent=req.headers.get("user-agent"),
            ip_address=req.client.host if req.client else None,
        )
    )
    return ApiResponse(
        success=True,
        data=TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            expires_in=token_pair.expires_in,
        ),
    )


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
@inject
async def refresh(
    request: RefreshRequest,
    handler: RefreshTokenHandler = Depends(Provide["refresh_token_handler"]),
):
    """Rotates refresh token and issues a new access token."""
    token_pair = await handler.handle(RefreshTokenCommand(refresh_token=request.refresh_token))
    return ApiResponse(
        success=True,
        data=TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            expires_in=token_pair.expires_in,
        ),
    )


@router.post("/logout", response_model=ApiResponse[dict])
@inject
async def logout(
    request: RefreshRequest,
    handler: LogoutUserHandler = Depends(Provide["logout_user_handler"]),
):
    """Revokes session refresh token."""
    await handler.handle(LogoutUserCommand(refresh_token=request.refresh_token))
    return ApiResponse(success=True, data={"message": "Logged out successfully."})


@router.post("/forgot-password", response_model=ApiResponse[dict])
@inject
async def forgot_password(
    request: ForgotPasswordRequest,
    handler: ForgotPasswordHandler = Depends(Provide["forgot_password_handler"]),
):
    """Initiates password reset workflow for the specified email."""
    await handler.handle(ForgotPasswordCommand(email=request.email))
    return ApiResponse(
        success=True,
        data={"message": "If that email is registered, a reset link has been sent."},
    )


@router.post("/reset-password", response_model=ApiResponse[dict])
@inject
async def reset_password(
    request: ResetPasswordRequest,
    handler: ResetPasswordHandler = Depends(Provide["reset_password_handler"]),
):
    """Resets user password using a verified password reset token."""
    await handler.handle(
        ResetPasswordCommand(token=request.token, new_password=request.new_password)
    )
    return ApiResponse(success=True, data={"message": "Password reset successfully."})


@router.post("/change-password", response_model=ApiResponse[dict])
@inject
async def change_password(
    request: ChangePasswordRequest,
    user_id: str = Depends(get_current_user_id),
    handler: ChangePasswordHandler = Depends(Provide["change_password_handler"]),
):
    """Changes current logged-in user password."""
    await handler.handle(
        ChangePasswordCommand(
            user_id=user_id,
            current_password=request.current_password,
            new_password=request.new_password,
        )
    )
    return ApiResponse(success=True, data={"message": "Password changed successfully."})


@router.post("/verify-email", response_model=ApiResponse[dict])
@inject
async def verify_email(
    request: VerifyEmailRequest,
    handler: VerifyEmailHandler = Depends(Provide["verify_email_handler"]),
):
    """Verifies email address via legacy link token."""
    await handler.handle(VerifyEmailCommand(token=request.token))
    return ApiResponse(success=True, data={"message": "Email verified successfully."})


@router.post("/{provider}/callback", response_model=ApiResponse[TokenResponse])
@inject
async def oauth_callback(
    provider: str,
    request: OAuthLoginRequest,
    req: Request,
    handler: OAuthLoginHandler = Depends(Provide["oauth_login_handler"]),
):
    """Processes OAuth2 authorization code callback and issues JWT tokens."""
    token_pair = await handler.handle(
        OAuthLoginCommand(
            code=request.code,
            token=request.token,
            provider_name=provider,
            user_agent=req.headers.get("user-agent"),
            ip_address=req.client.host if req.client else None,
        )
    )
    return ApiResponse(
        success=True,
        data=TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            expires_in=token_pair.expires_in,
        ),
    )


@router.get("/public-key")
@inject
async def public_key(crypto=Depends(Provide["password_encryption"])):
    from cryptography.hazmat.primitives import serialization
    pem = crypto.public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return ApiResponse(success=True, data={"public_key": pem.decode("ascii")})

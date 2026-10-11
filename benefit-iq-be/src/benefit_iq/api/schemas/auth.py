"""
Module missing docstring.
"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Class missing docstring."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    username: str
    middle_name: str | None = None


class LoginRequest(BaseModel):
    """Request payload for Step 1 login authentication."""

    email: EmailStr
    password: str


class VerifyOtpRequest(BaseModel):
    """Request payload for verifying 2-Step OTP code for registration or login."""

    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit numeric OTP code")


class RefreshRequest(BaseModel):
    """Class missing docstring."""

    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Class missing docstring."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Class missing docstring."""

    token: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    """Request payload for changing or setting local password."""

    new_password: str = Field(..., min_length=8)
    current_password: str | None = Field(
        None,
        description="Current password (Required for local users, optional for SSO users setting initial password)",
    )


class VerifyEmailRequest(BaseModel):
    """Class missing docstring."""

    token: str


class OAuthLoginRequest(BaseModel):
    """Request payload for Google/Microsoft OAuth authentication."""

    code: str | None = None
    token: str | None = None


class TokenResponse(BaseModel):
    """Class missing docstring."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

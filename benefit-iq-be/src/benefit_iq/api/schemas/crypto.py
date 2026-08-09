"""Cryptography API Request and Response Schemas."""
from pydantic import BaseModel, Field


class EncryptRequest(BaseModel):
    """Request payload for encrypting data."""

    data: str = Field(..., description="Plaintext string to encrypt")


class DecryptRequest(BaseModel):
    """Request payload for decrypting data."""

    encrypted_data: str = Field(..., description="Encrypted Base64 string to decrypt")


class EncryptAlphanumericRequest(BaseModel):
    """Request payload for encrypting data with alphanumeric output."""

    data: str = Field(..., description="Plaintext string to encrypt")


class DecryptAlphanumericRequest(BaseModel):
    """Request payload for decrypting alphanumeric data."""

    alphanumeric_data: str = Field(..., description="Base32 alphanumeric ciphertext string")


class HashPasswordRequest(BaseModel):
    """Request payload for Argon2id password hashing."""

    data: str = Field(..., description="Plaintext string to hash")


class VerifyHashRequest(BaseModel):
    """Request payload for verifying Argon2id password hash."""

    plain_text: str = Field(..., description="Plaintext string to check")
    hash: str = Field(..., description="Argon2id hash string to compare against")


class CryptoResultResponse(BaseModel):
    """Generic response for cryptography operations."""

    result: str = Field(..., description="Output string result of cryptographic operation")
    is_valid: bool | None = Field(None, description="Verification result if applicable")

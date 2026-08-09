"""Cryptography & Security Operations Router.

Exposes endpoints for RSA encryption, RSA decryption, Base32 alphanumeric transport encoding,
and Argon2id password hashing and verification.
"""
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from benefit_iq.api.schemas.common import ApiResponse
from benefit_iq.api.schemas.crypto import (
    DecryptAlphanumericRequest,
    DecryptRequest,
    EncryptAlphanumericRequest,
    EncryptRequest,
    CryptoResultResponse,
    HashPasswordRequest,
    VerifyHashRequest,
)
from benefit_iq.api.dependencies.auth import get_current_admin_user
from benefit_iq.infrastructure.security.encryption import PasswordEncryptionService
from benefit_iq.infrastructure.security.password_hasher import Argon2PasswordHasher

router = APIRouter(
    prefix="/crypto",
    tags=["Cryptography & Security"],
    dependencies=[Depends(get_current_admin_user)],
)


@router.post("/encrypt", response_model=ApiResponse[CryptoResultResponse])
@inject
async def encrypt(
    request: EncryptRequest,
    crypto_service: PasswordEncryptionService = Depends(Provide["password_encryption"]),
):
    """Encrypts plaintext string using RSA public key encryption."""
    try:
        encrypted = crypto_service.encrypt(request.data)
        return ApiResponse(success=True, data=CryptoResultResponse(result=encrypted))
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Encryption failed: {e}",
        ) from e


@router.post("/decrypt", response_model=ApiResponse[CryptoResultResponse])
@inject
async def decrypt(
    request: DecryptRequest,
    crypto_service: PasswordEncryptionService = Depends(Provide["password_encryption"]),
):
    """Decrypts Base64 encoded RSA ciphertext string using RSA private key."""
    try:
        decrypted = crypto_service.decrypt(request.encrypted_data)
        return ApiResponse(success=True, data=CryptoResultResponse(result=decrypted))
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Decryption failed: {e}",
        ) from e


@router.post("/encrypt-alphanumeric", response_model=ApiResponse[CryptoResultResponse])
@inject
async def encrypt_alphanumeric(
    request: EncryptAlphanumericRequest,
    crypto_service: PasswordEncryptionService = Depends(Provide["password_encryption"]),
):
    """Encrypts plaintext string and encodes result as Base32 alphanumeric string."""
    try:
        encrypted = crypto_service.encrypt_alphanumeric(request.data)
        return ApiResponse(success=True, data=CryptoResultResponse(result=encrypted))
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Alphanumeric encryption failed: {e}",
        ) from e


@router.post("/decrypt-alphanumeric", response_model=ApiResponse[CryptoResultResponse])
@inject
async def decrypt_alphanumeric(
    request: DecryptAlphanumericRequest,
    crypto_service: PasswordEncryptionService = Depends(Provide["password_encryption"]),
):
    """Decodes Base32 alphanumeric ciphertext string and decrypts using RSA private key."""
    try:
        decrypted = crypto_service.decrypt_alphanumeric(request.alphanumeric_data)
        return ApiResponse(success=True, data=CryptoResultResponse(result=decrypted))
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Alphanumeric decryption failed: {e}",
        ) from e


@router.post("/hash", response_model=ApiResponse[CryptoResultResponse])
@inject
async def hash_password(
    request: HashPasswordRequest,
    hasher: Argon2PasswordHasher = Depends(Provide["password_hasher"]),
):
    """Hashes a plaintext string using Argon2id algorithm."""
    try:
        hashed = hasher.hash_password(request.data)
        return ApiResponse(success=True, data=CryptoResultResponse(result=hashed))
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password hashing failed: {e}",
        ) from e


@router.post("/verify-hash", response_model=ApiResponse[CryptoResultResponse])
@inject
async def verify_hash(
    request: VerifyHashRequest,
    hasher: Argon2PasswordHasher = Depends(Provide["password_hasher"]),
):
    """Verifies a plaintext string against an Argon2id hash."""
    try:
        is_valid = hasher.verify_password(request.plain_text, request.hash)
        return ApiResponse(
            success=True,
            data=CryptoResultResponse(result="verification_completed", is_valid=is_valid),
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Hash verification failed: {e}",
        ) from e

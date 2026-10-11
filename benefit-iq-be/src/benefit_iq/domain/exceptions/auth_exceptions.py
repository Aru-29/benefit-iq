"""
Module missing docstring.
"""


class AuthDomainException(Exception):
    """Base exception for authentication domain errors."""


class TokenExpiredException(AuthDomainException):
    """Raised when a token (JWT, reset, verification) has expired."""


class TokenInvalidException(AuthDomainException):
    """Raised when a token is structurally invalid or verification fails."""


class RefreshTokenReusedException(AuthDomainException):
    """Raised when a refresh token has already been used, indicating potential compromise."""


class TokenFamilyRevokedException(AuthDomainException):
    """Raised when a token family has been revoked."""

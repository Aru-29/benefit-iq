"""
Module missing docstring.
"""
class UserDomainException(Exception):
    """Base exception for user domain errors."""


class UserNotFoundException(UserDomainException):
    """Raised when a user cannot be found."""


class UserAlreadyExistsException(UserDomainException):
    """Raised when a user already exists (e.g., username/email conflict)."""


class InvalidCredentialsException(UserDomainException):
    """Raised when user credentials do not match."""


class EmailNotVerifiedException(UserDomainException):
    """Raised when an operation requires verified email, but the email is not verified."""


class InvalidOtpException(UserDomainException):
    """Raised when an OTP code is invalid or expired."""

"""
Module missing docstring.
"""


class ApplicationException(Exception):
    """Base application exception."""


class NotFoundException(ApplicationException):
    """Resource was not found."""


class ConflictException(ApplicationException):
    """Resource conflict occurred."""


class ValidationException(ApplicationException):
    """Application validation failed."""


class UnauthorizedException(ApplicationException):
    """Authentication is required."""


class ForbiddenException(ApplicationException):
    """Authenticated user is not authorized."""

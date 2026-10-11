"""
Module missing docstring.
"""


class RoleDomainException(Exception):
    """Base exception for role domain errors."""


class InvalidRoleNameException(RoleDomainException):
    """Raised when a role name is invalid."""


class RoleAlreadyExistsException(RoleDomainException):
    """Raised when a role already exists."""


class RoleNotFoundException(RoleDomainException):
    """Raised when a role cannot be found."""

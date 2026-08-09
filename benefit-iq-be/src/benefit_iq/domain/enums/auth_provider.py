"""
Module missing docstring.
"""
from enum import Enum


class AuthProvider(str, Enum):
    """Class missing docstring."""
    LOCAL = "local"
    GOOGLE = "google"
    MICROSOFT = "microsoft"

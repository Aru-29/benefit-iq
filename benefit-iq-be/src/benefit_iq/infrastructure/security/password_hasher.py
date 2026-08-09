"""
Module missing docstring.
"""
from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError

from benefit_iq.application.contracts.auth.password_hasher import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    """Class missing docstring."""
    def __init__(self) -> None:
        """Function missing docstring."""
        self.ph = Argon2Hasher()

    def hash_password(self, password: str) -> str:
        """Function missing docstring."""
        return self.ph.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Function missing docstring."""
        try:
            return self.ph.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False

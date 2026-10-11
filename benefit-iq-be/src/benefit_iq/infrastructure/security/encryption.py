"""Cryptography and Encryption Services for Benefit IQ."""

import base64

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key


class PasswordEncryptionService:
    """Asymmetric RSA Cryptography & Alphanumeric Encoding Service.

    Supports RSA keypair encryption, decryption, and reversible Base32 alphanumeric transport encoding.
    """

    def __init__(self, private_key_pem: bytes) -> None:
        """Initialize RSA private key from PEM bytes, generating a keypair if placeholder is provided."""
        if not private_key_pem or private_key_pem == b"placeholder":
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
        else:
            self.private_key = load_pem_private_key(private_key_pem, password=None)
        self.public_key = self.private_key.public_key()

    @staticmethod
    def encode_alphanumeric(ciphertext: bytes) -> str:
        """Encodes raw bytes to a strict Base32 alphanumeric string (A-Z, 2-7)."""
        return base64.b32encode(ciphertext).decode("utf-8").replace("=", "")

    @staticmethod
    def decode_alphanumeric(encoded_text: str) -> bytes:
        """Decodes a strict Base32 alphanumeric string back to raw bytes."""
        padding_needed = len(encoded_text) % 8
        if padding_needed:
            encoded_text += "=" * (8 - padding_needed)
        return base64.b32decode(encoded_text.upper())

    def encrypt(self, plaintext: str) -> str:
        """Encrypts plaintext string using RSA public key and returns Base64 encoded string."""
        try:
            ciphertext = self.public_key.encrypt(
                plaintext.encode("utf-8"),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return base64.b64encode(ciphertext).decode("utf-8")
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise ValueError(f"Encryption failed: {e}") from e

    def decrypt(self, ciphertext_b64: str) -> str:
        """Decrypts Base64 encoded RSA ciphertext string."""
        try:
            raw_ciphertext = base64.b64decode(ciphertext_b64)
            plaintext_bytes = self.private_key.decrypt(
                raw_ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return plaintext_bytes.decode("utf-8")
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise ValueError(f"Decryption failed: {e}") from e

    def encrypt_alphanumeric(self, plaintext: str) -> str:
        """Encrypts plaintext string and encodes result as Base32 alphanumeric string."""
        try:
            ciphertext = self.public_key.encrypt(
                plaintext.encode("utf-8"),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return self.encode_alphanumeric(ciphertext)
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise ValueError(f"Alphanumeric encryption failed: {e}") from e

    def decrypt_password(self, alphanumeric_ciphertext: str) -> str:
        """Decodes alphanumeric ciphertext and decrypts using RSA private key."""
        try:
            ciphertext = self.decode_alphanumeric(alphanumeric_ciphertext)
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise ValueError(f"Invalid alphanumeric encoding: {e}") from e

        try:
            plaintext_bytes = self.private_key.decrypt(
                ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return plaintext_bytes.decode("utf-8")
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise ValueError(f"Decryption failed: {e}") from e

    def decrypt_alphanumeric(self, alphanumeric_ciphertext: str) -> str:
        """Alias for decrypt_password."""
        return self.decrypt_password(alphanumeric_ciphertext)

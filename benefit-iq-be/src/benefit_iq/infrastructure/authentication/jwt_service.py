"""
Module missing docstring.
"""
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import jwt, JWTError

from benefit_iq.application.contracts.auth.token_service import TokenService, TokenPair, TokenPayload
from benefit_iq.domain.exceptions.auth_exceptions import TokenInvalidException, TokenExpiredException


class JWTService(TokenService):
    """Class missing docstring."""
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7,
    ) -> None:
        """Function missing docstring."""
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def generate_token_pair(self, user_id: UUID, role_id: UUID, session_id: str) -> TokenPair:
        """Function missing docstring."""
        import uuid
        now = datetime.now(UTC)

        access_exp = now + timedelta(minutes=self.access_token_expire_minutes)
        refresh_exp = now + timedelta(days=self.refresh_token_expire_days)

        refresh_jti = str(uuid.uuid4())
        access_jti = str(uuid.uuid4())

        access_payload = {
            "sub": str(user_id),
            "role_id": str(role_id),
            "session_id": session_id,
            "type": "access",
            "jti": access_jti,
            "exp": access_exp,
            "iat": now,
        }

        refresh_payload = {
            "sub": str(user_id),
            "role_id": str(role_id),
            "session_id": session_id,
            "type": "refresh",
            "jti": refresh_jti,
            "exp": refresh_exp,
            "iat": now,
        }

        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)

        expires_in = int((access_exp - now).total_seconds())

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    def decode_token(self, token: str) -> TokenPayload:
        """Function missing docstring."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
            return TokenPayload(
                user_id=UUID(payload["sub"]),
                role_id=UUID(payload["role_id"]),
                session_id=payload["session_id"],
                token_type=payload["type"],
                exp=exp,
                jti=payload["jti"],
            )
        except jwt.ExpiredSignatureError:
            raise TokenExpiredException("Token has expired.")
        except (JWTError, KeyError, ValueError) as e:
            raise TokenInvalidException(f"Invalid token: {str(e)}")

    def _generate_single_use_token(self, user_id: UUID, token_type: str, expire_minutes: int = 1440) -> str:
        """Function missing docstring."""
        import uuid
        now = datetime.now(UTC)
        exp = now + timedelta(minutes=expire_minutes)
        payload = {
            "sub": str(user_id),
            "type": token_type,
            "jti": str(uuid.uuid4()),
            "exp": exp,
            "iat": now,
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def _decode_single_use_token(self, token: str, expected_type: str) -> UUID:
        """Function missing docstring."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != expected_type:
                raise TokenInvalidException(f"Expected token type '{expected_type}'")
            return UUID(payload["sub"])
        except jwt.ExpiredSignatureError:
            raise TokenExpiredException("Token has expired.")
        except (JWTError, KeyError, ValueError) as e:
            raise TokenInvalidException(f"Invalid token: {str(e)}")

    def generate_verification_token(self, user_id: UUID) -> str:
        """Function missing docstring."""
        return self._generate_single_use_token(user_id, "verification", expire_minutes=1440)

    def decode_verification_token(self, token: str) -> UUID:
        """Function missing docstring."""
        return self._decode_single_use_token(token, "verification")

    def generate_password_reset_token(self, user_id: UUID) -> str:
        """Function missing docstring."""
        return self._generate_single_use_token(user_id, "password_reset", expire_minutes=15)

    def decode_password_reset_token(self, token: str) -> UUID:
        """Function missing docstring."""
        return self._decode_single_use_token(token, "password_reset")

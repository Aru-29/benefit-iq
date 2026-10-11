"""OpenBao (HashiCorp Vault compatible) Secrets Manager.

Provides secure secret CRUD operations against a Vault-compatible
KV v2 secrets engine using HTTP API. Used for JWT keys, OAuth secrets,
SMTP credentials, and other sensitive configuration.
"""

from typing import Any

import httpx
import structlog

from benefit_iq.application.contracts.auth.secret_manager import SecretManager

logger = structlog.get_logger(__name__)


class OpenBaoManager(SecretManager):
    """Vault-compatible secret manager using KV v2 HTTP API."""

    def __init__(self, bao_url: str, bao_token: str) -> None:
        """Initialize OpenBao connection parameters."""
        self._url = bao_url.rstrip("/")
        self._token = bao_token
        self._headers = {"X-Vault-Token": self._token}

    async def get_secret(self, path: str, key: str) -> str:
        """Retrieves a specific key from a secret path in Vault KV v2."""
        data = await self._fetch_secret_data(path)
        if data and key in data:
            return str(data[key])
        return ""

    async def get_secrets(self, path: str) -> dict[str, str]:
        """Retrieves all keys for a specific secret path."""
        data = await self._fetch_secret_data(path)
        if data:
            return {k: str(v) for k, v in data.items()}
        return {}

    async def set_secret(self, path: str, secrets: dict[str, str]) -> None:
        """Stores a dictionary of secrets at the specified path."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self._url}/v1/{path}",
                    headers=self._headers,
                    json={"data": secrets},
                )
                if response.status_code not in (200, 204):
                    logger.warning(
                        "openbao_secret_write_failed",
                        path=path,
                        status=response.status_code,
                    )
        except httpx.HTTPError as exc:
            logger.error("openbao_write_error", path=path, error=str(exc))

    async def delete_secret(self, path: str) -> bool:
        """Deletes a secret from Vault KV v2 at the given path."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(
                    f"{self._url}/v1/{path}",
                    headers=self._headers,
                )
                return response.status_code in (200, 204)
        except httpx.HTTPError as exc:
            logger.error("openbao_delete_error", path=path, error=str(exc))
            return False

    async def health_check(self) -> dict[str, Any]:
        """Checks OpenBao/Vault health endpoint."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self._url}/v1/sys/health",
                    headers=self._headers,
                )
                return {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "details": response.json() if response.status_code == 200 else None,
                }
        except httpx.HTTPError:
            return {"status": "unreachable"}

    async def _fetch_secret_data(self, path: str) -> dict[str, Any] | None:
        """Internal helper to fetch raw secret data from Vault."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self._url}/v1/{path}",
                    headers=self._headers,
                )
                if response.status_code != 200:
                    logger.warning(
                        "openbao_secret_fetch_failed",
                        path=path,
                        status=response.status_code,
                    )
                    return None

                data = response.json().get("data", {})
                # KV v2 wraps data inside data.data
                if "data" in data:
                    data = data["data"]
                return data

        except httpx.HTTPError as exc:
            logger.error("openbao_connection_error", path=path, error=str(exc))
            return None


# Alias for backward compatibility with existing router imports
OpenBaoSecretsManager = OpenBaoManager

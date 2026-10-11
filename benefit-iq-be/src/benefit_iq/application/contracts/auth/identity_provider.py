"""External OAuth2 / OIDC Identity Provider Contracts."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class IdentityProfile:
    """User profile data extracted from an external identity provider."""

    external_id: str
    email: str
    first_name: str
    last_name: str
    is_email_verified: bool


class ExternalIdentityProvider(ABC):
    """Abstract contract for OAuth2/OIDC identity providers (Google, Microsoft)."""

    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        """Generates provider authorization URL."""
        ...

    @abstractmethod
    async def exchange_code_for_profile(self, code: str) -> IdentityProfile:
        """Exchanges an authorization code for user identity profile."""
        ...

    @abstractmethod
    async def validate_token_and_get_profile(self, token: str) -> IdentityProfile:
        """Validates a frontend-obtained OAuth/ID token and returns user identity profile."""
        ...

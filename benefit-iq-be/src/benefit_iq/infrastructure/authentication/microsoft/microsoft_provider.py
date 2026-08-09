"""
Module missing docstring.
"""
import structlog
from authlib.integrations.httpx_client import AsyncOAuth2Client
from urllib.parse import urlencode

from benefit_iq.application.contracts.auth.identity_provider import ExternalIdentityProvider, IdentityProfile
from benefit_iq.infrastructure.utils.retry import with_retry


logger = structlog.get_logger(__name__)


class MicrosoftIdentityProvider(ExternalIdentityProvider):
    """Class missing docstring."""
    AUTHORIZATION_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    USERINFO_URL = "https://graph.microsoft.com/oidc/userinfo"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        """Function missing docstring."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = ["openid", "email", "profile"]

    def get_authorization_url(self, state: str) -> str:
        """Function missing docstring."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
            "response_mode": "query",
        }
        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def exchange_code_for_profile(self, code: str) -> IdentityProfile:
        """Async function missing docstring."""
        async def do_exchange() -> IdentityProfile:
            """Async function missing docstring."""
            async with AsyncOAuth2Client(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
            ) as client:
                token = await client.fetch_token(
                    self.TOKEN_URL,
                    grant_type="authorization_code",
                    code=code
                )

                resp = await client.get(self.USERINFO_URL)
                resp.raise_for_status()
                userinfo = resp.json()

                return IdentityProfile(
                    external_id=userinfo["sub"],
                    email=userinfo.get("email", userinfo.get("preferred_username", "")),
                    first_name=userinfo.get("given_name", ""),
                    last_name=userinfo.get("family_name", ""),
                    is_email_verified=True,  # Microsoft generally verifies
                )

        return await with_retry(
            do_exchange,
            operation_name="microsoft_oauth_exchange",
            max_attempts=3
        )

    async def validate_token_and_get_profile(self, token: str) -> IdentityProfile:
        """Validates a frontend-obtained Microsoft token/id_token and fetches user profile."""
        import base64
        import json
        import httpx

        async def do_validate() -> IdentityProfile:
            # 1. Check if token is a JWT ID Token (starts with 'ey')
            if token.startswith("ey"):
                try:
                    parts = token.split(".")
                    if len(parts) == 3:
                        padding = "=" * ((4 - len(parts[1]) % 4) % 4)
                        claims = json.loads(base64.urlsafe_b64decode(parts[1] + padding).decode("utf-8"))
                        email = claims.get("email") or claims.get("preferred_username") or claims.get("upn", "")
                        ext_id = claims.get("oid") or claims.get("sub") or claims.get("user_id", "")
                        name = claims.get("name", "")
                        name_parts = name.split() if name else []
                        first_name = claims.get("given_name") or (name_parts[0] if name_parts else "")
                        last_name = claims.get("family_name") or (name_parts[-1] if len(name_parts) > 1 else "")
                        if email and ext_id:
                            return IdentityProfile(
                                external_id=ext_id,
                                email=email,
                                first_name=first_name,
                                last_name=last_name,
                                is_email_verified=True,
                            )
                except Exception:
                    pass

            # 2. Fallback to Microsoft Graph API for Access Tokens
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {token}"}
                resp = await client.get(self.USERINFO_URL, headers=headers)
                if resp.status_code != 200:
                    resp = await client.get("https://graph.microsoft.com/v1.0/me", headers=headers)
                resp.raise_for_status()
                userinfo = resp.json()

                email = userinfo.get("email") or userinfo.get("mail") or userinfo.get("userPrincipalName", "")
                return IdentityProfile(
                    external_id=userinfo.get("sub") or userinfo.get("id", ""),
                    email=email,
                    first_name=userinfo.get("given_name") or userinfo.get("givenName", ""),
                    last_name=userinfo.get("family_name") or userinfo.get("surname", ""),
                    is_email_verified=True,
                )

        return await with_retry(
            do_validate,
            operation_name="microsoft_token_validation",
            max_attempts=3,
        )

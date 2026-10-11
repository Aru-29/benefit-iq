"""Security Headers Middleware for Benefit IQ API.

Applies enterprise-grade HTTP security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
to protect against common web vulnerabilities (XSS, Clickjacking, MIME-sniffing).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# pylint: disable=too-few-public-methods
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """HTTP middleware that injects security headers into every outgoing response.

    Automatically adjusts Content-Security-Policy (CSP) for API documentation endpoints
    (/docs, /redoc, /openapi.json) to allow loading CDN assets required by Swagger UI.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and attach security headers to the response.

        Args:
            request: Incoming HTTP request.
            call_next: Middleware chain callable.

        Returns:
            Response: HTTP response enriched with security headers.
        """
        response = await call_next(request)

        # Standard hardening headers
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Relax CSP for Swagger UI / ReDoc docs so CDN scripts/styles render correctly
        if request.url.path in ("/docs", "/redoc", "/openapi.json"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com;"
            )
        else:
            response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response

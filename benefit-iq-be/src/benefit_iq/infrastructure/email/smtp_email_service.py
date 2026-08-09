"""
Module missing docstring.
"""
import aiosmtplib
import structlog
from email.message import EmailMessage

from benefit_iq.application.contracts.auth.email_service import EmailService
from benefit_iq.infrastructure.utils.retry import with_retry


from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from benefit_iq.infrastructure.configuration.app_config_service import AppConfigService


logger = structlog.get_logger(__name__)


class SmtpEmailService(EmailService):
    """Class missing docstring."""
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_address: str,
        use_tls: bool,
        config_service: Any = None,
    ) -> None:
        """Function missing docstring."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_address = from_address
        self.use_tls = use_tls
        self.config_service = config_service

    async def _get_smtp_credentials(self) -> tuple[str, int, str, str, str, bool]:
        """Resolves SMTP host, port, username (from DB), password (from KeyVault/OpenBao), sender email, and TLS flag."""
        host = self.host
        port = self.port
        username = self.username
        password = self.password
        from_address = self.from_address
        use_tls = self.use_tls

        if self.config_service:
            try:
                db_user = await self.config_service.get_config("SMTP_USERNAME")
                if db_user:
                    username = db_user

                db_pass = await self.config_service.get_config("SMTP_PASSWORD")
                if db_pass and str(db_pass).strip():
                    password = db_pass

                db_host = await self.config_service.get_config("SMTP_HOST")
                if db_host:
                    host = db_host

                db_port = await self.config_service.get_config("SMTP_PORT")
                if db_port:
                    port = int(db_port)

                db_from = await self.config_service.get_config("SMTP_FROM_ADDRESS")
                if db_from:
                    from_address = db_from

                db_tls = await self.config_service.get_config("SMTP_USE_TLS")
                if db_tls is not None:
                    use_tls = str(db_tls).lower() in ("true", "1", "yes")
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("smtp_dynamic_config_fetch_failed_using_defaults", error=str(e))

        return host, port, username, password, from_address, use_tls

    async def _send_email(self, to_email: str, subject: str, content: str) -> None:
        """Async function missing docstring."""
        host, port, username, password, from_address, use_tls = await self._get_smtp_credentials()

        message = EmailMessage()
        message["From"] = from_address
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(content, subtype="html")

        async def do_send() -> None:
            """Async function missing docstring."""
            await aiosmtplib.send(
                message,
                hostname=host,
                port=port,
                username=username if username else None,
                password=password if password else None,
                use_tls=use_tls,
            )

        try:
            await with_retry(
                operation=do_send,
                max_attempts=3,
                operation_name=f"smtp_send_{to_email}"
            )
            logger.info("email_sent", to_email=to_email, subject=subject)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "email_send_failed",
                to_email=to_email,
                error=str(e),
            )
            from benefit_iq.domain.exceptions.auth_exceptions import AuthDomainException
            raise AuthDomainException(
                f"Failed to send email to {to_email}. Ensure SMTP mail server configuration is valid. Error: {str(e)}"
            ) from e

    async def send_verification_email(self, to_email: str, token: str) -> None:
        # In a real app, this would use a Jinja template
        """Async function missing docstring."""
        link = f"http://localhost:4200/verify-email?token={token}"
        content = f"""
        <html>
            <body>
                <h1>Verify your email</h1>
                <p>Please click the link below to verify your email address:</p>
                <a href="{link}">Verify Email</a>
            </body>
        </html>
        """
        await self._send_email(to_email, "BenefitIQ - Verify Your Email", content)

    async def send_password_reset_email(self, to_email: str, token: str) -> None:
        """Async function missing docstring."""
        link = f"http://localhost:4200/reset-password?token={token}"
        content = f"""
        <html>
            <body>
                <h1>Reset your password</h1>
                <p>Please click the link below to reset your password:</p>
                <a href="{link}">Reset Password</a>
            </body>
        </html>
        """
        await self._send_email(to_email, "BenefitIQ - Password Reset", content)

    async def send_password_changed_notification(self, to_email: str) -> None:
        """Sends security alert notification when password is changed."""
        content = """
        <html>
            <body>
                <h1>Password Changed</h1>
                <p>Your password has been successfully changed.</p>
                <p>If you did not perform this action, please contact support immediately.</p>
            </body>
        </html>
        """
        await self._send_email(to_email, "BenefitIQ - Security Alert: Password Changed", content)

    async def send_otp_email(self, to_email: str, otp: str, purpose: str) -> None:
        """Sends a 2-Step OTP verification code to user's email."""
        title = "Registration Verification Code" if purpose == "registration" else "Login 2FA Security Code"
        content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Benefit IQ Security - {title}</h2>
                <p>Your 2-Step OTP verification code is:</p>
                <h1 style="background-color: #f4f4f4; padding: 10px; display: inline-block; letter-spacing: 4px;">{otp}</h1>
                <p>This code will expire in 10 minutes. Do not share this code with anyone.</p>
            </body>
        </html>
        """
        await self._send_email(to_email, f"BenefitIQ - {title}", content)

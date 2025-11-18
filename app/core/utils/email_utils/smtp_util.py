import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from loguru import logger
from typing import List, Union, Optional
from app.web.settings import settings
import os
from functools import lru_cache


class SmtpSender:
    """Encapsulates functions to send emails with SMTP."""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self._connection = None

    def _get_connection(self):
        """Get or create SMTP connection with connection pooling."""
        if self._connection is None:
            self._connection = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                self._connection.starttls()
            self._connection.login(self.username, self.password)
        return self._connection

    def _close_connection(self):
        """Close the SMTP connection."""
        if self._connection:
            try:
                self._connection.quit()
            except Exception:
                pass
            finally:
                self._connection = None

    def send_email(
        self,
        source: str,
        destination: Union[str, List[str]],
        subject: str,
        text: str = "",
        html: str = "",
    ) -> Optional[bool]:
        if isinstance(destination, str):
            destination = [destination]

        msg = MIMEMultipart("alternative")
        msg["From"] = source
        msg["To"] = ", ".join(destination)
        msg["Subject"] = subject
        if text:
            msg.attach(MIMEText(text, "plain"))
        if html:
            msg.attach(MIMEText(html, "html"))

        try:
            server = self._get_connection()
            server.sendmail(source, destination, msg.as_string())
            logger.info(f"Sent SMTP mail from {source} to {destination}.")
            return True
        except Exception as e:
            logger.error(f"Couldn't send SMTP mail from {source} to {destination}: {e}")
            self._close_connection()
            return None

    def __del__(self):
        """Cleanup connection on object destruction."""
        self._close_connection()


# Global SMTP sender instance for connection reuse
_smtp_sender_instance = None


def get_smtp_sender() -> SmtpSender:
    """Factory function to create an SmtpSender instance."""
    global _smtp_sender_instance
    if _smtp_sender_instance is None:
        _smtp_sender_instance = SmtpSender(
            smtp_server=settings.smtp_server,
            smtp_port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            use_tls=settings.smtp_use_tls,
        )
    return _smtp_sender_instance


@lru_cache(maxsize=2)
def _load_template(template_name: str) -> str:
    """Load and cache email templates."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", template_name)
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def send_reset_password_email(destination_email: str, reset_url: str):
    """Send password reset email."""
    # FIXED: Use single curly braces to match template
    html_content = _load_template("reset_password.html").replace(
        "{reset_url}", reset_url
    )
    subject = "Reset Your Password - Psychotherapy"

    smtp_sender = get_smtp_sender()
    smtp_sender.send_email(
        source=settings.smtp_username,
        destination=destination_email,
        subject=subject,
        text=f"Please use the following link to reset your password: {reset_url}",
        html=html_content,
    )
    logger.info(f"Password reset email sent to {destination_email}")


def send_verification_email(destination_email: str, verification_url: str):
    """Send email verification email."""
    # FIXED: Use single curly braces to match template
    html_content = _load_template("verify_email.html").replace(
        "{verification_url}", verification_url
    )
    subject = "Verify Your Email - Psychotherapy"

    smtp_sender = get_smtp_sender()
    smtp_sender.send_email(
        source=settings.smtp_username,
        destination=destination_email,
        subject=subject,
        text=f"Please use the following link to verify your email address: {verification_url}",
        html=html_content,
    )
    logger.info(f"Verification email sent to {destination_email}")

"""Email sending abstraction.

In production, set EMAIL_BACKEND="smtp" and configure SMTP_* env vars.
Defaults to a console/logging backend for development.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body_html: str) -> None:
    """Send an email using the configured backend.

    Falls back to logging in development / when SMTP is not configured.
    """
    backend = getattr(settings, "EMAIL_BACKEND", "console")

    if backend == "smtp":
        _send_smtp(to, subject, body_html)
    else:
        # Console / log backend — useful for dev & CI
        logger.info("[EMAIL → %s] Subject: %s\n%s", to, subject, body_html)


def _send_smtp(to: str, subject: str, body_html: str) -> None:
    """Send via SMTP (works with SendGrid, SES SMTP, Mailgun, etc.)."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, [to], msg.as_string())
        logger.info("Email sent to %s — subject: %s", to, subject)
    except Exception:
        logger.exception("Failed to send email to %s", to)
        raise

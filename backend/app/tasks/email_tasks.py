"""Email background tasks."""

import logging

from app.core.email import send_email
from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, email: str, full_name: str) -> None:  # noqa: ANN001
    """Send a welcome email after registration."""
    try:
        send_email(
            to=email,
            subject="Welcome to StayNest!",
            body_html=(
                f"<h1>Welcome, {full_name}!</h1>"
                "<p>Thank you for joining StayNest. Start exploring properties today.</p>"
            ),
        )
    except Exception as exc:
        logger.exception("Welcome email failed for %s", email)
        raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation(self, email: str, booking_id: str) -> None:  # noqa: ANN001
    """Send booking confirmation email."""
    try:
        send_email(
            to=email,
            subject="Booking Confirmed — StayNest",
            body_html=(
                f"<h1>Booking Confirmed</h1>"
                f"<p>Your booking <strong>{booking_id}</strong> has been received.</p>"
                "<p>The host will review and confirm shortly.</p>"
            ),
        )
    except Exception as exc:
        logger.exception("Booking confirmation email failed for %s", email)
        raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email(self, email: str, reset_token: str) -> None:  # noqa: ANN001
    """Send a password reset email with token link."""
    from app.config import settings

    reset_url = f"{settings.CORS_ORIGINS[0]}/auth/reset-password?token={reset_token}"
    try:
        send_email(
            to=email,
            subject="Reset Your Password — StayNest",
            body_html=(
                "<h1>Password Reset</h1>"
                f'<p>Click <a href="{reset_url}">here</a> to reset your password.</p>'
                "<p>This link expires in 30 minutes.</p>"
            ),
        )
    except Exception as exc:
        logger.exception("Password reset email failed for %s", email)
        raise self.retry(exc=exc) from exc

"""Membership renewal background tasks.

These tasks run synchronously inside the Celery worker and use
a *synchronous* SQLAlchemy engine (Celery does not support asyncio by default).
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings
from app.tasks import celery_app

logger = logging.getLogger(__name__)


def _sync_engine():
    """Create a synchronous engine from the async DATABASE_URL."""
    url = settings.DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", "")
    return create_engine(url)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def check_expiring_memberships(self) -> None:  # noqa: ANN001
    """Send renewal reminders for memberships expiring within 7 days.

    Scheduled daily via Celery Beat.
    """
    from app.core.email import send_email
    from app.models.membership import Membership, MembershipStatus
    from app.models.user import HostProfile, User

    try:
        engine = _sync_engine()
        with Session(engine) as session:
            threshold = datetime.now(UTC) + timedelta(days=7)
            stmt = (
                select(Membership, User.email, User.full_name)
                .join(HostProfile, HostProfile.id == Membership.host_id)
                .join(User, User.id == HostProfile.user_id)
                .where(
                    Membership.status == MembershipStatus.ACTIVE,
                    Membership.end_date <= threshold,
                    Membership.end_date > datetime.now(UTC),
                )
            )
            rows = session.execute(stmt).all()
            for membership, email, full_name in rows:
                send_email(
                    to=email,
                    subject="Your StayNest Membership is Expiring Soon",
                    body_html=(
                        f"<p>Hi {full_name},</p>"
                        f"<p>Your <strong>{membership.plan_type}</strong> membership "
                        f"expires on {membership.end_date.strftime('%Y-%m-%d')}.</p>"
                        "<p>Renew now to keep your listings active.</p>"
                    ),
                )
            logger.info("Checked expiring memberships — %d reminders sent", len(rows))
    except Exception as exc:
        logger.exception("check_expiring_memberships failed")
        raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def process_auto_renewals(self) -> None:  # noqa: ANN001
    """Process automatic membership renewals for expired memberships with auto_renew=True.

    Scheduled daily via Celery Beat.
    In a real system the payment charge would happen here; for now we
    extend the membership period and log the action.
    """
    from app.models.membership import PLAN_CONFIG, Membership, MembershipPlan, MembershipStatus

    try:
        engine = _sync_engine()
        with Session(engine) as session:
            now = datetime.now(UTC)
            stmt = select(Membership).where(
                Membership.status == MembershipStatus.ACTIVE,
                Membership.auto_renew.is_(True),
                Membership.end_date <= now,
            )
            expired = session.execute(stmt).scalars().all()
            renewed = 0
            for membership in expired:
                plan = PLAN_CONFIG.get(MembershipPlan(membership.plan_type))
                if plan is None:
                    continue
                # Extend by 30 days from current end_date
                membership.end_date = membership.end_date + timedelta(days=30)
                membership.amount = plan["price"]
                membership.updated_at = now
                renewed += 1
            session.commit()
            logger.info("Auto-renewed %d / %d expired memberships", renewed, len(expired))
    except Exception as exc:
        logger.exception("process_auto_renewals failed")
        raise self.retry(exc=exc) from exc

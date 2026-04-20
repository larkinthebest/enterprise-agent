"""Database initialisation helpers — seed default admin user."""

import secrets
import logging

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models.user import User, Role

logger = logging.getLogger(__name__)

DEFAULT_ADMIN_USERNAME = "admin"


def seed_default_admin(db: Session) -> None:
    """Create a default admin user if none exists."""
    existing = db.query(User).filter(User.role == Role.ADMIN).first()
    if existing:
        logger.info("Admin user already exists, skipping seed.")
        return

    api_key = secrets.token_hex(32)
    admin = User(
        username=DEFAULT_ADMIN_USERNAME,
        api_key=api_key,
        role=Role.ADMIN,
        full_name="System Administrator",
    )
    db.add(admin)
    db.commit()
    logger.info(
        "Default admin created",
        extra={"username": DEFAULT_ADMIN_USERNAME, "api_key": api_key},
    )


def init_db() -> None:
    """Run all DB seed steps."""
    db = SessionLocal()
    try:
        seed_default_admin(db)
    finally:
        db.close()

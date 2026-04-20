"""User model with RBAC role enum."""

import enum

from sqlalchemy import Column, String, Enum as SAEnum

from app.db.base import Base, TimestampMixin, GUID, new_uuid


class Role(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=new_uuid)
    username = Column(String(100), unique=True, nullable=False, index=True)
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    role = Column(SAEnum(Role), nullable=False, default=Role.VIEWER)
    full_name = Column(String(200), nullable=True)

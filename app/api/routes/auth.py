"""Auth routes — user management (admin only for create/list)."""

import secrets
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User, Role
from app.api.deps import CurrentUser, require_admin

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Schemas ──────────────────────────────────────────────────────────────
class CreateUserRequest(BaseModel):
    username: str
    role: Role = Role.VIEWER
    full_name: str | None = None


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    full_name: str | None
    api_key: str | None = None  # only shown on creation

    model_config = {"from_attributes": True}


class WhoAmIResponse(BaseModel):
    id: str
    username: str
    role: str
    full_name: str | None

    model_config = {"from_attributes": True}


# ── Endpoints ────────────────────────────────────────────────────────────
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    body: CreateUserRequest,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new user (admin only). Returns the generated API key."""
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already exists")

    api_key = secrets.token_hex(32)
    user = User(
        username=body.username,
        api_key=api_key,
        role=body.role,
        full_name=body.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("User created", extra={"username": body.username, "role": body.role.value})
    return UserResponse(
        id=str(user.id),
        username=user.username,
        role=user.role.value,
        full_name=user.full_name,
        api_key=api_key,
    )


@router.get("/users", response_model=list[UserResponse])
def list_users(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all users (admin only). API keys are hidden."""
    users = db.query(User).all()
    return [
        UserResponse(
            id=str(u.id),
            username=u.username,
            role=u.role.value,
            full_name=u.full_name,
        )
        for u in users
    ]


@router.get("/me", response_model=WhoAmIResponse)
def who_am_i(user: CurrentUser):
    """Return the identity of the caller based on their API key."""
    return WhoAmIResponse(
        id=str(user.id),
        username=user.username,
        role=user.role.value,
        full_name=user.full_name,
    )

"""API dependencies — RBAC enforcement via API-key header."""

import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User, Role

logger = logging.getLogger(__name__)


def _get_current_user(
    x_api_key: Annotated[str, Header()],
    db: Session = Depends(get_db),
) -> User:
    """Resolve user from X-Api-Key header."""
    user = db.query(User).filter(User.api_key == x_api_key).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return user


CurrentUser = Annotated[User, Depends(_get_current_user)]


class RequireRole:
    """Dependency that checks the caller has *at least* the required role."""

    HIERARCHY = {Role.VIEWER: 0, Role.OPERATOR: 1, Role.ADMIN: 2}

    def __init__(self, minimum: Role):
        self.minimum = minimum

    def __call__(self, user: CurrentUser) -> User:
        if self.HIERARCHY.get(user.role, 0) < self.HIERARCHY[self.minimum]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.value}' insufficient; need '{self.minimum.value}'",
            )
        return user


require_admin = RequireRole(Role.ADMIN)
require_operator = RequireRole(Role.OPERATOR)
require_viewer = RequireRole(Role.VIEWER)

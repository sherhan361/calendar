from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.responses import ApiException
from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db


bearer_scheme = HTTPBearer(auto_error=False)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiException(401, "unauthorized", "Bearer token is required.")
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise ApiException(401, "unauthorized", "Invalid token.")
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise ApiException(401, "unauthorized", "Invalid token.")
    return user

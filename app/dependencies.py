import json
import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token

DbSession = Annotated[Session, Depends(get_db)]


def normalize_token(value: str) -> str:
    if value.lower().startswith("bearer "):
        return value[7:]
    try:
        decoded = json.loads(value)
        return decoded if isinstance(decoded, str) else value
    except json.JSONDecodeError:
        return value


def optional_user(
    db: DbSession, authorization: Annotated[str | None, Header()] = None
) -> User | None:
    if not authorization:
        return None
    try:
        payload = decode_access_token(normalize_token(authorization))
        return db.get(User, uuid.UUID(payload["sub"]))
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        return None


def current_user(user: Annotated[User | None, Depends(optional_user)]) -> User:
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token not verified")
    return user


def admin_user(user: Annotated[User, Depends(current_user)]) -> User:
    if not user.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator access required")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
AdminUser = Annotated[User, Depends(admin_user)]
OptionalUser = Annotated[User | None, Depends(optional_user)]

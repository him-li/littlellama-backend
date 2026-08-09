from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import get_settings

argon2 = PasswordHasher()


def hash_password(password: str) -> str:
    return argon2.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    if encoded.startswith("$2"):
        return bcrypt.checkpw(password.encode(), encoded.encode())
    try:
        return argon2.verify(encoded, password)
    except VerifyMismatchError:
        return False


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])

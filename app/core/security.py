from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

PASSWORD_SPECIAL = set("@#!$%^&*()-_=+[]{}|;:,.<>?")


def hash_secret(value: str) -> str:
    return pwd_context.hash(value)


def verify_secret(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def validate_password_rules(password: str) -> str | None:
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if " " in password:
        return "Password must not contain spaces"
    if not any(c.isupper() for c in password):
        return "Password must include at least one uppercase letter"
    if not any(c.isdigit() for c in password):
        return "Password must include at least one number"
    if not any(c in PASSWORD_SPECIAL for c in password):
        return "Password must include at least one allowed special character"
    for c in password:
        if not (c.isalnum() or c in PASSWORD_SPECIAL):
            return "Password contains a disallowed character"
    return None


def create_token(subject: str, token_type: str, expires_delta: timedelta, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "exp": datetime.now(UTC) + expires_delta,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def create_access_token(subject: str, role: str, tier: str | None = None) -> str:
    settings = get_settings()
    return create_token(
        subject,
        "access",
        timedelta(minutes=settings.jwt_access_minutes),
        {"role": role, "tier": tier},
    )


def create_refresh_token(subject: str) -> str:
    settings = get_settings()
    return create_token(subject, "refresh", timedelta(days=settings.jwt_refresh_days))


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


def safe_decode(token: str) -> dict[str, Any] | None:
    try:
        return decode_token(token)
    except JWTError:
        return None

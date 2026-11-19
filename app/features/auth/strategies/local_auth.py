from sqlalchemy.orm import Session

from app.core.security import hash_secret, verify_secret
from app.features.auth.data.models import Profile


class LocalAuthStrategy:
    """Email auth against profiles.password_hash (AUTH_PROVIDER=local)."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def register_email(self, email: str, password: str) -> str:
        existing = self._db.query(Profile).filter(Profile.email == email.lower()).first()
        if existing:
            raise ValueError("Email already used")
        profile = Profile(
            email=email.lower(),
            password_hash=hash_secret(password),
            role="customer",
            tier="silver",
        )
        self._db.add(profile)
        self._db.commit()
        self._db.refresh(profile)
        return profile.id

    def login_email(self, email: str, password: str) -> str:
        profile = self._db.query(Profile).filter(Profile.email == email.lower()).first()
        if not profile or not profile.password_hash:
            raise ValueError("Invalid credentials")
        if not verify_secret(password, profile.password_hash):
            raise ValueError("Invalid credentials")
        return profile.id

    def request_password_reset(self, email: str) -> None:
        # Stub: real email send later; no user enumeration
        _ = email
        return None

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import safe_decode
from app.features.auth.data.models import Profile
from app.features.auth.domain.use_cases import AuthUseCases
from app.features.auth.strategies.local_auth import LocalAuthStrategy
from app.features.auth.strategies.supabase_auth import SupabaseAuthStrategy

bearer = HTTPBearer(auto_error=False)


def get_auth_use_cases(db: Session = Depends(get_db)) -> AuthUseCases:
    settings = get_settings()
    if settings.auth_provider == "supabase":
        strategy = SupabaseAuthStrategy()
    else:
        strategy = LocalAuthStrategy(db)
    return AuthUseCases(db, strategy)


def get_current_profile(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Profile:
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = safe_decode(creds.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    profile = db.query(Profile).filter(Profile.id == payload["sub"]).first()
    if not profile or profile.is_blocked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return profile

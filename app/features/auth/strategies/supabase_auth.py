"""Supabase AuthStrategy — used when AUTH_PROVIDER=supabase and keys are set."""

import httpx

from app.core.config import get_settings


class SupabaseAuthStrategy:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.supabase_url or not (
            settings.supabase_service_role_key or settings.supabase_key
        ):
            raise RuntimeError("Supabase credentials missing. Fill env-profiles and set AUTH_PROVIDER=supabase.")
        self._base = settings.supabase_url.rstrip("/")
        self._key = settings.supabase_service_role_key or settings.supabase_key

    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        }

    def register_email(self, email: str, password: str) -> str:
        with httpx.Client(timeout=30) as client:
            res = client.post(
                f"{self._base}/auth/v1/signup",
                headers=self._headers(),
                json={"email": email, "password": password},
            )
            if res.status_code >= 400:
                raise ValueError(res.json().get("msg") or res.json().get("error_description") or "Register failed")
            data = res.json()
            user = data.get("user") or data
            uid = user.get("id")
            if not uid:
                raise ValueError("Supabase did not return user id")
            return str(uid)

    def login_email(self, email: str, password: str) -> str:
        with httpx.Client(timeout=30) as client:
            res = client.post(
                f"{self._base}/auth/v1/token?grant_type=password",
                headers=self._headers(),
                json={"email": email, "password": password},
            )
            if res.status_code >= 400:
                raise ValueError("Invalid credentials")
            data = res.json()
            user = data.get("user") or {}
            uid = user.get("id")
            if not uid:
                raise ValueError("Invalid credentials")
            return str(uid)

    def request_password_reset(self, email: str) -> None:
        with httpx.Client(timeout=30) as client:
            client.post(
                f"{self._base}/auth/v1/recover",
                headers=self._headers(),
                json={"email": email},
            )

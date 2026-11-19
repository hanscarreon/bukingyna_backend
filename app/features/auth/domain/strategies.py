from typing import Protocol


class AuthStrategy(Protocol):
    """Swappable auth provider (local DEV store or Supabase)."""

    def register_email(self, email: str, password: str) -> str:
        """Return provider user id."""
        ...

    def login_email(self, email: str, password: str) -> str:
        """Return provider user id or raise ValueError."""
        ...

    def request_password_reset(self, email: str) -> None: ...

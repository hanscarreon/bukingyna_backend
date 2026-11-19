"""Supabase-backed health check stub."""


class SupabaseHealthRepository:
    """Placeholder adapter. Wire supabase-py when a real project exists."""

    async def ping(self) -> bool:
        # Starter: no network call yet. Treat as "not configured".
        return False

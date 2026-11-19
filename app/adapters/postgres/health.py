"""PostgreSQL-backed health check stub."""


class PostgresHealthRepository:
    """Placeholder adapter. Wire asyncpg/SQLAlchemy when DATABASE_URL is live."""

    async def ping(self) -> bool:
        return False

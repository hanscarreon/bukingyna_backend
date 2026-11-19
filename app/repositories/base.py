"""Repository protocol stubs — swap adapters without changing routers."""

from typing import Protocol


class HealthRepository(Protocol):
    """Example seam: health/readiness backed by whatever data adapter is configured."""

    async def ping(self) -> bool:
        """Return True when the data store is reachable."""
        ...

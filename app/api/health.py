from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe — no DB dependency in the starter."""
    return {"status": "ok", "service": "booking-yna-api"}

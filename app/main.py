from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.db import SessionLocal, init_db
from app.features.auth.api.router import router as auth_router
from app.features.auth.domain.use_cases import seed_superadmin


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_superadmin(db)
    finally:
        db.close()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Booking Yna API — auth + health. Export OpenAPI to contracts/ when stable.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Booking Yna API", "env": settings.app_env, "auth_provider": settings.auth_provider}

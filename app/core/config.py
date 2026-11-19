from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Booking Yna API"
    app_env: str = "dev"
    auth_provider: str = "local"  # local | supabase

    jwt_secret: str = "dev-change-me"
    jwt_access_minutes: int = 30
    jwt_refresh_days: int = 14

    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: str = ""

    database_url: str = "sqlite:///./data/bookingyna_dev.db"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    seed_superadmin_email: str = "superadmin@example.com"
    seed_superadmin_password: str = "Admin@12345"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_dev(self) -> bool:
        # local + dev both expose DEV helpers (e.g. OTP in API response)
        return self.app_env.lower() in ("dev", "local")


@lru_cache
def get_settings() -> Settings:
    return Settings()

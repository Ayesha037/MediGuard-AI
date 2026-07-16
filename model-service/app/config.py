"""
Configuration for the MediGuard AI Prediction Service.

All settings are environment-driven so the exact same Docker image works
across dev / staging / production — nothing environment-specific is baked
into the image itself, which is what any cloud platform (Render, Railway,
ECS, Cloud Run, Azure Container Apps) expects.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVICE_NAME: str = "MediGuard AI Prediction Service"
    ENVIRONMENT: str = "production"

    # API key(s) allowed to call protected endpoints. Comma-separated list
    # so keys can be rotated (add new, remove old) without downtime.
    API_KEYS: str = "changeme-generate-a-real-key"

    # CORS — restrict to your actual frontend/hospital-system origins in prod.
    CORS_ORIGINS: str = "*"

    # Rate limiting (requests per minute per API key)
    RATE_LIMIT_PER_MINUTE: int = 120

    # Model artifacts
    ARTIFACT_DIR: str = "app/artifacts"

    # Risk thresholds — must match whatever the model was trained/calibrated against
    FAILURE_PROB_HIGH_THRESHOLD: float = 0.70
    FAILURE_PROB_MEDIUM_THRESHOLD: float = 0.35

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def api_key_set(self) -> set[str]:
        return {k.strip() for k in self.API_KEYS.split(",") if k.strip()}

    @property
    def cors_origin_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

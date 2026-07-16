from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "MediGuard AI"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    POSTGRES_USER: str = "mediguard"
    POSTGRES_PASSWORD: str = "mediguard_dev_password"
    POSTGRES_DB: str = "mediguard"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    MODEL_ARTIFACT_DIR: str = "app/ml/artifacts"
    FAILURE_PROB_HIGH_THRESHOLD: float = 0.70
    FAILURE_PROB_MEDIUM_THRESHOLD: float = 0.35

    SIMULATOR_TICK_SECONDS: float = 3.0
    SIMULATOR_ENABLED: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
settings = get_settings()

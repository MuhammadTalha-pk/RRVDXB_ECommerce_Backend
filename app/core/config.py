from typing import Optional

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    PROJECT_NAME: str = "RRVDXB API"
    DATABASE_URL: str
    SECRET_KEY: str

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    STRIPE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@rrvdxb.com"

    # --- AI Product Recommender (Ubaid Ullah Farooqui) ---
    RECOMMENDER_DEFAULT_LIMIT: int = 5
    RECOMMENDER_MAX_LIMIT: int = 20
    RECOMMENDER_CACHE_TTL_SECONDS: int = 300
    TRENDING_WINDOW_DAYS: int = 7
    PRODUCT_ID_PREFIX: str = "P"
    PRODUCT_ID_PAD: int = 3
    USE_SYNTHETIC_FALLBACK: bool = True
    SYNTHETIC_DATASET_PATH: str = "data/synthetic_dataset.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
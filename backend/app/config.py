from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    secret_key: str = "examai-dev-secret-change-in-production"
    groq_api_key: str = ""
    database_url: str = "sqlite:///./examai.db"
    frontend_url: str = "http://localhost:3000"
    google_client_id: str = ""
    google_client_secret: str = ""
    access_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()

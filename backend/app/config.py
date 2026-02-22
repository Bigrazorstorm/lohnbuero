import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Lohnbüro Management System"
    secret_key: str = "aom-secret-key-change-in-production-2026"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours

    # Use local .env.local for development, fallback to .env or MySQL
    database_url: str = "sqlite:///./lohnbuero.db"  # Default to SQLite for local dev

    model_config = {
        "env_file": ".env.local" if os.path.exists(".env.local") else ".env"
    }


settings = Settings()

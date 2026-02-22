from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Addison Operations Manager"
    secret_key: str = "aom-secret-key-change-in-production-2026"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours

    database_url: str = "mysql+pymysql://lohnbuero:lohnbuero123@mysql:3306/lohnbuero"

    model_config = {"env_file": ".env"}


settings = Settings()

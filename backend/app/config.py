from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql+psycopg2://couple:couple@localhost:5432/couple_simulator"
    )
    api_prefix: str = "/api"
    environment: str = "development"


settings = Settings()

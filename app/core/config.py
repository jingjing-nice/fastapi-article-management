from functools import lru_cache

from pydantic import Field, SecretStr


from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    app_name: str = "Article Management API"
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_user: str = "articles_db"
    db_name: str = "article_management"
    db_password: str = ""
    sql_echo: bool = False
    log_level: str = "INFO"
    test_database_url: str | None = None

    jwt_secret_key: SecretStr
    jwt_access_token_expire_minutes: int = Field(default=30, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

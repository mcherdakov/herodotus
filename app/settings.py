from dataclasses import fields

from pydantic import BaseSettings, Field, PostgresDsn


class Settings(BaseSettings):
    auth_key: str = ""
    pg_dsn: str = ""
    jwt_alogrithm: str = "HS256"
    access_token_expires_minutes: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

        fields = {"auth_key": {"env": "AUTH_KEY"}, "pg_dsn": {"env": "POSTGRES_DSN"}}


settings = Settings()

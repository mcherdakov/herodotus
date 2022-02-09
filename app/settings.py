from dataclasses import fields

from pydantic import BaseSettings, Field, PostgresDsn


class Settings(BaseSettings):
    auth_key: str = ""
    pg_dsn: str = ""
    jwt_alogrithm: str = "HS256"
    access_token_expires_minutes: int = 30

    mail_username: str = ""
    mail_password: str = ""
    mail_port: int = 465
    mail_server: str = "smtp.yandex.ru"
    mail_tls: bool = False
    mail_ssl: bool = True
    mail_use_credentials: bool = True
    mail_validatae_certs: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

        fields = {
            "auth_key": {"env": "AUTH_KEY"},
            "pg_dsn": {"env": "POSTGRES_DSN"},
            "mail_username": {"env": "MAIL_USERNAME"},
            "mail_password": {"env": "MAIL_PASSWORD"},
        }


settings = Settings()

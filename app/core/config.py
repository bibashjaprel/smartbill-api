import os
from typing import List, Optional
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise ValueError(f"Missing required environment variable: {name}")
    return value


class Settings:
    def __init__(self) -> None:
        self.PROJECT_NAME: str = os.getenv("PROJECT_NAME", "BillSmart API")
        self.VERSION: str = os.getenv("VERSION", "1.0.0")
        self.API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")

        cors_origins_raw = os.getenv(
            "BACKEND_CORS_ORIGINS",
            "http://localhost:3000,http://localhost:3001,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,https://billsmart.app,*",
        )
        self.BACKEND_CORS_ORIGINS: List[str] = [
            origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()
        ]

        self.POSTGRES_USER: str = _require_env("POSTGRES_USER")
        self.POSTGRES_PASSWORD: str = _require_env("POSTGRES_PASSWORD")
        self.POSTGRES_HOST: str = _require_env("POSTGRES_HOST")
        self.POSTGRES_PORT: int = int(_require_env("POSTGRES_PORT"))
        self.POSTGRES_DB: str = _require_env("POSTGRES_DB")

        password_escaped = quote_plus(self.POSTGRES_PASSWORD)
        self.DATABASE_URL: str = (
            f"postgresql://{self.POSTGRES_USER}:{password_escaped}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

        self.SECRET_KEY: str = _require_env("SECRET_KEY")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

        self.GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
        self.GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")

        self.SMTP_TLS: bool = os.getenv("SMTP_TLS", "true").lower() in {"1", "true", "yes", "on"}
        self.SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
        self.SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
        self.SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
        self.SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
        self.EMAILS_FROM_EMAIL: Optional[str] = os.getenv("EMAILS_FROM_EMAIL")
        self.EMAILS_FROM_NAME: Optional[str] = os.getenv("EMAILS_FROM_NAME")

        self.FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = int(
            os.getenv("EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS", "24")
        )
        self.PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = int(
            os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_HOURS", "2")
        )
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"}
        self.AUTO_INIT_DB: bool = os.getenv("AUTO_INIT_DB", "false").lower() in {"1", "true", "yes", "on"}

    def masked_database_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:***"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()

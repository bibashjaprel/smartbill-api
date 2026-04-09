from typing import List, Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    PROJECT_NAME: str = "BillSmart API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # Allow all origins for development
    
    # Database
    POSTGRES_USER: str = Field(default="postgres", validation_alias="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="root", validation_alias="POSTGRES_PASSWORD")
    POSTGRES_HOST: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    POSTGRES_DB: str = Field(default="postgres", validation_alias="POSTGRES_DB")
    DATABASE_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # Email settings
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Frontend URL for email verification links
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Email verification
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    
    # Password reset
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 2
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://billsmart.app",   # Add your production domains here
        "*"  # Allow all origins in development (remove in production)
    ]
    
    # Development
    DEBUG: bool = False

    @model_validator(mode="after")
    def build_database_url(self):
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self


settings = Settings()

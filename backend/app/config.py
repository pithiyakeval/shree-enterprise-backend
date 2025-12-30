from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, field_validator
from typing import List, Optional


class Settings(BaseSettings):
    # =============================
    # DATABASE
    # =============================
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # =============================
    # SECURITY
    # =============================
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # =============================
    # ADMIN
    # =============================
    ADMIN_EMAIL: EmailStr
    ADMIN_PASSWORD: str

    # =============================
    # EMAIL
    # =============================
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: Optional[EmailStr] = None
    OWNER_EMAILS: Optional[str] = None

    # =============================
    # FRONTEND
    # =============================
    FRONTEND_URL: str = "http://localhost:3000"

    # =============================
    # ENVIRONMENT
    # =============================
    ENVIRONMENT: str = "production"  # dev | production
    ENABLE_DOCS: bool = False        # 🔥 FIXED

    # =============================
    # AI (OPTIONAL ON FREE TIER)
    # =============================
    MODEL_PATH: Optional[str] = None
    LLAMA_CTX: int = 2048

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    def owner_email_list(self) -> List[str]:
        if not self.OWNER_EMAILS:
            return []
        return [e.strip() for e in self.OWNER_EMAILS.split(",") if e.strip()]

    @field_validator("*", mode="before")
    def strip_spaces(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


settings = Settings()

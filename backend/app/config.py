from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, field_validator
from typing import List, Optional


class Settings(BaseSettings):

    # =====================================================
    # APP ENVIRONMENT
    # =====================================================

    ENVIRONMENT:str="production"

    DEBUG:bool=False

    ENABLE_DOCS:bool=False

    LOG_LEVEL:str="INFO"

    APP_NAME:str="Shree Enterprise API"

    API_V1_PREFIX:str="/api"


    # =====================================================
    # DATABASE
    # =====================================================

    DATABASE_URL:str

    DATABASE_URL_SYNC:str

    DB_POOL_SIZE:int=10

    DB_MAX_OVERFLOW:int=20


    # =====================================================
    # SECURITY
    # =====================================================

    SECRET_KEY:str

    ALGORITHM:str="HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES:int=1440

    PASSWORD_MIN_LENGTH:int=6


    # =====================================================
    # ADMIN
    # =====================================================

    ADMIN_EMAIL:Optional[EmailStr]=None

    ADMIN_PASSWORD:Optional[str]=None


    # =====================================================
    # FRONTEND
    # =====================================================

    FRONTEND_URL:str

    ADDITIONAL_ORIGINS:Optional[str]=None


    # =====================================================
    # EMAIL
    # =====================================================

    SMTP_HOST:Optional[str]=None

    SMTP_PORT:Optional[int]=None

    SMTP_USER:Optional[str]=None

    SMTP_PASSWORD:Optional[str]=None

    FROM_EMAIL:Optional[EmailStr]=None

    OWNER_EMAILS:Optional[str]=None


    # =====================================================
    # AI SETTINGS
    # =====================================================

    GROQ_API_KEY:str

    LLM_TIMEOUT:int=30

    MAX_AI_RETRIES:int=2


    # =====================================================
    # VECTOR DATABASE
    # =====================================================

    QDRANT_URL:str

    QDRANT_API_KEY:Optional[str]=None

    QDRANT_COLLECTION:str="shree_docs"

    VECTOR_TOP_K:int=5


    # =====================================================
    # EMBEDDINGS
    # =====================================================

    EMBEDDING_MODEL:str="sentence-transformers/all-MiniLM-L6-v2"

    EMBEDDING_DEVICE:str="cpu"

    HF_CACHE_DIR:str="./hf-cache"


    # =====================================================
    # PERFORMANCE
    # =====================================================

    CACHE_TTL:int=300

    MAX_HISTORY:int=50

    MAX_CONTEXT:int=1500

    REQUEST_TIMEOUT:int=30


    # =====================================================
    # RATE LIMITING (future ready)
    # =====================================================

    RATE_LIMIT_ENABLED:bool=False

    RATE_LIMIT:str="100/minute"


    # =====================================================
    # HEALTH CHECK
    # =====================================================

    HEALTH_PATH:str="/health"


    # =====================================================
    # Pydantic config
    # =====================================================

    model_config = SettingsConfigDict(

        env_file="../.env",

        extra="ignore",

        case_sensitive=False

    )


    # =====================================================
    # HELPERS
    # =====================================================

    def owner_email_list(self)->List[str]:

        if not self.OWNER_EMAILS:

            return []

        return [

            e.strip()

            for e in self.OWNER_EMAILS.split(",")

            if e.strip()

        ]


    def cors_origins(self)->List[str]:

        origins=[

            self.FRONTEND_URL,

            "https://shreeenterprise.live",

            "https://www.shreeenterprise.live",

            "http://localhost:5173",

            "http://localhost:8080",

            "http://localhost:8081"

        ]

        if self.ADDITIONAL_ORIGINS:

            origins+=self.ADDITIONAL_ORIGINS.split(",")

        return list(set(origins))


    @field_validator("*",mode="before")

    def strip_spaces(cls,v):

        if isinstance(v,str):

            return v.strip()

        return v


settings=Settings()
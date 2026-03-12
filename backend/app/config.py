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


    # =====================================================
    # DATABASE
    # =====================================================

    DATABASE_URL:str

    DATABASE_URL_SYNC:str


    # =====================================================
    # SECURITY
    # =====================================================

    SECRET_KEY:str

    ALGORITHM:str="HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES:int=1440


    # =====================================================
    # ADMIN
    # =====================================================

    ADMIN_EMAIL:Optional[EmailStr]=None

    ADMIN_PASSWORD:Optional[str]=None


    # =====================================================
    # FRONTEND
    # =====================================================

    FRONTEND_URL:str


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

    LLM_TIMEOUT:int=20


    # =====================================================
    # VECTOR DATABASE
    # =====================================================

    QDRANT_URL:str

    QDRANT_API_KEY:Optional[str]=None

    QDRANT_COLLECTION:str="shree_docs"


    # =====================================================
    # EMBEDDINGS
    # =====================================================

    EMBEDDING_MODEL:str="BAAI/bge-small-en-v1.5"

    EMBEDDING_DEVICE:str="cpu"

    HF_CACHE_DIR:str="./hf-cache"


    # =====================================================
    # PERFORMANCE
    # =====================================================

    CACHE_TTL:int=300

    MAX_HISTORY:int=50

    MAX_CONTEXT:int=1500


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


    @field_validator("*",mode="before")

    def strip_spaces(cls,v):

        if isinstance(v,str):

            return v.strip()

        return v


settings=Settings()
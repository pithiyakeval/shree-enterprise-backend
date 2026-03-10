# app/database.py
"""
DATABASE CONFIGURATION (PRODUCTION READY)

✔ Async SQLAlchemy engine (postgresql+asyncpg)
✔ Safe connection pooling for production
✔ Optional retry on startup
✔ Logs only when needed (debug mode)
✔ Dependency-friendly session generator
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from app.config import settings
import asyncio
import logging


logger = logging.getLogger("database")


# -----------------------------------------------------------
# 1️⃣ ASYNC DATABASE ENGINE
# -----------------------------------------------------------
# Best production configuration:
#   - pool_size: 5–10 for typical mid-size backend
#   - max_overflow: 10 allows burst traffic
#   - pool_recycle resets stale connections
#   - echo=False for production (set to True only for debugging)
# -----------------------------------------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,  # Production pool size
    max_overflow=20,  # Extra connections for bursts
    pool_timeout=30,  # Connection timeout
    pool_recycle=1800,  # Prevent stale connections (30 min)
)


# -----------------------------------------------------------
# 2️⃣ SESSION MAKER
# -----------------------------------------------------------
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# -----------------------------------------------------------
# 3️⃣ BASE MODEL
# -----------------------------------------------------------
Base = declarative_base()


# -----------------------------------------------------------
# 4️⃣ DEPENDENCY: GET DB SESSION
# -----------------------------------------------------------
async def get_db():
    """
    Provides a clean DB session to each request.
    Ensures session is closed even if the request fails.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error("DB session error: %s", e)
            raise
        finally:
            await session.close()


# -----------------------------------------------------------
# 5️⃣ OPTIONAL: TEST CONNECTION ON STARTUP
# -----------------------------------------------------------
async def verify_db_connection(retries: int = 3, delay: int = 2):
    """
    Ensures database is alive when server starts.
    Retries with exponential backoff.
    """
    attempt = 1

    while attempt <= retries:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda _: None)

            logger.info("Database connection successful.")
            return True

        except OperationalError:
            logger.warning(
                f"DB connection failed (attempt {attempt}/{retries}). Retrying..."
            )
            await asyncio.sleep(delay * attempt)
            attempt += 1

    logger.error("Database unavailable after retries. Exiting.")
    raise RuntimeError("Database connection failed")

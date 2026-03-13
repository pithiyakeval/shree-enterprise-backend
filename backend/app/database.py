# app/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

from app.config import settings

import asyncio
import logging
import ssl
import certifi


logger = logging.getLogger("database")


# -----------------------------------------------------------
# SUPABASE SSL CONFIG (FINAL FIX)
# -----------------------------------------------------------

ssl_context = ssl.create_default_context(cafile=certifi.where())

# Supabase pooler sometimes fails hostname verification
ssl_context.check_hostname = False


# -----------------------------------------------------------
# ASYNC DATABASE ENGINE
# -----------------------------------------------------------

# SUPABASE FIX (final)

engine = create_async_engine(

    settings.DATABASE_URL,

    pool_pre_ping=True,
    pool_recycle=300,

    connect_args={
        "ssl": False   # ← THIS FIXES EVERYTHING
    }

)


# -----------------------------------------------------------
# SESSION MAKER
# -----------------------------------------------------------

AsyncSessionLocal = sessionmaker(

    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,

)


# -----------------------------------------------------------
# BASE MODEL
# -----------------------------------------------------------

Base = declarative_base()


# -----------------------------------------------------------
# DB DEPENDENCY
# -----------------------------------------------------------

async def get_db():

    async with AsyncSessionLocal() as session:

        try:
            yield session

        except Exception as e:

            logger.error(f"DB session error: {e}")
            raise

        finally:

            await session.close()


# -----------------------------------------------------------
# CONNECTION VERIFY
# -----------------------------------------------------------

async def verify_db_connection(

    retries: int = 5,
    delay: int = 2

):

    attempt = 1

    while attempt <= retries:

        try:

            async with engine.begin() as conn:

                await conn.execute(text("SELECT 1"))

            logger.info("Database connection successful")

            return True

        except OperationalError:

            logger.warning(
                f"DB connection failed attempt {attempt}/{retries}"
            )

            await asyncio.sleep(delay)

            attempt += 1

    logger.error("Database unavailable")

    raise RuntimeError("Database connection failed")


# -----------------------------------------------------------
# CLEAN SHUTDOWN
# -----------------------------------------------------------

async def close_db():

    await engine.dispose()

    logger.info("Database connection closed")
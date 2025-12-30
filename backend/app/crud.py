# app/crud.py
"""
CRUD OPERATIONS — PRODUCTION READY

✔ Clean separation of DB logic
✔ Lead creation with strict validation
✔ Admin authentication with secure hashing
✔ Safe query execution & logging
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app import models, schemas
from app.utils import verify_password, get_password_hash

import logging

logger = logging.getLogger("crud")


# ============================================================
# LEAD CREATION
# ============================================================

async def create_lead_with_service(db: AsyncSession, lead_in: schemas.BaseLeadCreate):
    """
    Creates a base lead + service-specific child table.
    Safe for production.
    """
    try:
        d = lead_in.dict()

        # 1️⃣ Create Base Lead
        base = models.BaseLead(
            name=d["name"],
            phone=d["phone"],
            email=d.get("email"),
            city=d["city"],
            message=d["message"],
            service=d["service"].lower(),
            where_from=d["where_from"],
            kw=d.get("kw"),
            budget=d.get("budget"),
            event_type=d.get("event_type"),
            event_date=d.get("event_date"),
        )

        db.add(base)
        await db.flush()  # gives us base.id

        service = d["service"].lower()

        # -----------------------
        # 2️⃣ Insert into Service Tables
        # -----------------------

        if service == "solar":
            db.add(models.SolarRequest(
                lead_id=base.id,
                kw=d.get("kw"),
                budget=d.get("budget")
            ))

        elif service == "mandap":
            db.add(models.MandapRequest(
                lead_id=base.id,
                event_type=d.get("event_type"),
                budget=d.get("budget"),
                event_date=d.get("event_date")
            ))

        elif service == "both":
            db.add(models.CombinedRequest(
                lead_id=base.id,
                kw=d.get("kw"),
                solar_budget=d.get("budget"),
                event_type=d.get("event_type"),
                mandap_budget=d.get("budget"),
                event_date=d.get("event_date")
            ))

        else:
            logger.error(f"Unknown service type received: {service}")
            raise ValueError("Invalid service type")

        await db.commit()
        await db.refresh(base)

        logger.info(f"Lead created (ID {base.id}, Service: {service})")

        return base

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("DB Error in create_lead_with_service: %s", e)
        raise

    except Exception as e:
        logger.error("Unexpected Error in create_lead_with_service: %s", e)
        raise


# ============================================================
# ADMIN GETTERS
# ============================================================

async def get_all_base_leads(db: AsyncSession, limit: int = 200):
    q = await db.execute(
        select(models.BaseLead)
        .order_by(models.BaseLead.created_at.desc())
        .limit(limit)
    )
    return q.scalars().all()


async def get_solar_requests(db: AsyncSession, limit: int = 200):
    q = await db.execute(
        select(models.SolarRequest, models.BaseLead)
        .join(models.BaseLead, models.SolarRequest.lead_id == models.BaseLead.id)
        .order_by(models.BaseLead.created_at.desc())
        .limit(limit)
    )
    return q.all()


async def get_mandap_requests(db: AsyncSession, limit: int = 200):
    q = await db.execute(
        select(models.MandapRequest, models.BaseLead)
        .join(models.BaseLead, models.MandapRequest.lead_id == models.BaseLead.id)
        .order_by(models.BaseLead.created_at.desc())
        .limit(limit)
    )
    return q.all()


async def get_combined_requests(db: AsyncSession, limit: int = 200):
    q = await db.execute(
        select(models.CombinedRequest, models.BaseLead)
        .join(models.BaseLead, models.CombinedRequest.lead_id == models.BaseLead.id)
        .order_by(models.BaseLead.created_at.desc())
        .limit(limit)
    )
    return q.all()


# ============================================================
# ADMIN AUTH MANAGEMENT
# ============================================================

async def create_admin(db: AsyncSession, email: str, password: str):
    """
    Create a secure admin using Argon2 hashing.
    """
    hashed = get_password_hash(password)
    admin = models.AdminUser(email=email, password_hash=hashed)

    db.add(admin)
    await db.commit()
    await db.refresh(admin)

    logger.info(f"Admin created: {email}")

    return admin


async def get_admin_by_email(db: AsyncSession, email: str):
    q = await db.execute(
        select(models.AdminUser).where(models.AdminUser.email == email)
    )
    return q.scalar_one_or_none()


async def authenticate_admin(db: AsyncSession, email: str, password: str):
    """
    Production-ready login:
    - Checks email exists
    - Uses Argon2 verify
    - Returns admin model or None
    """
    admin = await get_admin_by_email(db, email)
    if not admin:
        logger.warning(f"Login failed: No admin with email {email}")
        return None

    if not verify_password(password, admin.password_hash):
        logger.warning(f"Login failed: Wrong password for {email}")
        return None

    logger.info(f"Admin logged in: {email}")
    return admin

# app/routers/admin.py
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from jose import JWTError

from app import models
from app.database import get_db
from app.schemas import AdminLogin, AdminLoginResponse
from app.utils import (
    create_access_token,
    decode_token,
    get_password_hash,
)
from app.crud import (
    authenticate_admin,
    create_admin,
    get_admin_by_email,
)
from app.config import settings

logger = logging.getLogger("shree_backend.admin")

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Correct OAuth2 token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")


# ============================================================
# HELPER: Get current admin from token
# ============================================================
async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> models.AdminUser:

    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    admin_id = payload.get("sub")
    if not admin_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    admin = await db.get(models.AdminUser, int(admin_id))
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")

    return admin


# ============================================================
# LOGIN
# ============================================================
@router.post("/login", response_model=AdminLoginResponse)
async def login(payload: AdminLogin, db: AsyncSession = Depends(get_db)):

    admin = await authenticate_admin(db, payload.email, payload.password)
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(admin.id)})
    logger.info(f"Admin logged in: {admin.email}")

    return {"access_token": token, "token_type": "bearer"}


# ============================================================
# REGISTER FIRST ADMIN (only when DB empty)
# ============================================================
@router.post("/register-first", response_model=AdminLoginResponse)
async def register_first_admin(payload: AdminLogin, db: AsyncSession = Depends(get_db)):

    # check if admins exist
    count_query = await db.execute(select(func.count()).select_from(models.AdminUser))
    total_admins = count_query.scalar_one()

    if total_admins > 0:
        raise HTTPException(
            status_code=403,
            detail="First admin already exists. Use /api/admin/register (protected)."
        )

    admin = await create_admin(db, payload.email, payload.password)
    token = create_access_token({"sub": str(admin.id)})

    logger.info(f"First admin created: {admin.email}")

    return {"access_token": token, "token_type": "bearer"}


# ============================================================
# REGISTER MORE ADMINS (Admin-only)
# ============================================================
@router.post("/register", response_model=AdminLoginResponse)
async def register_admin(
    payload: AdminLogin,
    current_admin: models.AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):

    exists = await get_admin_by_email(db, payload.email)
    if exists:
        raise HTTPException(status_code=400, detail="Admin already exists")

    admin = await create_admin(db, payload.email, payload.password)
    token = create_access_token({"sub": str(admin.id)})

    logger.info(f"New admin created: {admin.email} by {current_admin.email}")

    return {"access_token": token, "token_type": "bearer"}


# ============================================================
# LEAD DATA (PROTECTED)
# ============================================================
@router.get("/leads")
async def all_leads(
    db: AsyncSession = Depends(get_db),
    current_admin: models.AdminUser = Depends(get_current_admin)
):
    from app.crud import get_all_base_leads
    return await get_all_base_leads(db)


@router.get("/solar")
async def solar_list(
    db: AsyncSession = Depends(get_db),
    current_admin: models.AdminUser = Depends(get_current_admin)
):
    from app.crud import get_solar_requests
    rows = await get_solar_requests(db)
    return [{"solar": s, "base": b} for s, b in rows]


@router.get("/mandap")
async def mandap_list(
    db: AsyncSession = Depends(get_db),
    current_admin: models.AdminUser = Depends(get_current_admin)
):
    from app.crud import get_mandap_requests
    rows = await get_mandap_requests(db)
    return [{"mandap": m, "base": b} for m, b in rows]


@router.get("/combined")
async def combined_list(
    db: AsyncSession = Depends(get_db),
    current_admin: models.AdminUser = Depends(get_current_admin)
):
    from app.crud import get_combined_requests
    rows = await get_combined_requests(db)
    return [{"combined": c, "base": b} for c, b in rows]


# ============================================================
# MARK LEAD DONE
# ============================================================
@router.post("/lead/{lead_id}/done")
async def mark_done(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: models.AdminUser = Depends(get_current_admin)
):
    lead = await db.get(models.BaseLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.status = "done"
    await db.commit()

    logger.info(f"Lead {lead_id} marked done by {current_admin.email}")
    return {"success": True, "message": "Lead marked as done"}


# ============================================================
# DELETE LEAD
# ============================================================
@router.delete("/lead/{lead_id}")
async def delete_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: models.AdminUser = Depends(get_current_admin)
):
    lead = await db.get(models.BaseLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    await db.delete(lead)
    await db.commit()

    logger.info(f"Lead {lead_id} deleted by {current_admin.email}")
    return {"success": True, "message": "Lead deleted"}


# ============================================================
# ADMIN LIST (Protected)
# ============================================================
@router.get("/admins")
async def list_admins(
    current_admin: models.AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.AdminUser))
    admins = result.scalars().all()

    return [
        {"id": a.id, "email": a.email, "created_at": a.created_at}
        for a in admins
    ]


# ============================================================
# ADMIN PASSWORD RESET
# ============================================================
@router.post("/reset-password/{admin_id}")
async def reset_password(
    admin_id: int,
    payload: dict = Body(...),  # expects {"new_password": "..."}
    db: AsyncSession = Depends(get_db),
    current_admin: models.AdminUser = Depends(get_current_admin),
):

    new_password = payload.get("new_password")
    if not new_password or len(new_password) < 6:
        raise HTTPException(400, "new_password must be at least 6 characters")

    admin = await db.get(models.AdminUser, admin_id)
    if not admin:
        raise HTTPException(404, "Admin not found")

    admin.password_hash = get_password_hash(new_password)
    await db.commit()

    logger.info(f"Password reset for {admin.email} by {current_admin.email}")
    return {"success": True, "message": "Password reset successful"}

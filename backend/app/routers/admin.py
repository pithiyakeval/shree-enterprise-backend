# app/routers/admin.py

import logging

from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app import models
from app.database import get_db
from app.schemas import AdminLogin, AdminLoginResponse
from app.utils import create_access_token, decode_token, get_password_hash
from app.crud import authenticate_admin, create_admin, get_admin_by_email

logger = logging.getLogger("shree_backend.admin")

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/admin/login"
)

# ============================================================
# GET CURRENT ADMIN (SAFE)
# ============================================================

async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> models.AdminUser:

    try:

        if not token:
            raise HTTPException(401,"Missing token")

        payload = decode_token(token)

        if not payload:
            raise HTTPException(401,"Invalid token")

        admin_id = payload.get("sub")

        if not admin_id:
            raise HTTPException(401,"Invalid token")

        admin = await db.get(
            models.AdminUser,
            int(admin_id)
        )

        if not admin:
            raise HTTPException(401,"Admin not found")

        return admin

    except HTTPException:
        raise

    except Exception as e:

        logger.exception("Token validation failed")

        raise HTTPException(
            401,
            "Authentication failed"
        )


# ============================================================
# LOGIN (CRASH SAFE)
# ============================================================

@router.post("/login",response_model=AdminLoginResponse)
async def login(
    payload: AdminLogin,
    db: AsyncSession = Depends(get_db)
):

    try:

        logger.info(f"Login attempt → {payload.email}")

        admin = await authenticate_admin(
            db,
            payload.email,
            payload.password
        )

        if not admin:

            logger.warning("Invalid credentials")

            raise HTTPException(
                401,
                "Invalid email or password"
            )

        token=create_access_token(
            {"sub":str(admin.id)}
        )

        logger.info("Login success")

        return {
            "access_token":token,
            "token_type":"bearer"
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.exception("LOGIN CRASH")

        raise HTTPException(
            500,
            "Login failed"
        )


# ============================================================
# REGISTER FIRST ADMIN
# ============================================================

@router.post(
    "/register-first",
    response_model=AdminLoginResponse
)
async def register_first_admin(
    payload:AdminLogin,
    db:AsyncSession=Depends(get_db)
):

    try:

        result=await db.execute(
            select(func.count()).select_from(
                models.AdminUser
            )
        )

        total=result.scalar_one()

        if total>0:

            raise HTTPException(
                403,
                "First admin already exists"
            )

        admin=await create_admin(
            db,
            payload.email,
            payload.password
        )

        token=create_access_token(
            {"sub":str(admin.id)}
        )

        logger.info(
            f"First admin created → {admin.email}"
        )

        return {
            "access_token":token,
            "token_type":"bearer"
        }

    except HTTPException:
        raise

    except Exception:

        logger.exception("Admin register failed")

        raise HTTPException(
            500,
            "Admin creation failed"
        )


# ============================================================
# REGISTER MORE ADMINS
# ============================================================

@router.post(
    "/register",
    response_model=AdminLoginResponse
)
async def register_admin(

    payload:AdminLogin,

    current_admin:models.AdminUser=Depends(
        get_current_admin
    ),

    db:AsyncSession=Depends(get_db)
):

    try:

        exists=await get_admin_by_email(
            db,
            payload.email
        )

        if exists:

            raise HTTPException(
                400,
                "Admin already exists"
            )

        admin=await create_admin(
            db,
            payload.email,
            payload.password
        )

        token=create_access_token(
            {"sub":str(admin.id)}
        )

        return {
            "access_token":token,
            "token_type":"bearer"
        }

    except HTTPException:
        raise

    except Exception:

        logger.exception("Admin register failed")

        raise HTTPException(
            500,
            "Admin creation failed"
        )


# ============================================================
# ADMIN LIST
# ============================================================

@router.get("/admins")
async def list_admins(

    current_admin:models.AdminUser=
        Depends(get_current_admin),

    db:AsyncSession=Depends(get_db)

):

    result=await db.execute(
        select(models.AdminUser)
    )

    admins=result.scalars().all()

    return [

        {
            "id":a.id,
            "email":a.email,
            "created_at":a.created_at
        }

        for a in admins

    ]


# ============================================================
# PASSWORD RESET
# ============================================================

@router.post("/reset-password/{admin_id}")
async def reset_password(

    admin_id:int,

    payload:dict=Body(...),

    db:AsyncSession=Depends(get_db),

    current_admin:models.AdminUser=
        Depends(get_current_admin)

):

    try:

        new_password=payload.get(
            "new_password"
        )

        if not new_password:

            raise HTTPException(
                400,
                "Password required"
            )

        admin=await db.get(
            models.AdminUser,
            admin_id
        )

        if not admin:

            raise HTTPException(
                404,
                "Admin not found"
            )

        admin.password_hash=get_password_hash(
            new_password
        )

        await db.commit()

        return {
            "success":True
        }

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Password reset failed"
        )

        raise HTTPException(
            500,
            "Reset failed"
        )
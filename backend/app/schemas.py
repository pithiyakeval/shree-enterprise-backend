# app/schemas.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ==========================================================
# LEAD INPUT SCHEMA (Validated & Production Ready)
# ==========================================================


class BaseLeadCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    phone: str = Field(..., min_length=7, max_length=20)
    email: Optional[EmailStr] = None
    city: str = Field(..., min_length=2, max_length=120)
    message: str = Field(..., min_length=2, max_length=500)
    service: str = Field(..., description="solar | mandap | both")
    where_from: str = Field(..., max_length=50)

    # Service-specific optional fields
    kw: Optional[str] = Field(None, max_length=50)
    budget: Optional[str] = Field(None, max_length=150)

    event_type: Optional[str] = Field(None, max_length=150)
    event_date: Optional[str] = Field(None, max_length=50)

    model_config = {"extra": "ignore"}  # ignore unexpected frontend fields safely


# ==========================================================
# LEAD OUTPUT SCHEMA
# ==========================================================


class BaseLeadOut(BaseLeadCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ==========================================================
# CHILD TABLE OUTPUT SCHEMAS
# ==========================================================


class SolarOut(BaseModel):
    id: int
    lead_id: int
    kw: Optional[str]
    budget: Optional[str]

    model_config = {"from_attributes": True}


class MandapOut(BaseModel):
    id: int
    lead_id: int
    event_type: Optional[str]
    budget: Optional[str]
    event_date: Optional[str]

    model_config = {"from_attributes": True}


class CombinedOut(BaseModel):
    id: int
    lead_id: int
    kw: Optional[str] = None
    solar_budget: Optional[str] = None
    event_type: Optional[str] = None
    mandap_budget: Optional[str] = None
    event_date: Optional[str] = None

    model_config = {"from_attributes": True}


# ==========================================================
# ADMIN AUTH SCHEMAS
# ==========================================================


class AdminLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4)


class AdminCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4)


class AdminOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ==========================================================
# ADMIN PASSWORD RESET SCHEMA
# ==========================================================


class PasswordReset(BaseModel):
    new_password: str = Field(..., min_length=4)

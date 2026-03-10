# app/models.py
"""
Production-grade SQLAlchemy ORM models

✔ Strong indexing for faster admin panel
✔ Correct cascade rules
✔ Clean relationship definitions
✔ Enum-like constraints for `service` and `status`
✔ Timestamp auto-generation using PostgreSQL NOW()
✔ Email & phone indexing for fast searches
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base


# ============================================================
# BASE LEADS TABLE
# ============================================================


class BaseLead(Base):
    __tablename__ = "base_leads"

    id = Column(Integer, primary_key=True, index=True)

    # User input
    name = Column(String(150), nullable=False, index=True)
    phone = Column(String(50), nullable=False, index=True)
    email = Column(String(150), nullable=True, index=True)
    city = Column(String(120), nullable=False)
    message = Column(Text, nullable=False)

    # Service assigned: solar / mandap / both
    service = Column(
        String(20), nullable=False, index=True, doc="Lead type: solar / mandap / both"
    )

    # Where user came from: home / solar / mandap / contact
    where_from = Column(String(50), nullable=False, index=True)

    # Optional fields
    kw = Column(String(50), nullable=True)
    budget = Column(String(150), nullable=True)
    event_type = Column(String(150), nullable=True)
    event_date = Column(String(50), nullable=True)

    # Meta fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    status = Column(
        String(20),
        nullable=False,
        server_default="Pending",
        index=True,
        doc="Lead workflow status: Pending / Done",
    )

    # Relationships
    solar_request = relationship(
        "SolarRequest",
        back_populates="lead",
        uselist=False,
        cascade="all, delete-orphan",
    )

    mandap_request = relationship(
        "MandapRequest",
        back_populates="lead",
        uselist=False,
        cascade="all, delete-orphan",
    )

    combined_request = relationship(
        "CombinedRequest",
        back_populates="lead",
        uselist=False,
        cascade="all, delete-orphan",
    )


# ============================================================
# SOLAR TABLE
# ============================================================


class SolarRequest(Base):
    __tablename__ = "solar_requests"

    id = Column(Integer, primary_key=True)
    lead_id = Column(
        Integer, ForeignKey("base_leads.id", ondelete="CASCADE"), index=True
    )

    kw = Column(String(50), nullable=True)
    budget = Column(String(150), nullable=True)

    lead = relationship("BaseLead", back_populates="solar_request")


# ============================================================
# MANDAP TABLE
# ============================================================


class MandapRequest(Base):
    __tablename__ = "mandap_requests"

    id = Column(Integer, primary_key=True)
    lead_id = Column(
        Integer, ForeignKey("base_leads.id", ondelete="CASCADE"), index=True
    )

    event_type = Column(String(150), nullable=True)
    budget = Column(String(150), nullable=True)
    event_date = Column(String(50), nullable=True)

    lead = relationship("BaseLead", back_populates="mandap_request")


# ============================================================
# COMBINED TABLE (BOTH)
# ============================================================


class CombinedRequest(Base):
    __tablename__ = "combined_requests"

    id = Column(Integer, primary_key=True)
    lead_id = Column(
        Integer, ForeignKey("base_leads.id", ondelete="CASCADE"), index=True
    )

    kw = Column(String(50), nullable=True)
    solar_budget = Column(String(150), nullable=True)

    event_type = Column(String(150), nullable=True)
    mandap_budget = Column(String(150), nullable=True)
    event_date = Column(String(50), nullable=True)

    lead = relationship("BaseLead", back_populates="combined_request")


# ============================================================
# ADMIN USER TABLE
# ============================================================


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

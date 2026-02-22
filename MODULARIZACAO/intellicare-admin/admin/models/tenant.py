"""Tenant and TenantModule ORM models — schema 'platform'."""

import re
import uuid
from datetime import datetime, UTC

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, JSON, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all platform models."""
    pass


# ─── Helpers ─────────────────────────────────────────────────

_SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,62}$")


def generate_slug(nome_fantasia: str) -> str:
    """Generate a tenant_id slug from company name.

    Example: 'Hospital Einstein' → 'hospital_einstein'
    """
    slug = nome_fantasia.lower().strip()
    slug = re.sub(r"[àáâãä]", "a", slug)
    slug = re.sub(r"[èéêë]", "e", slug)
    slug = re.sub(r"[ìíîï]", "i", slug)
    slug = re.sub(r"[òóôõö]", "o", slug)
    slug = re.sub(r"[ùúûü]", "u", slug)
    slug = re.sub(r"[ç]", "c", slug)
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = slug.strip("_")
    return slug[:63]


def validate_cnpj(cnpj: str) -> bool:
    """Validate CNPJ format and check digits."""
    cnpj_digits = re.sub(r"\D", "", cnpj)
    if len(cnpj_digits) != 14:
        return False
    if cnpj_digits == cnpj_digits[0] * 14:
        return False

    # First check digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(cnpj_digits[i]) * weights1[i] for i in range(12))
    remainder = total % 11
    d1 = 0 if remainder < 2 else 11 - remainder
    if int(cnpj_digits[12]) != d1:
        return False

    # Second check digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(cnpj_digits[i]) * weights2[i] for i in range(13))
    remainder = total % 11
    d2 = 0 if remainder < 2 else 11 - remainder
    return int(cnpj_digits[13]) == d2


# ─── Models ──────────────────────────────────────────────────

class Tenant(Base):
    """Represents an organization (tenant) on the IntelliCare platform."""

    __tablename__ = "tenants"
    __table_args__ = {"schema": "platform"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(100), unique=True, nullable=False, index=True)  # slug
    nome_fantasia = Column(String(255), nullable=False)
    razao_social = Column(String(255), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=False)
    email_admin = Column(String(255), nullable=False)

    # Branding
    logo_url = Column(String(500))
    cor_primaria = Column(String(7), default="#1E88E5")
    cor_secundaria = Column(String(7), default="#43A047")
    dominio_custom = Column(String(255))

    # Plan
    plan_id = Column(UUID(as_uuid=True), ForeignKey("platform.plans.id"))
    plan = relationship("Plan", back_populates="tenants", lazy="selectin")

    # Status: active, suspended, trial, cancelled
    status = Column(String(20), default="trial", index=True)
    provisioned = Column(Boolean, default=False)

    # Limits
    max_users = Column(Integer, default=5)
    max_sms_month = Column(Integer, default=100)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(UTC))
    trial_expires_at = Column(DateTime)
    suspended_at = Column(DateTime)

    # Relationships
    modules = relationship("TenantModule", back_populates="tenant", lazy="selectin")
    billing_records = relationship("BillingRecord", back_populates="tenant", lazy="noload")

    def __repr__(self) -> str:
        return f"<Tenant {self.tenant_id} status={self.status}>"


class TenantModule(Base):
    """Tracks which modules are enabled for a tenant."""

    __tablename__ = "tenant_modules"
    __table_args__ = {"schema": "platform"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        String(100),
        ForeignKey("platform.tenants.tenant_id"),
        nullable=False,
        index=True,
    )
    module_name = Column(String(100), nullable=False)  # "zilda", "oswaldo", etc.
    enabled = Column(Boolean, default=True)
    config_json = Column(JSON, default=dict)
    activated_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationship
    tenant = relationship("Tenant", back_populates="modules")

    def __repr__(self) -> str:
        return f"<TenantModule {self.tenant_id}/{self.module_name} enabled={self.enabled}>"

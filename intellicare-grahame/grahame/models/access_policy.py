"""SQLAlchemy ORM models for FHIR Access Policies in intellicare-grahame."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import JSON, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from grahame.models.base import Base


class AccessPolicy(Base):
    """A named access policy defining what a user can do and see."""

    __tablename__ = "access_policies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_rules: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    """List of ResourceRule dicts."""
    compartment_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    """e.g. 'Organization/setor-a'"""
    ip_access_rules: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )


class TenantMembership(Base):
    """Assignment of an AccessPolicy to a user within a tenant."""

    __tablename__ = "tenant_memberships"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    """Keycloak sub claim."""
    access_policy_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    parameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    """Parameter substitutions: {'%profile': 'Practitioner/123'}."""
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.datetime.utcnow, nullable=False
    )

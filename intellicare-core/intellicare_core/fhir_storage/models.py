"""SQLAlchemy ORM models for FHIR-Native Storage.

Two tables:
    fhir_native_resources — current state of each resource
    fhir_native_history   — full audit history (every create/update/delete)

Designed to be database-agnostic (SQLite for tests, PostgreSQL for production).
JSON columns use sqlalchemy.JSON which maps to:
    - SQLite:     TEXT with JSON_EXTRACT for querying
    - PostgreSQL: JSONB with GIN indexes for full-text FHIR search
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Boolean, DateTime, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class FHIRStorageBase(DeclarativeBase):
    """Separate base to avoid metadata collision with Grahame models."""
    pass


class FHIRNativeResource(FHIRStorageBase):
    """Current state of a FHIR resource — one row per (tenant, type, fhir_id).

    Updated in-place on every PUT/PATCH; old states go to fhir_native_history.
    """

    __tablename__ = "fhir_native_resources"
    __table_args__ = (
        UniqueConstraint("tenant_id", "resource_type", "fhir_id", name="uq_fhir_native_current"),
    )

    # Surrogate PK for SQLite compat (UUID is stored as text)
    pk: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    fhir_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    """FHIR resource id (from resource.id)."""

    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    version_id: Mapped[str] = mapped_column(
        String(36), nullable=False, default=lambda: str(uuid.uuid4())
    )
    """UUID of the current version — matches fhir_native_history entry."""

    resource: Mapped[dict] = mapped_column(JSON, nullable=False)
    """Complete FHIR resource (JSON)."""

    last_updated: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, default=datetime.datetime.utcnow
    )
    author: Mapped[str | None] = mapped_column(String(256), nullable=True)
    """Practitioner/123 — who last wrote this resource."""

    compartments: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    """List of compartment references: ['Patient/123', 'Organization/abc']."""

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class FHIRResourceHistory(FHIRStorageBase):
    """Audit log — every create / update / delete creates one row."""

    __tablename__ = "fhir_native_history"

    version_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    """UUID PK — same value stored in FHIRNativeResource.version_id."""

    fhir_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)

    resource: Mapped[dict] = mapped_column(JSON, nullable=False)
    """Snapshot of the resource at this version."""

    last_updated: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )
    author: Mapped[str | None] = mapped_column(String(256), nullable=True)

    interaction: Mapped[str] = mapped_column(String(16), nullable=False)
    """create | update | delete"""

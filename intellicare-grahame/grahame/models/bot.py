"""SQLAlchemy ORM models for Bots in intellicare-grahame."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from grahame.models.base import Base


class Bot(Base):
    """A Bot resource — contains tenant-defined Python code executed on FHIR events."""

    __tablename__ = "bots"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, default="")
    code_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    runtime: Mapped[str] = mapped_column(String(32), default="sandbox", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)
    run_as_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )


class BotSecret(Base):
    """Encrypted secret associated with a Bot or tenant-wide."""

    __tablename__ = "bot_secrets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    bot_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    value_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.datetime.utcnow, nullable=False
    )


class BotExecution(Base):
    """Audit log for every bot execution attempt."""

    __tablename__ = "bot_executions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    bot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    subscription_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    input_resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    interaction: Mapped[str] = mapped_column(String(32), default="create", nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    log_output: Mapped[str] = mapped_column(Text, default="", nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.datetime.utcnow, nullable=False
    )

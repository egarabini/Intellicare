"""
Measurement model - Medições temporais dos indicadores.

Armazena valores medidos de indicadores ao longo do tempo,
com cálculo automático de status (green/yellow/red).

FASE 2: Updated with audit metadata, UUID primary key, soft delete, and optimistic locking.
"""

from datetime import datetime, date
from typing import Optional
from uuid import UUID as PythonUUID
import enum

from sqlalchemy import String, Integer, Float, DateTime, Date, ForeignKey, Enum as SQLEnum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from donabedian.models import Base


class PeriodType(str, enum.Enum):
    """Tipos de período de medição."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class MeasurementStatus(str, enum.Enum):
    """Status da medição em relação à meta."""
    GREEN = "green"    # Meta atingida
    YELLOW = "yellow"  # Próximo da meta (90-100% ou 100-110%)
    RED = "red"        # Abaixo/acima da meta


class Measurement(Base):
    """
    Measurement model representing time-series data for indicators.
    
    Each measurement records a value for an indicator in a specific period,
    with automatic status calculation based on the indicator's target.
    
    Features:
    - UUID primary key (distributed systems compatible)
    - Audit metadata (created_by, created_at, updated_by, updated_at)
    - Soft delete (valid_to for data retention)
    - Optimistic locking (rowversion for concurrent update detection)
    """
    
    __tablename__ = "medicoes"
    
    # Primary Key (FASE 2: UUID instead of autoincrement)
    id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()",
        comment="Unique identifier (UUID)"
    )
    
    # Foreign Key (Updated to UUID to match Indicator)
    indicator_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("donabedian_operacional.indicadores.id"),
        nullable=False,
        comment="Reference to indicator"
    )
    
    # Measurement Data
    valor: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Measured value"
    )
    
    # Period Information
    periodo_inicio: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Start date of measurement period"
    )
    
    periodo_fim: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="End date of measurement period"
    )
    
    tipo_periodo: Mapped[PeriodType] = mapped_column(
        SQLEnum(PeriodType, native_enum=False, length=20),
        nullable=False,
        comment="Type of period (daily, weekly, monthly, quarterly, yearly)"
    )
    
    # Status (auto-calculated based on target)
    status: Mapped[MeasurementStatus] = mapped_column(
        SQLEnum(MeasurementStatus, native_enum=False, length=10),
        nullable=False,
        comment="Status: green (met), yellow (close), red (not met)"
    )
    
    # ========================================================================
    # AUDIT METADATA (REQUIRED - FASE 2)
    # ========================================================================
    
    created_by: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="User ID who created this measurement"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="Timestamp when measurement was recorded"
    )
    
    updated_by: Mapped[Optional[PythonUUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who last updated this measurement"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="Timestamp when measurement was last updated"
    )
    
    # ========================================================================
    # SOFT DELETE (REQUIRED - FASE 2)
    # ========================================================================
    
    valid_to: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft delete timestamp (NULL = active)"
    )
    
    # ========================================================================
    # OPTIMISTIC LOCKING (REQUIRED - FASE 2)
    # ========================================================================
    
    rowversion: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Row version for optimistic locking"
    )
    
    # Constraint: valid_to must be after created_at if set
    __table_args__ = (
        CheckConstraint('valid_to IS NULL OR valid_to > created_at', name='ck_measurement_valid_to'),
    )
    
    # Relationships
    indicator: Mapped["Indicator"] = relationship(
        "Indicator",
        back_populates="measurements",
        foreign_keys=[indicator_id]
    )
    
    def __repr__(self) -> str:
        return (
            f"<Measurement(id={self.id}, "
            f"indicator_id={self.indicator_id}, "
            f"valor={self.valor}, "
            f"status='{self.status.value}', "
            f"periodo={self.periodo_inicio} to {self.periodo_fim})>"
        )
    
    def __str__(self) -> str:
        return f"{self.valor} ({self.status.value}) - {self.periodo_inicio}"
    
    def is_deleted(self) -> bool:
        """Check if this record is soft-deleted."""
        return self.valid_to is not None


"""
IndicatorPillar model - Tabela associativa N:N entre Indicator e Pillar.

Permite que um indicador esteja associado a múltiplos pilares,
com pesos diferentes para cada associação.

FASE 2: Updated with UUID references to match parent models.
"""

from uuid import UUID as PythonUUID

from sqlalchemy import Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from donabedian.models import Base


class IndicatorPillar(Base):
    """
    IndicatorPillar model - N:N associative table.
    
    Links indicators to pillars with a weight field that allows
    different importance levels for the same indicator across different pillars.
    
    Features (FASE 2):
    - UUID foreign keys (matches parent models)
    - Integer primary key (can be optimized later if needed)
    
    Example:
        "Hospital Infection Rate" indicator might have:
        - weight=1.0 in Efficacy pillar
        - weight=0.8 in Effectiveness pillar
        - weight=0.5 in Efficiency pillar
    """
    
    __tablename__ = "indicador_pilar"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys (FASE 2: Updated to UUID)
    indicator_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("donabedian_operacional.indicadores.id"),
        nullable=False,
        comment="Reference to indicator"
    )

    pillar_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("donabedian_operacional.pilares.id"),
        nullable=False,
        comment="Reference to pillar"
    )
    
    # Weight Field
    peso: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
        comment="Weight/importance of this indicator in this pillar (0.0-1.0)"
    )
    
    # Relationships
    indicator: Mapped["Indicator"] = relationship(
        "Indicator",
        back_populates="indicator_pillars",
        foreign_keys=[indicator_id]
    )
    
    pillar: Mapped["Pillar"] = relationship(
        "Pillar",
        back_populates="indicator_pillars",
        foreign_keys=[pillar_id]
    )
    
    def __repr__(self) -> str:
        return (
            f"<IndicatorPillar(id={self.id}, "
            f"indicator_id={self.indicator_id}, "
            f"pillar_id={self.pillar_id}, "
            f"peso={self.peso})>"
        )
    
    def __str__(self) -> str:
        return f"Indicator {self.indicator_id} → Pillar {self.pillar_id} (peso={self.peso})"


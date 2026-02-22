"""
Example service using OperationalDataAccess with EventPublisher.

This demonstrates FASE 2.2 integration: CREATE/UPDATE/DELETE → Redis Events → Analytics
"""

import logging
from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session

from donabedian.models import Pillar
from donabedian.data_access import OperationalDataAccess
from donabedian.events import get_event_callback, get_event_publisher

logger = logging.getLogger(__name__)


class PillarService:
    """
    Service for managing pillars with event publishing.
    
    Every CREATE/UPDATE/DELETE operation publishes an event to Redis Streams
    which is then consumed by ConsolidationConsumer (FASE 1) to update analytics.
    """

    def __init__(self, session: Session):
        """
        Initialize service with event publishing.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
        
        # Initialize event publisher (connects to Redis)
        self.publisher = get_event_publisher()
        
        # Create callback for OperationalDataAccess
        self.event_callback = get_event_callback(self.publisher)
        
        # Initialize DAO with callback
        self.dao = OperationalDataAccess(
            session=session,
            entity_class=Pillar,
            event_callback=self.event_callback
        )

    def create_pilar(
        self,
        nome: str,
        descricao: str,
        tipo: str,
        ordem_exibicao: int,
        actor_id: UUID
    ) -> Pillar:
        """
        Create a new pillar.
        
        Flow:
        1. DAO validates and creates in donabedian_operacional
        2. Callback publishes "pilar.create" event to Redis
        3. ConsolidationConsumer reads event and denormalizes to donabedian_analitico
        
        Args:
            nome: Pillar name
            descricao: Description
            tipo: Type (ESTRUTURA, PROCESSO, RESULTADO)
            ordem_exibicao: Display order
            actor_id: User creating this
            
        Returns:
            Created Pillar
        """
        pilar = Pillar(
            nome=nome,
            descricao=descricao,
            tipo=tipo,
            ordem_exibicao=ordem_exibicao,
            ativo=True,
            created_by=actor_id,
        )
        
        # Create via DAO (triggers event_callback)
        created = self.dao.create(
            entity=pilar,
            actor_id=actor_id,
            reason=f"Created pillar '{nome}' via API"
        )
        
        logger.info(f"✅ Created pilar: {created.id} ({nome})")
        
        return created

    def update_pilar(
        self,
        pilar_id: UUID,
        nome: Optional[str] = None,
        descricao: Optional[str] = None,
        ativo: Optional[bool] = None,
        actor_id: Optional[UUID] = None
    ) -> Pillar:
        """
        Update an existing pillar.
        
        Flow:
        1. DAO reads from donabedian_operacional
        2. Validates and updates
        3. Callback publishes "pilar.update" event to Redis
        4. ConsolidationConsumer updates denormalized record in donabedian_analitico
        
        Args:
            pilar_id: Pillar UUID
            nome: New name (optional)
            descricao: New description (optional)
            ativo: New status (optional)
            actor_id: User updating this
            
        Returns:
            Updated Pillar
            
        Raises:
            ValueError: If pilar not found
        """
        pilar = self.dao.read(pilar_id)
        if not pilar:
            raise ValueError(f"Pilar {pilar_id} not found")
        
        # Track changes for audit
        changes = []
        if nome is not None and pilar.nome != nome:
            pilar.nome = nome
            changes.append(f"nome={nome}")
        if descricao is not None and pilar.descricao != descricao:
            pilar.descricao = descricao
            changes.append(f"descricao={descricao}")
        if ativo is not None and pilar.ativo != ativo:
            pilar.ativo = ativo
            changes.append(f"ativo={ativo}")
        
        if not changes:
            logger.info("No changes to apply")
            return pilar
        
        # Update via DAO (triggers event_callback)
        updated = self.dao.update(
            entity=pilar,
            actor_id=actor_id,
            reason=f"Updated pilar: {', '.join(changes)}"
        )
        
        logger.info(f"✅ Updated pilar: {updated.id} ({', '.join(changes)})")
        
        return updated

    def delete_pilar(
        self,
        pilar_id: UUID,
        actor_id: Optional[UUID] = None
    ) -> bool:
        """
        Soft-delete a pillar.
        
        Flow:
        1. Marks record as deleted (valid_to = NOW())
        2. Callback publishes "pilar.delete" event to Redis
        3. ConsolidationConsumer updates analytic record (sets valid_to)
        
        Args:
            pilar_id: Pillar UUID
            actor_id: User deleting this
            
        Returns:
            True if deleted, False if not found
        """
        success = self.dao.delete(
            entity_id=pilar_id,
            actor_id=actor_id,
            reason="Pilar deleted"
        )
        
        if success:
            logger.info(f"✅ Deleted pilar: {pilar_id}")
        else:
            logger.warning(f"❌ Pilar not found: {pilar_id}")
        
        return success

    def close(self) -> None:
        """Close event publisher connection."""
        self.publisher.close()


# ============================================================================
# USAGE IN API ROUTES
# ============================================================================

"""
Example FastAPI route using PillarService with event publishing:

from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from donabedian.services.pilar_service import PillarService

router = APIRouter(prefix="/pilares", tags=["Pilares"])

async def get_pilar_service(session: Session = Depends(get_db_session)) -> PillarService:
    return PillarService(session)

@router.post("/")
async def criar_pilar(
    nome: str,
    descricao: str,
    tipo: str,
    service: PillarService = Depends(get_pilar_service),
    actor_id: UUID = Depends(get_current_user_id),
) -> dict:
    try:
        pilar = service.create_pilar(
            nome=nome,
            descricao=descricao,
            tipo=tipo,
            ordem_exibicao=1,
            actor_id=actor_id,
        )
        session.commit()
        return {"id": str(pilar.id), "nome": pilar.nome}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{pilar_id}")
async def atualizar_pilar(
    pilar_id: UUID,
    nome: str,
    ativo: bool,
    service: PillarService = Depends(get_pilar_service),
    actor_id: UUID = Depends(get_current_user_id),
) -> dict:
    try:
        pilar = service.update_pilar(
            pilar_id=pilar_id,
            nome=nome,
            ativo=ativo,
            actor_id=actor_id,
        )
        session.commit()
        return {"id": str(pilar.id), "nome": pilar.nome, "rowversion": pilar.rowversion}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{pilar_id}")
async def deletar_pilar(
    pilar_id: UUID,
    service: PillarService = Depends(get_pilar_service),
    actor_id: UUID = Depends(get_current_user_id),
) -> dict:
    try:
        success = service.delete_pilar(pilar_id=pilar_id, actor_id=actor_id)
        if not success:
            raise HTTPException(status_code=404, detail="Pilar not found")
        session.commit()
        return {"deleted": True, "id": str(pilar_id)}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
"""

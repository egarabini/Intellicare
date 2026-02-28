"""Excalidraw API Routes.

Endpoints para gerenciar diagramas Excalidraw integrados com FHIR.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.api.deps import get_db
from grahame.services.excalidraw import ExcalidrawDiagramStorage, ExcalidrawCollaborationService


# Router
router = APIRouter(prefix="/excalidraw", tags=["Excalidraw"])

# Serviço de colaboração (singleton)
collaboration_service = ExcalidrawCollaborationService()


# Schemas
class CreateDiagramRequest(BaseModel):
    """Request para criar um diagrama."""
    diagram_data: Dict[str, Any] = Field(..., description="Dados do diagrama Excalidraw (JSON)")
    patient_id: str = Field(..., description="ID do paciente (FHIR Patient)")
    title: str = Field(..., description="Título do diagrama")
    description: Optional[str] = Field(None, description="Descrição opcional")
    category: str = Field("clinical-diagram", description="Categoria do diagrama")
    author_id: Optional[str] = Field(None, description="ID do autor (FHIR Practitioner)")


class UpdateDiagramRequest(BaseModel):
    """Request para atualizar um diagrama."""
    diagram_data: Dict[str, Any] = Field(..., description="Novos dados do diagrama")
    title: Optional[str] = Field(None, description="Novo título (opcional)")


class DiagramResponse(BaseModel):
    """Response com dados de um diagrama."""
    id: str
    data: Dict[str, Any]
    title: str
    created: str
    patient_id: str


class DiagramListItem(BaseModel):
    """Item da lista de diagramas."""
    id: str
    document_reference_id: str
    title: str
    description: str
    category: str
    created: str
    author: str


class CreateDiagramResponse(BaseModel):
    """Response ao criar um diagrama."""
    media_id: str
    document_reference_id: str
    diagram_url: str


# Endpoints REST
@router.post("/diagrams", response_model=CreateDiagramResponse, status_code=201)
def create_diagram(
    request: CreateDiagramRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = "default",  # TODO: Get from auth context
):
    """Cria um novo diagrama Excalidraw.
    
    Salva o diagrama como FHIR Media + DocumentReference.
    """
    storage = ExcalidrawDiagramStorage(db, tenant_id)
    
    result = storage.save_diagram(
        diagram_data=request.diagram_data,
        patient_id=request.patient_id,
        title=request.title,
        description=request.description,
        category=request.category,
        author_id=request.author_id,
    )
    
    return result


@router.get("/diagrams/{media_id}", response_model=DiagramResponse)
def get_diagram(
    media_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = "default",
):
    """Recupera um diagrama Excalidraw."""
    storage = ExcalidrawDiagramStorage(db, tenant_id)
    
    diagram = storage.get_diagram(media_id)
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    return diagram


@router.get("/patients/{patient_id}/diagrams", response_model=List[DiagramListItem])
def list_patient_diagrams(
    patient_id: str,
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = "default",
):
    """Lista todos os diagramas de um paciente."""
    storage = ExcalidrawDiagramStorage(db, tenant_id)
    
    diagrams = storage.list_patient_diagrams(patient_id, category)
    return diagrams


@router.put("/diagrams/{media_id}", status_code=200)
def update_diagram(
    media_id: str,
    request: UpdateDiagramRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = "default",
):
    """Atualiza um diagrama existente (cria nova versão)."""
    storage = ExcalidrawDiagramStorage(db, tenant_id)
    
    success = storage.update_diagram(
        media_id=media_id,
        diagram_data=request.diagram_data,
        title=request.title,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    return {"status": "updated", "media_id": media_id}


@router.delete("/diagrams/{media_id}", status_code=204)
def delete_diagram(
    media_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = "default",
):
    """Deleta um diagrama (soft delete)."""
    storage = ExcalidrawDiagramStorage(db, tenant_id)
    
    success = storage.delete_diagram(media_id)
    if not success:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    return None


# WebSocket para colaboração em tempo real
@router.websocket("/collaborate/{room_id}")
async def collaborate_websocket(
    websocket: WebSocket,
    room_id: str,
    user_id: str = Query(..., description="ID do usuário"),
    user_name: str = Query(..., description="Nome do usuário"),
    patient_id: Optional[str] = Query(None, description="ID do paciente"),
):
    """WebSocket para colaboração em tempo real em um diagrama.
    
    Permite múltiplos usuários editarem o mesmo diagrama simultaneamente.
    """
    await websocket.accept()
    
    try:
        # Entrar na sala
        await collaboration_service.join_room(
            room_id=room_id,
            websocket=websocket,
            user_id=user_id,
            user_name=user_name,
            patient_id=patient_id,
        )
        
        # Loop de mensagens
        while True:
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "diagram-update":
                # Broadcast de atualização do diagrama
                await collaboration_service.broadcast_update(
                    room_id=room_id,
                    sender_ws=websocket,
                    update_data=data.get("data", {}),
                )
            
            elif message_type == "cursor-update":
                # Broadcast de posição do cursor
                await collaboration_service.broadcast_cursor(
                    room_id=room_id,
                    sender_ws=websocket,
                    user_id=user_id,
                    cursor_data=data.get("cursor", {}),
                )
    
    except WebSocketDisconnect:
        # Sair da sala ao desconectar
        await collaboration_service.leave_room(room_id, websocket, user_id)
    
    except Exception as e:
        # Log error e sair da sala
        print(f"WebSocket error: {e}")
        await collaboration_service.leave_room(room_id, websocket, user_id)

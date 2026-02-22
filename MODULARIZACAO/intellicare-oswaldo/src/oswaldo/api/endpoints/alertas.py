"""
Query endpoints para Alerta (clinical alerts).

Endpoints (read-only):
- GET /api/v1/oswaldo/alertas/pendentes
- GET /api/v1/oswaldo/alertas/{id}
- GET /api/v1/oswaldo/paciente/{cpf_hash}/alertas
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from datetime import date

from src.oswaldo.models.oswaldo_models import Alerta, CondicaoCronica
from src.oswaldo.schemas.oswaldo_schemas import (
    AlertaResponse,
    AlertasListResponse,
)
from src.oswaldo.database.session import get_db

router = APIRouter()


@router.get(
    "/alertas/pendentes",
    response_model=AlertasListResponse,
    tags=["alertas"],
    summary="Listar alertas pendentes"
)
def listar_alertas_pendentes(
    severidade: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Listar alertas clínicos pendentes (status=NOVO).
    
    Severidade opcional:
    - CRITICO
    - ALTO
    - MÉDIO
    - BAIXO
    
    Alertas mais críticos primeiro.
    """
    query = db.query(Alerta).filter(Alerta.status == "NOVO")
    
    if severidade:
        valid_severidades = ["CRITICO", "ALTO", "MÉDIO", "BAIXO"]
        if severidade not in valid_severidades:
            raise HTTPException(
                status_code=400,
                detail=f"Severidade inválida. Opções: {', '.join(valid_severidades)}"
            )
        query = query.filter(Alerta.severidade == severidade)
    
    total = query.count()
    
    # Ordernar por data (mais recente primeiro)
    items = query.order_by(
        desc(Alerta.data_criacao)
    ).offset(skip).limit(limit).all()
    
    # Ordenar em memória por severidade depois por data
    severity_order = {"CRITICO": 4, "ALTO": 3, "MÉDIO": 2, "BAIXO": 1}
    items.sort(
        key=lambda x: (-severity_order.get(x.severidade, 0), -x.data_criacao.timestamp())
    )
    
    return AlertasListResponse(total=total, items=items)


@router.get(
    "/alertas/resumo",
    tags=["alertas"],
    summary="Resumo de alertas por severidade"
)
def resumo_alertas(
    db: Session = Depends(get_db),
):
    """
    Obter resumo de alertas por severidade e status.
    
    Útil para dashboards e monitores.
    """
    from sqlalchemy import func
    
    # Alertas por severidade
    por_severidade = db.query(
        Alerta.severidade,
        func.count(Alerta.id).label("total")
    ).filter(
        Alerta.status == "NOVO"
    ).group_by(Alerta.severidade).all()
    
    # Alertas por status
    por_status = db.query(
        Alerta.status,
        func.count(Alerta.id).label("total")
    ).group_by(Alerta.status).all()
    
    return {
        "por_severidade": [
            {"severidade": sev, "total": total}
            for sev, total in por_severidade
        ],
        "por_status": [
            {"status": status, "total": total}
            for status, total in por_status
        ],
        "total_pendentes": db.query(func.count(Alerta.id)).filter(
            Alerta.status == "NOVO"
        ).scalar() or 0
    }


@router.get(
    "/alertas/{alerta_id}",
    response_model=AlertaResponse,
    tags=["alertas"],
    summary="Obter detalhes de um alerta"
)
def obter_alerta(
    alerta_id: int,
    db: Session = Depends(get_db),
):
    """
    Obter detalhes completo de um alerta clínico.
    """
    alerta = db.query(Alerta).filter(
        Alerta.id == alerta_id
    ).first()
    
    if not alerta:
        raise HTTPException(
            status_code=404,
            detail=f"Alerta {alerta_id} não encontrado"
        )
    
    return alerta


@router.get(
    "/paciente/{paciente_cpf_hash}/alertas",
    response_model=AlertasListResponse,
    tags=["alertas"],
    summary="Listar alertas de um paciente"
)
def listar_alertas_paciente(
    paciente_cpf_hash: str,
    status: str = Query(None),
    severidade: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Listar alertas clínicos de um paciente.
    
    Filtro por status opcional:
    - NOVO (não lido/acionado)
    - ACIONADO (ação tomada)
    - RESOLVIDO (resolvido)
    - DESCONSIDERADO (usuário ignorou)
    
    Filtro por severidade opcional:
    - CRITICO
    - ALTO
    - MÉDIO
    - BAIXO
    
    Alertas mais recentes primeiro.
    """
    query = db.query(Alerta).filter(
        Alerta.paciente_cpf_hash == paciente_cpf_hash
    )
    
    if status:
        valid_status = ["NOVO", "ACIONADO", "RESOLVIDO", "DESCONSIDERADO"]
        if status not in valid_status:
            raise HTTPException(
                status_code=400,
                detail=f"Status inválido. Opções: {', '.join(valid_status)}"
            )
        query = query.filter(Alerta.status == status)
    
    if severidade:
        valid_severidades = ["CRITICO", "ALTO", "MÉDIO", "BAIXO"]
        if severidade not in valid_severidades:
            raise HTTPException(
                status_code=400,
                detail=f"Severidade inválida. Opções: {', '.join(valid_severidades)}"
            )
        query = query.filter(Alerta.severidade == severidade)
    
    total = query.count()
    items = query.order_by(desc(Alerta.data_criacao)).offset(skip).limit(limit).all()
    
    return AlertasListResponse(total=total, items=items)


@router.get(
    "/alertas/resumo",
    tags=["alertas"],
    summary="Resumo de alertas por severidade"
)
def resumo_alertas(
    db: Session = Depends(get_db),
):
    """
    Obter resumo de alertas por severidade e status.
    
    Útil para dashboards e monitores.
    """
    from sqlalchemy import func
    
    # Alertas por severidade
    por_severidade = db.query(
        Alerta.severidade,
        func.count(Alerta.id).label("total")
    ).filter(
        Alerta.status == "NOVO"
    ).group_by(Alerta.severidade).all()
    
    # Alertas por status
    por_status = db.query(
        Alerta.status,
        func.count(Alerta.id).label("total")
    ).group_by(Alerta.status).all()
    
    return {
        "por_severidade": [
            {"severidade": sev, "total": total}
            for sev, total in por_severidade
        ],
        "por_status": [
            {"status": status, "total": total}
            for status, total in por_status
        ],
        "total_pendentes": db.query(func.count(Alerta.id)).filter(
            Alerta.status == "NOVO"
        ).scalar() or 0
    }

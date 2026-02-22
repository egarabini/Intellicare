"""
CRUD endpoints para Acompanhamento (clinical follow-ups).

Endpoints:
- POST /api/v1/oswaldo/acompanhamentos
- GET /api/v1/oswaldo/paciente/{cpf_hash}/acompanhamentos
- GET /api/v1/oswaldo/acompanhamentos/{id}
- GET /api/v1/oswaldo/paciente/{cpf_hash}/timeline
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import date, datetime

from src.oswaldo.models.oswaldo_models import Acompanhamento, CondicaoCronica
from src.oswaldo.schemas.oswaldo_schemas import (
    AcompanhamentoCreate,
    AcompanhamentoResponse,
    AcompanhamentosListResponse,
)
from src.oswaldo.database.session import get_db

router = APIRouter()


@router.post(
    "/acompanhamentos",
    response_model=AcompanhamentoResponse,
    status_code=201,
    tags=["acompanhamentos"],
    summary="Registrar acompanhamento clínico"
)
def criar_acompanhamento(
    paciente_cpf_hash: str,
    acompanhamento: AcompanhamentoCreate,
    db: Session = Depends(get_db),
):
    """
    Registrar novo acompanhamento clínico (visita, consulta, etc).
    
    Valida:
    - Paciente + condição existem
    - Adesão está entre 0-100 (se fornecida)
    """
    # Verificar se condição existe
    condicao = db.query(CondicaoCronica).filter(
        CondicaoCronica.id == acompanhamento.condicao_cronica_id,
        CondicaoCronica.paciente_cpf_hash == paciente_cpf_hash
    ).first()
    
    if not condicao:
        raise HTTPException(
            status_code=404,
            detail=f"Condição {acompanhamento.condicao_cronica_id} não encontrada para paciente"
        )
    
    # Validar adesão (se fornecida)
    if acompanhamento.aderencia_medicacao is not None:
        if not (0 <= acompanhamento.aderencia_medicacao <= 100):
            raise HTTPException(
                status_code=400,
                detail="Aderência deve estar entre 0 e 100%"
            )
    
    # Criar acompanhamento
    db_acompanhamento = Acompanhamento(
        paciente_cpf_hash=paciente_cpf_hash,
        condicao_cronica_id=acompanhamento.condicao_cronica_id,
        data_acompanhamento=acompanhamento.data_acompanhamento or datetime.now(),
        medico_id=acompanhamento.medico_responsavel,
        pressao_arterial=f"{acompanhamento.pa_sist}/{acompanhamento.pa_diast}" if acompanhamento.pa_sist and acompanhamento.pa_diast else None,
        peso_kg=None,
        glicemia=acompanhamento.glicemia_jejum,
        temperatura=None,
        adesao_medicamentos=None,
        observacoes=acompanhamento.notas_clinicas,
        medicamentos_vigentes=None,
        proxima_consulta=None
    )
    
    db.add(db_acompanhamento)
    db.commit()
    db.refresh(db_acompanhamento)
    
    return db_acompanhamento


@router.get(
    "/paciente/{paciente_cpf_hash}/acompanhamentos",
    response_model=AcompanhamentosListResponse,
    tags=["acompanhamentos"],
    summary="Listar acompanhamentos de um paciente"
)
def listar_acompanhamentos(
    paciente_cpf_hash: str,
    condicao_id: int = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Listar acompanhamentos clínicos de um paciente.
    
    Opcionalmente filtrar por condição específica.
    Ordenado por data mais recente primeiro.
    """
    query = db.query(Acompanhamento).filter(
        Acompanhamento.paciente_cpf_hash == paciente_cpf_hash
    )
    
    if condicao_id:
        query = query.filter(Acompanhamento.condicao_cronica_id == condicao_id)
    
    total = query.count()
    items = query.order_by(
        desc(Acompanhamento.data_acompanhamento)
    ).offset(skip).limit(limit).all()
    
    return AcompanhamentosListResponse(total=total, items=items)


@router.get(
    "/acompanhamentos/{acompanhamento_id}",
    response_model=AcompanhamentoResponse,
    tags=["acompanhamentos"],
    summary="Obter detalhes de um acompanhamento"
)
def obter_acompanhamento(
    acompanhamento_id: int,
    db: Session = Depends(get_db),
):
    """
    Obter detalhes completos de um acompanhamento clínico.
    """
    acompanhamento = db.query(Acompanhamento).filter(
        Acompanhamento.id == acompanhamento_id
    ).first()
    
    if not acompanhamento:
        raise HTTPException(
            status_code=404,
            detail=f"Acompanhamento {acompanhamento_id} não encontrado"
        )
    
    return acompanhamento


@router.get(
    "/paciente/{paciente_cpf_hash}/timeline",
    tags=["timeline"],
    summary="Obter timeline clínica do paciente"
)
def obter_timeline_paciente(
    paciente_cpf_hash: str,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Obter timeline consolidada do paciente com:
    - Criação de condições (data diagnóstico)
    - Acompanhamentos (histórico de visitas com vitais)
    
    Ordenado cronologicamente (mais recente primeiro).
    """
    # Buscar condições
    condicoes = db.query(CondicaoCronica).filter(
        CondicaoCronica.paciente_cpf_hash == paciente_cpf_hash
    ).all()
    
    # Buscar acompanhamentos
    acompanhamentos = db.query(Acompanhamento).filter(
        Acompanhamento.paciente_cpf_hash == paciente_cpf_hash
    ).order_by(
        desc(Acompanhamento.data_acompanhamento)
    ).limit(limit).all()
    
    # Consolidar timeline
    timeline = []
    
    # Adicionar eventos de condições
    for cond in condicoes:
        timeline.append({
            "tipo": "condicao",
            "data": cond.data_diagnostico.isoformat() if cond.data_diagnostico else cond.criado_em.isoformat(),
            "cid10": cond.cid10,
            "status": cond.status,
            "id": cond.id
        })
    
    # Adicionar eventos de acompanhamentos
    for acomp in acompanhamentos:
        timeline.append({
            "tipo": "acompanhamento",
            "data": acomp.data_acompanhamento.isoformat(),
            "condicao_id": acomp.condicao_cronica_id,
            "medico": acomp.medico_id,
            "id": acomp.id
        })
    
    # Ordenar por data descrescente
    timeline.sort(key=lambda x: x["data"], reverse=True)
    
    return {
        "paciente_cpf_hash": paciente_cpf_hash,
        "total_eventos": len(timeline),
        "total_condicoes": len(condicoes),
        "total_acompanhamentos": len(acompanhamentos),
        "timeline": timeline[:limit]
    }

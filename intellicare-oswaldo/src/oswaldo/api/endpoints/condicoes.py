"""
CRUD endpoints para CondicaoCronica.

Endpoints:
- GET /api/v1/oswaldo/paciente/{cpf_hash}/condicoes
- POST /api/v1/oswaldo/condicoes
- GET /api/v1/oswaldo/condicoes/{id}
- PUT /api/v1/oswaldo/condicoes/{id}
- DELETE /api/v1/oswaldo/condicoes/{id}
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from datetime import date

from src.oswaldo.models.oswaldo_models import CondicaoCronica
from src.oswaldo.schemas.oswaldo_schemas import (
    CondicaoCronicaCreate,
    CondicaoCronicaUpdate,
    CondicaoCronicaResponse,
    CondicoesListResponse,
)
from src.oswaldo.database.session import get_db

router = APIRouter()


@router.get(
    "/paciente/{paciente_cpf_hash}/condicoes",
    response_model=CondicoesListResponse,
    tags=["condicoes"],
    summary="Listar condições de um paciente"
)
def listar_condicoes_paciente(
    paciente_cpf_hash: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    Listar todas as condições crônicas de um paciente.
    
    Filtro por status opcional:
    - PENDENTE_VALIDACAO
    - CONFIRMADO
    - REVISADO
    - SUSPENSO
    - ENCERRADO
    """
    query = db.query(CondicaoCronica).filter(
        CondicaoCronica.paciente_cpf_hash == paciente_cpf_hash
    )
    
    if status:
        query = query.filter(CondicaoCronica.status == status)
    
    total = query.count()
    items = query.order_by(desc(CondicaoCronica.criado_em)).offset(skip).limit(limit).all()
    
    return CondicoesListResponse(total=total, items=items)


@router.post(
    "/condicoes",
    response_model=CondicaoCronicaResponse,
    status_code=201,
    tags=["condicoes"],
    summary="Criar nova condição crônica"
)
def criar_condicao(
    paciente_cpf_hash: str,
    condicao: CondicaoCronicaCreate,
    db: Session = Depends(get_db),
):
    """
    Criar nova condição crônica para um paciente.
    
    Status inicial: PENDENTE_VALIDACAO (se não confirmada por exames)
    Status inicial: CONFIRMADO (se confirmada por exames)
    """
    # Verificar se já existe uma condição ativa com este CID
    existing = db.query(CondicaoCronica).filter(
        CondicaoCronica.paciente_cpf_hash == paciente_cpf_hash,
        CondicaoCronica.cid10 == condicao.cid10,
        CondicaoCronica.status != "ENCERRADO"
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Paciente já possui registro ativo de {condicao.cid10}"
        )
    
    # Criar nova condição
    db_condicao = CondicaoCronica(
        paciente_cpf_hash=paciente_cpf_hash,
        cid10=condicao.cid10,
        data_diagnostico=date.today(),
        medico_diagnosticador=condicao.medico_diagnosticador,
        confirmacao_exames=condicao.confirmacao_exames,
        status="CONFIRMADO" if condicao.confirmacao_exames else "PENDENTE_VALIDACAO",
        gravidade_inicial=condicao.gravidade_inicial
    )
    
    db.add(db_condicao)
    db.commit()
    db.refresh(db_condicao)
    
    return db_condicao


@router.get(
    "/condicoes/{condicao_id}",
    response_model=CondicaoCronicaResponse,
    tags=["condicoes"],
    summary="Obter detalhes de uma condição"
)
def obter_condicao(
    condicao_id: int,
    db: Session = Depends(get_db),
):
    """
    Obter detalhes completos de uma condição crônica.
    """
    condicao = db.query(CondicaoCronica).filter(
        CondicaoCronica.id == condicao_id
    ).first()
    
    if not condicao:
        raise HTTPException(
            status_code=404,
            detail=f"Condição {condicao_id} não encontrada"
        )
    
    return condicao


@router.put(
    "/condicoes/{condicao_id}",
    response_model=CondicaoCronicaResponse,
    tags=["condicoes"],
    summary="Atualizar condição crônica"
)
def atualizar_condicao(
    condicao_id: int,
    update: CondicaoCronicaUpdate,
    db: Session = Depends(get_db),
):
    """
    Atualizar status ou gravidade de uma condição.
    
    Transições de status permitidas:
    - PENDENTE_VALIDACAO → CONFIRMADO (após médico validar)
    - CONFIRMADO → REVISADO (reclassificação)
    - CONFIRMADO → SUSPENSO (temporariamente)
    - CONFIRMADO/REVISADO → ENCERRADO (resolvida)
    """
    condicao = db.query(CondicaoCronica).filter(
        CondicaoCronica.id == condicao_id
    ).first()
    
    if not condicao:
        raise HTTPException(
            status_code=404,
            detail=f"Condição {condicao_id} não encontrada"
        )
    
    # Validar transição de status
    if update.status:
        valid_transitions = {
            "PENDENTE_VALIDACAO": ["CONFIRMADO", "CANCELADO"],
            "CONFIRMADO": ["REVISADO", "SUSPENSO", "ENCERRADO"],
            "REVISADO": ["CONFIRMADO", "SUSPENSO", "ENCERRADO"],
            "SUSPENSO": ["CONFIRMADO", "ENCERRADO"],
            "ENCERRADO": [],
        }
        
        allowed = valid_transitions.get(condicao.status, [])
        if update.status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Transição inválida: {condicao.status} → {update.status}"
            )
        
        condicao.status = update.status
    
    if update.gravidade_inicial:
        condicao.gravidade_inicial = update.gravidade_inicial
    
    db.commit()
    db.refresh(condicao)
    
    return condicao


@router.delete(
    "/condicoes/{condicao_id}",
    tags=["condicoes"],
    summary="Soft-delete (encerrar) condição"
)
def deletar_condicao(
    condicao_id: int,
    db: Session = Depends(get_db),
):
    """
    Soft-delete: marca condição como ENCERRADO em vez de deletar.
    """
    condicao = db.query(CondicaoCronica).filter(
        CondicaoCronica.id == condicao_id
    ).first()
    
    if not condicao:
        raise HTTPException(
            status_code=404,
            detail=f"Condição {condicao_id} não encontrada"
        )
    
    if condicao.status == "ENCERRADO":
        raise HTTPException(
            status_code=400,
            detail="Condição já está encerrada"
        )
    
    condicao.status = "ENCERRADO"
    db.commit()
    
    return {"message": f"Condição {condicao_id} encerrada com sucesso"}

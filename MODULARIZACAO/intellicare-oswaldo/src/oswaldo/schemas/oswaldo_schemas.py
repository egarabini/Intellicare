"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Dict, Optional


# ========================================================================
# CondicaoCronica Schemas
# ========================================================================
class CondicaoCronicaCreate(BaseModel):
    """Schema para criar nova condição crônica."""
    cid10: str = Field(..., description="Código CID-10 da doença")
    medico_diagnosticador: str = Field(..., description="Nome do médico que diagnosticou")
    confirmacao_exames: bool = Field(False, description="Se tem exames confirmando")
    gravidade_inicial: str = Field("MODERADA", description="LEVE, MODERADA, GRAVE")


class CondicaoCronicaUpdate(BaseModel):
    """Schema para atualizar condição."""
    status: Optional[str] = Field(None, description="Novo status")
    gravidade_inicial: Optional[str] = Field(None, description="Nova gravidade")


class CondicaoCronicaResponse(BaseModel):
    """Schema de resposta para condição crônica."""
    id: int
    paciente_cpf_hash: str
    cid10: str
    data_diagnostico: date
    status: str
    gravidade_inicial: Optional[str] = None
    criado_em: datetime
    atualizado_em: datetime
    
    class Config:
        from_attributes = True


class CondicoesListResponse(BaseModel):
    """Response model for list of condicoes."""
    total: int
    items: List[CondicaoCronicaResponse]


# ========================================================================
# Estadiamento Schemas
# ========================================================================
class EstadiamentoCreate(BaseModel):
    """Schema para criar novo estadiamento."""
    condicao_cronica_id: int
    sistema_classificacao: str = Field(..., description="NYHA, KDIGO, SBC, ADA, etc")
    estagio: str = Field(..., description="I, II, III, G1-G5, etc")
    criterios: Optional[Dict] = Field(None, description="Critérios que levaram a classificação")


class EstadiamentoResponse(BaseModel):
    """Schema de resposta para estadiamento."""
    id: int
    condicao_cronica_id: int
    sistema_classificacao: str
    estagio: str
    data_classificacao: datetime
    criterios: Optional[Dict] = None
    
    class Config:
        from_attributes = True


# ========================================================================
# PlanoCuidado Schemas
# ========================================================================
class PlanoCuidadoCreate(BaseModel):
    """Schema para criar plano de cuidado."""
    condicao_cronica_id: int
    data_inicio: date
    objetivos: List[Dict] = Field(..., description="Objetivos SMART")
    intervencoes: List[Dict] = Field(..., description="Intervenções terapêuticas")
    medicamentos: List[Dict] = Field(..., description="Medicamentos prescritos")
    educacao_saude: Optional[List[Dict]] = None


class PlanoCuidadoResponse(BaseModel):
    """Schema de resposta para plano de cuidado."""
    id: int
    condicao_cronica_id: int
    data_inicio: date
    data_revisao: Optional[date] = None
    status: str
    objetivos: List[Dict]
    intervencoes: List[Dict]
    medicamentos: List[Dict]
    
    class Config:
        from_attributes = True


# ========================================================================
# Acompanhamento Schemas
# ========================================================================
class AcompanhamentoCreate(BaseModel):
    """Schema para criar novo acompanhamento."""
    condicao_cronica_id: int
    data_acompanhamento: Optional[datetime] = None
    medico_responsavel: str
    pa_sist: Optional[int] = None
    pa_diast: Optional[int] = None
    glicemia_jejum: Optional[float] = None
    hba1c: Optional[float] = None
    creatinina: Optional[float] = None
    tfge: Optional[float] = None
    colesterol_total: Optional[float] = None
    ldl: Optional[float] = None
    hdl: Optional[float] = None
    triglicerideos: Optional[float] = None
    notas_clinicas: Optional[str] = None
    aderencia_medicacao: Optional[int] = Field(None, ge=0, le=100, description="0-100%")
    intercorrencias: Optional[str] = None


class AcompanhamentoResponse(BaseModel):
    """Schema de resposta para acompanhamento."""
    id: int
    paciente_cpf_hash: str
    condicao_cronica_id: int
    data_acompanhamento: datetime
    medico_id: str
    pressao_arterial: Optional[str] = None
    peso_kg: Optional[float] = None
    glicemia: Optional[float] = None
    temperatura: Optional[float] = None
    adesao_medicamentos: Optional[str] = None
    observacoes: Optional[str] = None
    medicamentos_vigentes: Optional[Dict] = None
    proxima_consulta: Optional[date] = None
    criado_em: datetime
    atualizado_em: datetime
    
    class Config:
        from_attributes = True


class AcompanhamentosListResponse(BaseModel):
    """Response model for list of acompanhamentos."""
    total: int
    items: List[AcompanhamentoResponse]


# ========================================================================
# Alerta Schemas
# ========================================================================
class AlertaCreate(BaseModel):
    """Schema para criar novo alerta."""
    condicao_cronica_id: int
    tipo_alerta: str = Field(..., description="DESCONTROLE, PIORA_PROGRESSIVA, ALERGICO, OUTRO")
    severidade: str = Field(..., description="BAIXA, MEDIA, ALTA, CRITICA")
    descricao: str
    dados_alerta: Optional[Dict] = None


class AlertaResponse(BaseModel):
    """Schema de resposta para alerta."""
    id: int
    paciente_cpf_hash: str
    condicao_cronica_id: int
    tipo_alerta: str
    severidade: str
    descricao: str
    status: str
    data_criacao: datetime
    medico_atribuido: Optional[str] = None
    
    class Config:
        from_attributes = True


class AlertasListResponse(BaseModel):
    """Response model for list of alertas."""
    total: int
    items: List[AlertaResponse]


# ========================================================================
# List Responses
# ========================================================================
class CondicoesListResponse(BaseModel):
    """Response para listar condições."""
    total: int
    items: List[CondicaoCronicaResponse]


class AcompanhamentosListResponse(BaseModel):
    """Response para listar acompanhamentos."""
    total: int
    items: List[AcompanhamentoResponse]


class AlertasListResponse(BaseModel):
    """Response para listar alertas."""
    total: int
    items: List[AlertaResponse]

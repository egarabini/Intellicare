from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProtocolStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVAL = "approval"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class ProtocolMetadata(BaseModel):
    id: str = Field(..., description="Identificador único do protocolo")
    version: str = Field(..., description="Versão semântica (ex: 2.1.0)")
    title: str = Field(..., description="Título do protocolo")
    specialty: str = Field(..., description="Especialidade médica")
    condition: Optional[str] = Field(None, description="Condição clínica (ex: ckd, ic, dm2)")
    status: ProtocolStatus = Field(default=ProtocolStatus.DRAFT)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    author: str = Field(..., description="Autor do protocolo")
    author_email: Optional[str] = None
    reviewer: Optional[str] = Field(None, description="Revisor técnico")
    approver: Optional[str] = Field(None, description="Aprovador institucional")
    approved_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list, description="Referências bibliográficas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "proto-drc-kdigo-001",
                "version": "2.1.0",
                "title": "Protocolo DRC - Diretrizes KDIGO 2024",
                "specialty": "nefrologia",
                "condition": "ckd",
                "status": "published",
                "author": "Comissão de Nefrologia",
                "tags": ["drcronica", "kdigo", "nefrologia"],
                "keywords": ["DRC", "eGFR", "albuminúria", "estadiamento"]
            }
        }


class ProtocolSection(BaseModel):
    title: str = Field(..., description="Título da seção")
    content: str = Field(..., description="Conteúdo em Markdown")
    order: int = Field(default=0, description="Ordem de exibição")
    subsections: List['ProtocolSection'] = Field(default_factory=list)


class ProtocolCriteria(BaseModel):
    name: str = Field(..., description="Nome do critério")
    description: str = Field(..., description="Descrição detalhada")
    condition: str = Field(..., description="Condição lógica (ex: 'eGFR < 60')")
    action: Optional[str] = Field(None, description="Ação recomendada")


class ProtocolIntervention(BaseModel):
    code: str = Field(..., description="Código da intervenção")
    name: str = Field(..., description="Nome da intervenção")
    description: str = Field(..., description="Descrição detalhada")
    indication: str = Field(..., description="Quando indicar")
    contraindication: Optional[str] = Field(None, description="Contraindicações")
    dosage: Optional[str] = Field(None, description="Posologia")
    monitoring: Optional[str] = Field(None, description="Monitoramento necessário")


class Protocol(BaseModel):
    metadata: ProtocolMetadata
    summary: str = Field(..., description="Resumo executivo do protocolo")
    sections: List[ProtocolSection] = Field(default_factory=list)
    criteria: List[ProtocolCriteria] = Field(default_factory=list, description="Critérios de decisão")
    interventions: List[ProtocolIntervention] = Field(default_factory=list)
    pathways: Optional[Dict[str, Any]] = Field(None, description="Fluxos e pathways")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "id": "proto-drc-kdigo-001",
                    "version": "2.1.0",
                    "title": "Protocolo DRC - Diretrizes KDIGO 2024",
                    "specialty": "nefrologia",
                    "condition": "ckd",
                    "status": "published",
                    "author": "Comissão de Nefrologia"
                },
                "summary": "Protocolo baseado nas diretrizes KDIGO 2024 para classificação e manejo da DRC",
                "sections": [
                    {
                        "title": "Classificação KDIGO",
                        "content": "Estadiamento baseado em eGFR e albuminúria...",
                        "order": 1
                    }
                ],
                "criteria": [
                    {
                        "name": "Critério G3a",
                        "description": "eGFR entre 45-59",
                        "condition": "eGFR >= 45 AND eGFR < 60",
                        "action": "Monitoramento semestral"
                    }
                ]
            }
        }


class ProtocolVersion(BaseModel):
    protocol_id: str
    version: str
    created_at: datetime
    author: str
    changelog: str = Field(..., description="Descrição das mudanças")
    protocol_data: Protocol


class ProtocolSearchRequest(BaseModel):
    query: str = Field(..., description="Texto de busca")
    specialty: Optional[str] = None
    condition: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    status: Optional[ProtocolStatus] = None
    limit: int = Field(default=10, ge=1, le=100)


class ProtocolSearchResult(BaseModel):
    protocol: Protocol
    score: float = Field(..., description="Relevância da busca (0-1)")
    highlights: List[str] = Field(default_factory=list, description="Trechos relevantes")

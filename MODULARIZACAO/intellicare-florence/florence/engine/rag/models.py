"""Modelos de dados para RAG."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Protocol(BaseModel):
    """Protocolo clínico."""

    id: str = Field(..., description="ID único do protocolo")
    title: str = Field(..., description="Título do protocolo")
    specialty: str = Field(..., description="Especialidade médica")
    version: str = Field(default="1.0", description="Versão do protocolo")
    date: datetime = Field(default_factory=datetime.now, description="Data de criação")
    source: str | None = Field(None, description="Fonte/referência")
    content: str = Field(..., description="Conteúdo completo do protocolo")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais")


class ProtocolChunk(BaseModel):
    """Chunk de protocolo para indexação."""

    protocol_id: str
    chunk_id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGQuery(BaseModel):
    """Query para busca de protocolos."""

    query: str = Field(..., description="Texto da consulta")
    top_k: int = Field(default=3, ge=1, le=10, description="Número de resultados")
    filters: dict[str, Any] = Field(default_factory=dict, description="Filtros de busca")


class RAGResult(BaseModel):
    """Resultado de busca RAG."""

    protocol_id: str
    title: str
    content: str
    score: float = Field(..., ge=0.0, le=1.0, description="Score de relevância")
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGQueryResponse(BaseModel):
    """Resposta de query RAG."""

    query: str
    results: list[RAGResult]
    total_results: int
    execution_time_ms: float


"""
Contratos obrigatorios para todos os modulos.
Esta camada nao importa de db, auth, vector ou module_loader.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class TenantContext:
    """Contexto imutavel de um request autenticado."""

    tenant_id: str
    schema: str
    user_id: str
    roles: list[str] = field(default_factory=list)
    email: str = ""

    @classmethod
    def from_slug(
        cls,
        slug: str,
        user_id: str,
        roles: list[str] | None = None,
        email: str = "",
    ) -> "TenantContext":
        return cls(
            tenant_id=slug,
            schema=f"tenant_{slug}",
            user_id=user_id,
            roles=roles or [],
            email=email,
        )

    def has_role(self, role: str) -> bool:
        return role in self.roles


class HealthResponse(BaseModel):
    status: str
    module: str
    version: str
    db: str = "unknown"
    uptime_seconds: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)


class ModuleInfo(BaseModel):
    name: str
    version: str
    description: str
    phase: str
    enabled_for_roles: list[str]


class BaseModule(ABC):
    """Interface obrigatoria de todo modulo IntelliCare."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome unico do modulo."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Versao semantica do modulo."""

    @abstractmethod
    def get_router(self) -> APIRouter:
        """Retorna o APIRouter do modulo."""

    @abstractmethod
    async def health(self) -> HealthResponse:
        """Retorna o estado de saude do modulo."""

    def get_info(self) -> ModuleInfo:
        return ModuleInfo(
            name=self.name,
            version=self.version,
            description=f"Modulo {self.name}",
            phase="1",
            enabled_for_roles=[],
        )

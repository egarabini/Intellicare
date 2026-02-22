"""Modelos de dados para sincronização de usuários."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class UserSyncStatus(str, Enum):
    """Status de sincronização de usuário."""
    
    SYNCED = "synced"       # Sincronizado com sucesso
    PENDING = "pending"     # Aguardando sincronização
    ERROR = "error"         # Erro na sincronização
    DISABLED = "disabled"   # Usuário desabilitado


class UserSyncRecord(BaseModel):
    """Registro de sincronização de usuário Keycloak → Rocket.Chat."""
    
    id: UUID = Field(default_factory=uuid4, description="ID do registro")
    
    # Keycloak
    keycloak_user_id: str = Field(..., description="UUID do usuário no Keycloak")
    username: str = Field(..., description="Username único")
    email: str = Field(..., description="Email do usuário")
    full_name: str = Field(..., description="Nome completo")
    roles: list[str] = Field(default_factory=list, description="Roles do Keycloak")
    team_id: str | None = Field(None, description="ID da equipe/unidade")
    
    # Rocket.Chat
    rocketchat_user_id: str | None = Field(None, description="ID do usuário no RC (_id)")
    rc_channels: list[str] = Field(default_factory=list, description="Canais RC em que está")
    rc_active: bool = Field(True, description="Conta RC ativa?")
    
    # Status de sync
    sync_status: UserSyncStatus = Field(
        UserSyncStatus.PENDING,
        description="Status da sincronização"
    )
    last_synced_at: datetime | None = Field(None, description="Última sincronização")
    last_error: str | None = Field(None, description="Última mensagem de erro")
    sync_attempts: int = Field(0, description="Número de tentativas de sync")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Data de criação")
    updated_at: datetime = Field(default_factory=datetime.now, description="Última atualização")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "keycloak_user_id": "abc123-def456",
                "username": "joao.silva",
                "email": "joao.silva@example.com",
                "full_name": "João Silva",
                "roles": ["doctor", "user"],
                "team_id": "ubs-centro",
                "rocketchat_user_id": "rc-xyz789",
                "rc_channels": ["#equipe-ubs-centro", "#alertas-clinicos"],
                "rc_active": True,
                "sync_status": "synced",
                "last_synced_at": "2026-02-17T10:30:00Z",
                "sync_attempts": 1,
            }
        }


class KeycloakUser(BaseModel):
    """Usuário do Keycloak (simplificado)."""
    
    id: str = Field(..., description="UUID do usuário")
    username: str = Field(..., description="Username")
    email: str | None = Field(None, description="Email")
    first_name: str | None = Field(None, description="Primeiro nome")
    last_name: str | None = Field(None, description="Sobrenome")
    enabled: bool = Field(True, description="Conta habilitada?")
    email_verified: bool = Field(False, description="Email verificado?")
    attributes: dict[str, list[str]] = Field(default_factory=dict, description="Atributos customizados")
    realm_roles: list[str] = Field(default_factory=list, description="Roles do realm")
    
    @property
    def full_name(self) -> str:
        """Retorna nome completo."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc123-def456",
                "username": "joao.silva",
                "email": "joao.silva@example.com",
                "first_name": "João",
                "last_name": "Silva",
                "enabled": True,
                "email_verified": True,
                "attributes": {"team_id": ["ubs-centro"]},
                "realm_roles": ["doctor", "user"],
            }
        }


class KeycloakEvent(BaseModel):
    """Evento do Keycloak (webhook)."""
    
    type: str = Field(..., description="Tipo do evento (REGISTER, UPDATE, DELETE)")
    realm_id: str = Field(..., description="ID do realm")
    user_id: str = Field(..., description="ID do usuário")
    timestamp: int = Field(..., description="Timestamp Unix (ms)")
    details: dict[str, str] = Field(default_factory=dict, description="Detalhes do evento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "REGISTER",
                "realm_id": "bemcuidar",
                "user_id": "abc123-def456",
                "timestamp": 1708167000000,
                "details": {"username": "joao.silva", "email": "joao.silva@example.com"},
            }
        }


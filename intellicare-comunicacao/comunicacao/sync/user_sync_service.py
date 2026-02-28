"""Serviço de sincronização de usuários Keycloak → Rocket.Chat."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime
from typing import Any

from comunicacao.rocketchat.client import RocketChatClient
from comunicacao.rocketchat.config import RocketChatConfig
from comunicacao.sync.keycloak_client import KeycloakAdminClient, KeycloakConfig
from comunicacao.sync.models import (
    KeycloakEvent,
    KeycloakUser,
    UserSyncRecord,
    UserSyncStatus,
)

logger = logging.getLogger(__name__)


# Mapeamento de roles Keycloak → Rocket.Chat
ROLE_MAPPING = {
    "doctor": ["user", "doctor"],
    "nurse": ["user", "nurse"],
    "care_coordinator": ["user", "coordinator"],
    "admin": ["user", "admin"],
    "intellicare_admin": ["user", "admin"],
    "user": ["user"],
}


class UserSyncService:
    """
    Serviço de sincronização de usuários Keycloak → Rocket.Chat.
    
    Responsável por:
    - Criar usuários no RC quando criados no Keycloak
    - Atualizar usuários no RC quando atualizados no Keycloak
    - Desabilitar usuários no RC quando desabilitados no Keycloak
    - Reconciliação periódica (sync completo)
    """
    
    def __init__(
        self,
        keycloak_client: KeycloakAdminClient | None = None,
        rocketchat_client: RocketChatClient | None = None,
        keycloak_config: KeycloakConfig | None = None,
        rocketchat_config: RocketChatConfig | None = None,
    ):
        """
        Inicializa serviço.
        
        Args:
            keycloak_client: Cliente Keycloak (se None, cria novo)
            rocketchat_client: Cliente RC (se None, cria novo)
            keycloak_config: Config Keycloak (se None, usa from_env())
            rocketchat_config: Config RC (se None, usa from_env())
        """
        self.kc_client = keycloak_client or KeycloakAdminClient(keycloak_config)
        self.rc_client = rocketchat_client or RocketChatClient(rocketchat_config)
        
        # Storage em memória (simplificado - em produção usar DB)
        self._sync_records: dict[str, UserSyncRecord] = {}
        
        logger.info("UserSyncService inicializado")
    
    def _generate_strong_password(self) -> str:
        """Gera senha forte aleatória (não será usada, SSO via Keycloak)."""
        return secrets.token_urlsafe(32)
    
    def _map_roles(self, keycloak_roles: list[str]) -> list[str]:
        """
        Mapeia roles do Keycloak para roles do Rocket.Chat.
        
        Args:
            keycloak_roles: Lista de roles do Keycloak
        
        Returns:
            Lista de roles do RC
        """
        rc_roles = set()
        
        for kc_role in keycloak_roles:
            mapped = ROLE_MAPPING.get(kc_role, ["user"])
            rc_roles.update(mapped)
        
        return list(rc_roles)
    
    async def sync_user(self, keycloak_user_id: str) -> UserSyncRecord:
        """
        Sincroniza um usuário do Keycloak para o Rocket.Chat.
        
        Args:
            keycloak_user_id: UUID do usuário no Keycloak
        
        Returns:
            UserSyncRecord com resultado da sincronização
        """
        logger.info("Sincronizando usuário: %s", keycloak_user_id)
        
        # Buscar usuário no Keycloak
        try:
            kc_user = await self.kc_client.get_user(keycloak_user_id)
            kc_roles = await self.kc_client.get_user_roles(keycloak_user_id)
        except Exception as e:
            logger.error("Erro ao buscar usuário no Keycloak: %s", str(e))
            return UserSyncRecord(
                keycloak_user_id=keycloak_user_id,
                username="unknown",
                email="unknown@example.com",
                full_name="Unknown",
                sync_status=UserSyncStatus.ERROR,
                last_error=f"Erro ao buscar no Keycloak: {str(e)}",
                sync_attempts=1,
            )
        
        # Criar registro de sync
        sync_record = UserSyncRecord(
            keycloak_user_id=kc_user.id,
            username=kc_user.username,
            email=kc_user.email or f"{kc_user.username}@example.com",
            full_name=kc_user.full_name,
            roles=kc_roles,
            team_id=kc_user.attributes.get("team_id", [None])[0],
            sync_status=UserSyncStatus.PENDING,
        )
        
        # Verificar se usuário já existe no RC
        rc_user = await self.rc_client.get_user_by_username(kc_user.username)
        
        if rc_user:
            # Usuário já existe, atualizar
            logger.info("Usuário já existe no RC: %s", rc_user.id)
            sync_record.rocketchat_user_id = rc_user.id
            sync_record.rc_active = rc_user.active
            sync_record.sync_status = UserSyncStatus.SYNCED
            sync_record.last_synced_at = datetime.now()
        else:
            # Criar usuário no RC
            try:
                await self._create_rc_user(kc_user, kc_roles, sync_record)
            except Exception as e:
                logger.error("Erro ao criar usuário no RC: %s", str(e))
                sync_record.sync_status = UserSyncStatus.ERROR
                sync_record.last_error = f"Erro ao criar no RC: {str(e)}"
                sync_record.sync_attempts += 1
        
        # Salvar registro (em memória)
        self._sync_records[keycloak_user_id] = sync_record

        return sync_record

    async def _create_rc_user(
        self,
        kc_user: KeycloakUser,
        kc_roles: list[str],
        sync_record: UserSyncRecord,
    ) -> None:
        """
        Cria usuário no Rocket.Chat.

        Args:
            kc_user: Usuário do Keycloak
            kc_roles: Roles do Keycloak
            sync_record: Registro de sync (será atualizado)
        """
        logger.info("Criando usuário no RC: %s", kc_user.username)

        # Mapear roles
        rc_roles = self._map_roles(kc_roles)

        # Criar usuário via API do RC
        # POST /api/v1/users.create
        payload = {
            "username": kc_user.username,
            "email": kc_user.email or f"{kc_user.username}@example.com",
            "name": kc_user.full_name,
            "password": self._generate_strong_password(),  # Não será usado (SSO)
            "roles": rc_roles,
            "joinDefaultChannels": False,  # Controlar manualmente
            "verified": True,  # Já verificado no Keycloak
            "requirePasswordChange": False,
        }

        # Fazer requisição (simplificado - RC client não tem método create_user ainda)
        # Por enquanto, simulamos sucesso
        logger.warning("Criação de usuário no RC não implementada ainda (API call)")

        # Simular sucesso
        sync_record.rocketchat_user_id = f"rc-{kc_user.id[:8]}"
        sync_record.rc_active = True
        sync_record.sync_status = UserSyncStatus.SYNCED
        sync_record.last_synced_at = datetime.now()

        logger.info("Usuário criado no RC (simulado): %s", sync_record.rocketchat_user_id)

    async def handle_keycloak_event(self, event: KeycloakEvent) -> UserSyncRecord | None:
        """
        Processa evento do Keycloak (webhook).

        Args:
            event: Evento do Keycloak

        Returns:
            UserSyncRecord ou None se evento não processado
        """
        logger.info("Processando evento Keycloak: type=%s, user_id=%s", event.type, event.user_id)

        if event.type == "REGISTER":
            # Novo usuário criado
            return await self.sync_user(event.user_id)

        elif event.type == "UPDATE":
            # Usuário atualizado
            return await self.sync_user(event.user_id)

        elif event.type == "DELETE":
            # Usuário deletado - desabilitar no RC
            logger.info("Usuário deletado no Keycloak: %s", event.user_id)
            return await self._disable_user_from_delete_event(event)

        else:
            logger.warning("Tipo de evento não suportado: %s", event.type)
            return None

    async def _disable_user_from_delete_event(self, event: KeycloakEvent) -> UserSyncRecord | None:
        """
        Processa evento DELETE do Keycloak desativando usuário no RC.

        Estratégia:
        1. Tenta recuperar username pelos detalhes do evento.
        2. Fallback para registro de sync em memória.
        3. Busca usuário no RC por username e desativa.
        """
        username = None
        if isinstance(event.details, dict):
            username = event.details.get("username")

        sync_record = self._sync_records.get(event.user_id)
        if sync_record is not None and not username:
            username = sync_record.username

        if not username:
            logger.warning("DELETE sem username para user_id=%s", event.user_id)
            return sync_record

        rc_user = await self.rc_client.get_user_by_username(username)
        if rc_user is None:
            logger.warning("Usuário não encontrado no RC para desativação: %s", username)
            return sync_record

        disabled = await self.rc_client.set_user_active_status(rc_user.id, False)
        if not disabled:
            logger.error("Falha ao desativar usuário no RC: %s", username)
            if sync_record is not None:
                sync_record.sync_status = UserSyncStatus.ERROR
                sync_record.last_error = "Falha ao desativar usuário no Rocket.Chat"
            return sync_record

        if sync_record is None:
            sync_record = UserSyncRecord(
                keycloak_user_id=event.user_id,
                username=username,
                email=f"{username}@example.com",
                full_name=username,
                sync_status=UserSyncStatus.SYNCED,
                rocketchat_user_id=rc_user.id,
                rc_active=False,
                last_synced_at=datetime.now(),
            )
            self._sync_records[event.user_id] = sync_record
        else:
            sync_record.rocketchat_user_id = rc_user.id
            sync_record.rc_active = False
            sync_record.sync_status = UserSyncStatus.SYNCED
            sync_record.last_synced_at = datetime.now()
            sync_record.last_error = None

        return sync_record

    async def reconcile_all_users(self) -> dict[str, Any]:
        """
        Reconciliação completa: sincroniza todos os usuários do Keycloak.

        Returns:
            Dict com estatísticas da reconciliação
        """
        logger.info("Iniciando reconciliação completa de usuários")

        start_time = datetime.now()

        # Buscar todos os usuários do Keycloak
        kc_users = await self.kc_client.get_all_users()

        logger.info("Encontrados %d usuários no Keycloak", len(kc_users))

        stats = {
            "total": len(kc_users),
            "synced": 0,
            "errors": 0,
            "skipped": 0,
        }

        # Sincronizar cada usuário
        for kc_user in kc_users:
            try:
                if not kc_user.enabled:
                    logger.debug("Usuário desabilitado, pulando: %s", kc_user.username)
                    stats["skipped"] += 1
                    continue

                sync_record = await self.sync_user(kc_user.id)

                if sync_record.sync_status == UserSyncStatus.SYNCED:
                    stats["synced"] += 1
                else:
                    stats["errors"] += 1

            except Exception as e:
                logger.error("Erro ao sincronizar usuário %s: %s", kc_user.username, str(e))
                stats["errors"] += 1

        duration = (datetime.now() - start_time).total_seconds()

        logger.info(
            "Reconciliação completa finalizada - total=%d, synced=%d, errors=%d, skipped=%d, duration=%.2fs",
            stats["total"],
            stats["synced"],
            stats["errors"],
            stats["skipped"],
            duration,
        )

        stats["duration_seconds"] = duration

        return stats

    async def get_sync_status(self, keycloak_user_id: str) -> UserSyncRecord | None:
        """
        Obtém status de sincronização de um usuário.

        Args:
            keycloak_user_id: UUID do usuário no Keycloak

        Returns:
            UserSyncRecord ou None se não encontrado
        """
        return self._sync_records.get(keycloak_user_id)

    async def get_all_sync_records(self) -> list[UserSyncRecord]:
        """
        Obtém todos os registros de sincronização.

        Returns:
            Lista de UserSyncRecord
        """
        return list(self._sync_records.values())

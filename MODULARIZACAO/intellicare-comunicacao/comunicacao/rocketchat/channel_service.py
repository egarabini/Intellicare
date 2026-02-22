"""Serviço de gerenciamento de canais do Rocket.Chat."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from comunicacao.rocketchat.client import RocketChatClient
from comunicacao.rocketchat.config import RocketChatConfig
from comunicacao.rocketchat.models import RCChannel

logger = logging.getLogger(__name__)


class ChannelType(str, Enum):
    """Tipos de canais IntelliCare."""
    
    CASE = "case"           # Canal de caso clínico (caso-{patient_id})
    TEAM = "team"           # Canal de equipe (equipe-{team_id})
    ALERT = "alert"         # Canal de alertas (alertas-clinicos)
    TELECONSULT = "teleconsult"  # Canal de teleconsultas
    QUALITY = "quality"     # Canal de qualidade
    CUSTOM = "custom"       # Canal customizado


class RocketChatChannelService:
    """
    Serviço para gerenciamento de canais do Rocket.Chat.
    
    Responsável por:
    - Criar canais com naming conventions
    - Adicionar/remover membros
    - Arquivar canais
    - Configurar tópicos e descrições
    """
    
    def __init__(
        self,
        client: RocketChatClient | None = None,
        config: RocketChatConfig | None = None,
    ):
        """
        Inicializa serviço.
        
        Args:
            client: Cliente RC (se None, cria novo)
            config: Configuração RC (se None, usa from_env())
        """
        if config is None:
            config = RocketChatConfig.from_env()
        
        self.config = config
        self.client = client or RocketChatClient(config)
        self.rc_client = self.client  # compatibilidade com testes/integrações legadas
        
        logger.info("RocketChatChannelService inicializado")
    
    def _generate_channel_name(
        self,
        channel_type: ChannelType,
        identifier: str | None = None,
    ) -> str:
        """
        Gera nome do canal seguindo naming conventions.
        
        Args:
            channel_type: Tipo do canal
            identifier: Identificador (patient_id, team_id, etc.)
        
        Returns:
            Nome do canal (sem #)
        """
        if channel_type == ChannelType.CASE:
            prefix = self.config.default_case_channel_prefix
            return f"{prefix}{identifier}" if identifier else prefix
        
        elif channel_type == ChannelType.TEAM:
            prefix = self.config.default_team_channel_prefix
            return f"{prefix}{identifier}" if identifier else prefix
        
        elif channel_type == ChannelType.ALERT:
            return self.config.default_alert_channel
        
        elif channel_type == ChannelType.TELECONSULT:
            return "teleconsultas"
        
        elif channel_type == ChannelType.QUALITY:
            return "qualidade"
        
        else:  # CUSTOM
            return identifier or "custom-channel"
    
    async def create_case_channel(
        self,
        patient_id: str,
        patient_name: str | None = None,
        members: list[str] | None = None,
        read_only: bool = False,
    ) -> RCChannel:
        """
        Cria canal privado para caso clínico.
        
        Args:
            patient_id: ID do paciente
            patient_name: Nome do paciente (para tópico)
            members: Lista de usernames para adicionar
            read_only: Canal somente leitura?
        
        Returns:
            RCChannel criado
        """
        channel_name = self._generate_channel_name(ChannelType.CASE, patient_id)
        
        topic = f"Caso clínico - Paciente {patient_name}" if patient_name else f"Caso clínico - {patient_id}"
        
        logger.info("Criando canal de caso: %s", channel_name)
        
        # Criar grupo privado
        channel = await self.client.create_private_group(
            name=channel_name,
            members=members,
            read_only=read_only,
        )
        
        # Atualizar tópico (se necessário, via API adicional)
        # Por enquanto, retornamos o canal criado
        
        logger.info("Canal de caso criado: %s (id=%s)", channel_name, channel.id)
        
        return channel
    
    async def create_team_channel(
        self,
        team_id: str,
        team_name: str | None = None,
        members: list[str] | None = None,
        read_only: bool = False,
    ) -> RCChannel:
        """
        Cria canal privado para equipe.
        
        Args:
            team_id: ID da equipe
            team_name: Nome da equipe (para tópico)
            members: Lista de usernames para adicionar
            read_only: Canal somente leitura?
        
        Returns:
            RCChannel criado
        """
        channel_name = self._generate_channel_name(ChannelType.TEAM, team_id)
        
        topic = f"Equipe {team_name}" if team_name else f"Equipe {team_id}"
        
        logger.info("Criando canal de equipe: %s", channel_name)
        
        channel = await self.client.create_private_group(
            name=channel_name,
            members=members,
            read_only=read_only,
        )
        
        logger.info("Canal de equipe criado: %s (id=%s)", channel_name, channel.id)

        return channel

    async def create_alert_channel(
        self,
        members: list[str] | None = None,
        read_only: bool = False,
    ) -> RCChannel:
        """
        Cria canal de alertas clínicos (se não existir).

        Args:
            members: Lista de usernames para adicionar
            read_only: Canal somente leitura?

        Returns:
            RCChannel criado ou existente
        """
        channel_name = self._generate_channel_name(ChannelType.ALERT)

        logger.info("Criando/verificando canal de alertas: %s", channel_name)

        # Tentar criar canal público
        try:
            channel = await self.client.create_channel(
                name=channel_name,
                members=members,
                read_only=read_only,
            )
            logger.info("Canal de alertas criado: %s (id=%s)", channel_name, channel.id)
            return channel
        except Exception as e:
            # Se já existe, buscar info
            logger.warning("Canal de alertas já existe ou erro ao criar: %s", str(e))
            # Retornar canal existente (simplificado)
            return RCChannel(
                id="",
                name=channel_name,
                type="c",
                topic="Alertas clínicos IntelliCare",
            )

    async def add_member(
        self,
        channel_id: str,
        user_id: str,
        channel_type: str = "p",
    ) -> bool:
        """
        Adiciona membro a um canal.

        Args:
            channel_id: ID do canal
            user_id: ID do usuário
            channel_type: Tipo do canal (c=público, p=privado)

        Returns:
            True se sucesso
        """
        logger.info("Adicionando user=%s ao canal=%s (type=%s)", user_id, channel_id, channel_type)

        try:
            if channel_type == "c":
                await self.client.invite_user_to_channel(channel_id, user_id)
            else:  # p (private group)
                await self.client.invite_user_to_group(channel_id, user_id)

            logger.info("Membro adicionado com sucesso")
            return True
        except Exception as e:
            logger.error("Erro ao adicionar membro: %s", str(e))
            return False

    async def remove_member(
        self,
        channel_id: str,
        user_id: str,
        channel_type: str = "p",
    ) -> bool:
        """
        Remove membro de um canal.

        Args:
            channel_id: ID do canal
            user_id: ID do usuário
            channel_type: Tipo do canal (c=público, p=privado)

        Returns:
            True se sucesso
        """
        logger.info("Removendo user=%s do canal=%s (type=%s)", user_id, channel_id, channel_type)

        # Rocket.Chat API para remover membro
        # POST /api/v1/channels.kick ou /api/v1/groups.kick
        # Por enquanto, retornamos False (não implementado)
        logger.warning("Remoção de membro não implementada ainda")
        return False

    async def archive_channel(
        self,
        channel_id: str,
        channel_type: str = "p",
    ) -> bool:
        """
        Arquiva um canal.

        Args:
            channel_id: ID do canal
            channel_type: Tipo do canal (c=público, p=privado)

        Returns:
            True se sucesso
        """
        logger.info("Arquivando canal=%s (type=%s)", channel_id, channel_type)

        # Rocket.Chat API para arquivar
        # POST /api/v1/channels.archive ou /api/v1/groups.archive
        # Por enquanto, retornamos False (não implementado)
        logger.warning("Arquivamento de canal não implementado ainda")
        return False

    async def get_or_create_case_channel(
        self,
        patient_id: str,
        patient_name: str | None = None,
        members: list[str] | None = None,
    ) -> RCChannel:
        """
        Obtém canal de caso existente ou cria novo.

        Args:
            patient_id: ID do paciente
            patient_name: Nome do paciente
            members: Membros iniciais (se criar)

        Returns:
            RCChannel
        """
        channel_name = self._generate_channel_name(ChannelType.CASE, patient_id)

        logger.info("Buscando ou criando canal de caso: %s", channel_name)

        # Tentar buscar grupo privado existente por nome
        existing = await self.client.get_group_info(channel_name)
        if existing is None:
            groups = await self.client.list_groups()
            existing = next((g for g in groups if g.name == channel_name), None)
        if existing is not None:
            logger.info("Canal de caso já existe: %s (id=%s)", channel_name, existing.id)
            return existing

        return await self.create_case_channel(
            patient_id=patient_id,
            patient_name=patient_name,
            members=members,
        )

    async def get_or_create_team_channel(
        self,
        team_id: str,
        team_name: str | None = None,
        members: list[str] | None = None,
    ) -> RCChannel:
        """
        Obtém canal de equipe existente ou cria novo.

        Args:
            team_id: ID da equipe
            team_name: Nome da equipe
            members: Membros iniciais (se criar)

        Returns:
            RCChannel
        """
        channel_name = self._generate_channel_name(ChannelType.TEAM, team_id)

        logger.info("Buscando ou criando canal de equipe: %s", channel_name)

        # Tentar buscar grupo privado existente por nome
        existing = await self.client.get_group_info(channel_name)
        if existing is None:
            groups = await self.client.list_groups()
            existing = next((g for g in groups if g.name == channel_name), None)
        if existing is not None:
            logger.info("Canal de equipe já existe: %s (id=%s)", channel_name, existing.id)
            return existing

        return await self.create_team_channel(
            team_id=team_id,
            team_name=team_name,
            members=members,
        )

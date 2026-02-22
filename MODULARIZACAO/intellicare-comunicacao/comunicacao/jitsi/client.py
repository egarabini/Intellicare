"""Cliente para interação com Jitsi Meet."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt

from comunicacao.jitsi.config import JitsiConfig
from comunicacao.jitsi.models import JitsiRoom, ParticipantRole, RoomType


class JitsiClient:
    """
    Cliente para criar salas e gerar tokens JWT para Jitsi Meet.
    
    Responsabilidades:
    - Gerar nomes únicos de salas
    - Criar tokens JWT para participantes
    - Validar configuração de salas
    - Gerar URLs de acesso
    """
    
    def __init__(self, config: JitsiConfig):
        """
        Inicializa cliente Jitsi.
        
        Args:
            config: Configuração do Jitsi
        """
        self._config = config
    
    def generate_room_name(self, room_type: RoomType, room_id: str | None = None) -> str:
        """
        Gera nome único para sala.
        
        Formato: intellicare-{type}-{uuid}
        
        Args:
            room_type: Tipo da sala
            room_id: ID da sala (opcional, gera UUID se não fornecido)
        
        Returns:
            Nome único da sala
        
        Examples:
            >>> client.generate_room_name(RoomType.TELECONSULTA)
            'intellicare-teleconsulta-a1b2c3d4'
        """
        if room_id is None:
            room_id = str(uuid4())[:8]
        
        return f"intellicare-{room_type.value}-{room_id}"
    
    def generate_jwt_token(
        self,
        room_name: str,
        user_id: str,
        user_name: str,
        role: ParticipantRole,
        expires_in_minutes: int = 60,
        user_email: str | None = None,
        user_avatar: str | None = None,
    ) -> str:
        """
        Gera token JWT para participante.
        
        O token JWT é usado para autenticar o participante na sala Jitsi.
        
        Args:
            room_name: Nome da sala
            user_id: ID do usuário
            user_name: Nome do usuário
            role: Papel do usuário (moderator, presenter, participant)
            expires_in_minutes: Tempo de expiração do token (minutos)
            user_email: Email do usuário (opcional)
            user_avatar: URL do avatar do usuário (opcional)
        
        Returns:
            Token JWT assinado
        
        Raises:
            ValueError: Se configuração inválida
        """
        now = int(time.time())
        exp = now + (expires_in_minutes * 60)
        
        # Payload JWT conforme especificação Jitsi
        # https://github.com/jitsi/lib-jitsi-meet/blob/master/doc/tokens.md
        payload = {
            # Standard JWT claims
            "iss": self._config.app_id,
            "sub": self._config.base_url,
            "aud": "jitsi",
            "iat": now,
            "nbf": now,
            "exp": exp,
            
            # Jitsi-specific claims
            "room": room_name,
            "context": {
                "user": {
                    "id": user_id,
                    "name": user_name,
                    "email": user_email,
                    "avatar": user_avatar,
                },
            },
        }
        
        # Adicionar moderator flag se necessário
        if role == ParticipantRole.MODERATOR:
            payload["moderator"] = True
        
        # Assinar token com secret
        token = jwt.encode(
            payload,
            self._config.app_secret,
            algorithm="HS256",
        )
        
        return token
    
    def get_room_url(
        self,
        room_name: str,
        jwt_token: str | None = None,
    ) -> str:
        """
        Gera URL completa da sala.
        
        Args:
            room_name: Nome da sala
            jwt_token: Token JWT (opcional, adicionado como query param)
        
        Returns:
            URL completa da sala
        
        Examples:
            >>> client.get_room_url("intellicare-teleconsulta-123")
            'https://meet.gsi.srv.br/intellicare-teleconsulta-123'
            
            >>> client.get_room_url("intellicare-teleconsulta-123", jwt_token="abc123")
            'https://meet.gsi.srv.br/intellicare-teleconsulta-123?jwt=abc123'
        """
        url = self._config.get_room_url(room_name)
        
        if jwt_token:
            url = f"{url}?jwt={jwt_token}"
        
        return url
    
    def validate_room_config(
        self,
        scheduled_start: datetime,
        scheduled_end: datetime,
        max_participants: int,
    ) -> list[str]:
        """
        Valida configuração de sala.
        
        Args:
            scheduled_start: Data/hora de início
            scheduled_end: Data/hora de término
            max_participants: Máximo de participantes
        
        Returns:
            Lista de erros (vazia se válido)
        """
        errors = []
        
        # Validar datas
        if scheduled_start >= scheduled_end:
            errors.append("scheduled_start deve ser anterior a scheduled_end")
        
        if scheduled_start < datetime.utcnow():
            errors.append("scheduled_start não pode ser no passado")
        
        # Validar duração
        duration = (scheduled_end - scheduled_start).total_seconds() / 60
        if duration > 480:  # 8 horas
            errors.append("Duração máxima de sala é 8 horas")
        
        if duration < 5:
            errors.append("Duração mínima de sala é 5 minutos")
        
        # Validar participantes
        if max_participants < 2:
            errors.append("max_participants deve ser >= 2")
        
        if max_participants > self._config.max_participants:
            errors.append(f"max_participants não pode exceder {self._config.max_participants}")
        
        return errors


"""Configuração do Jitsi Meet."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class JitsiConfig:
    """
    Configuração do Jitsi Meet.
    
    Attributes:
        base_url: URL base do Jitsi (ex: https://meet.gsi.srv.br)
        app_id: Application ID para JWT
        app_secret: Secret para assinar JWT
        default_room_duration_minutes: Duração padrão de sala (minutos)
        max_participants: Máximo de participantes por sala
        enable_recording: Habilitar gravação de salas
        enable_lobby: Habilitar sala de espera
        enable_chat: Habilitar chat
        enable_screen_sharing: Habilitar compartilhamento de tela
        moderator_password: Senha para moderadores (opcional)
    """
    
    base_url: str
    app_id: str
    app_secret: str
    default_room_duration_minutes: int = 60
    max_participants: int = 10
    enable_recording: bool = True
    enable_lobby: bool = True
    enable_chat: bool = True
    enable_screen_sharing: bool = True
    moderator_password: str | None = None
    
    @classmethod
    def from_env(cls) -> JitsiConfig:
        """
        Cria configuração a partir de variáveis de ambiente.
        
        Variáveis:
            JITSI_BASE_URL: URL base do Jitsi
            JITSI_APP_ID: Application ID
            JITSI_APP_SECRET: Secret para JWT
            JITSI_DEFAULT_ROOM_DURATION: Duração padrão (minutos)
            JITSI_MAX_PARTICIPANTS: Máximo de participantes
            JITSI_ENABLE_RECORDING: Habilitar gravação (true/false)
            JITSI_ENABLE_LOBBY: Habilitar lobby (true/false)
            JITSI_ENABLE_CHAT: Habilitar chat (true/false)
            JITSI_ENABLE_SCREEN_SHARING: Habilitar screen sharing (true/false)
            JITSI_MODERATOR_PASSWORD: Senha para moderadores (opcional)
        
        Returns:
            JitsiConfig configurado
        """
        return cls(
            base_url=os.getenv("JITSI_BASE_URL", "https://meet.gsi.srv.br"),
            app_id=os.getenv("JITSI_APP_ID", "intellicare"),
            app_secret=os.getenv("JITSI_APP_SECRET", "change-me-in-production"),
            default_room_duration_minutes=int(os.getenv("JITSI_DEFAULT_ROOM_DURATION", "60")),
            max_participants=int(os.getenv("JITSI_MAX_PARTICIPANTS", "10")),
            enable_recording=os.getenv("JITSI_ENABLE_RECORDING", "true").lower() == "true",
            enable_lobby=os.getenv("JITSI_ENABLE_LOBBY", "true").lower() == "true",
            enable_chat=os.getenv("JITSI_ENABLE_CHAT", "true").lower() == "true",
            enable_screen_sharing=os.getenv("JITSI_ENABLE_SCREEN_SHARING", "true").lower() == "true",
            moderator_password=os.getenv("JITSI_MODERATOR_PASSWORD"),
        )
    
    def get_room_url(self, room_name: str) -> str:
        """
        Gera URL completa da sala.
        
        Args:
            room_name: Nome da sala
        
        Returns:
            URL completa (ex: https://meet.gsi.srv.br/intellicare-teleconsulta-123)
        """
        return f"{self.base_url}/{room_name}"
    
    def validate(self) -> list[str]:
        """
        Valida configuração.
        
        Returns:
            Lista de erros (vazia se válido)
        """
        errors = []
        
        if not self.base_url:
            errors.append("JITSI_BASE_URL é obrigatório")
        
        if not self.app_id:
            errors.append("JITSI_APP_ID é obrigatório")
        
        if not self.app_secret or self.app_secret == "change-me-in-production":
            errors.append("JITSI_APP_SECRET deve ser configurado em produção")
        
        if self.default_room_duration_minutes <= 0:
            errors.append("JITSI_DEFAULT_ROOM_DURATION deve ser > 0")
        
        if self.max_participants <= 0:
            errors.append("JITSI_MAX_PARTICIPANTS deve ser > 0")
        
        return errors


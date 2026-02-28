"""HL7v2 API Key Model — Autenticação para sistemas legados hospitalares.

Este modelo armazena API Keys para autenticação de sistemas legados que enviam
mensagens HL7v2. Cada hospital/sistema tem uma API Key única.

Features:
- API Key gerada automaticamente (UUID)
- Expiração configurável
- Rate limiting por key
- Auditoria de uso
- IP whitelist (opcional)
"""

import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from grahame.models.base import Base

if TYPE_CHECKING:
    from grahame.models.hl7v2_audit import HL7v2AuditLog


class HL7v2APIKey(Base):
    """API Key para autenticação HL7v2.
    
    Cada sistema legado (hospital, clínica, etc.) recebe uma API Key única
    para enviar mensagens HL7v2 ao endpoint /hl7v2/adt-a04.
    """
    
    __tablename__ = "hl7v2_api_keys"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # API Key (UUID format)
    api_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="API Key (UUID format) - usado no header X-API-Key"
    )
    
    # Identificação do sistema
    system_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nome do sistema/hospital (ex: 'Hospital São Paulo - Tasy')"
    )
    
    system_identifier: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Identificador único do sistema (ex: 'HSP-TASY')"
    )
    
    # Descrição
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Descrição adicional do sistema"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        comment="Se False, a API Key está desabilitada"
    )
    
    # Expiração
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Data de expiração (None = nunca expira)"
    )
    
    # Rate limiting
    rate_limit_per_minute: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
        comment="Máximo de requisições por minuto (0 = sem limite)"
    )
    
    # IP Whitelist (opcional)
    allowed_ips: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="IPs permitidos (separados por vírgula, ex: '192.168.1.1,10.0.0.1')"
    )
    
    # Auditoria
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Data de criação"
    )
    
    created_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Usuário que criou a API Key"
    )
    
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Última vez que a API Key foi usada"
    )
    
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Número total de requisições feitas com esta API Key"
    )
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notas administrativas"
    )

    audit_logs: Mapped[list["HL7v2AuditLog"]] = relationship(
        "HL7v2AuditLog",
        back_populates="api_key",
        passive_deletes=True,
    )
    
    @classmethod
    def generate_api_key(cls) -> str:
        """Gera uma nova API Key segura.
        
        Returns:
            str: API Key no formato UUID (32 caracteres hex)
        """
        return secrets.token_urlsafe(32)
    
    def is_valid(self) -> bool:
        """Verifica se a API Key é válida.
        
        Returns:
            bool: True se a key está ativa e não expirou
        """
        if not self.is_active:
            return False
        
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        
        return True
    
    def is_ip_allowed(self, ip: str) -> bool:
        """Verifica se o IP está na whitelist.

        Suporta IPs individuais e notação CIDR (ex: 192.168.1.0/24).

        Args:
            ip: Endereço IP do cliente

        Returns:
            bool: True se o IP é permitido (ou se não há whitelist)
        """
        if not self.allowed_ips:
            return True  # Sem whitelist = todos os IPs permitidos

        import ipaddress

        try:
            ip_obj = ipaddress.ip_address(ip)
        except ValueError:
            # IP inválido
            return False

        allowed_list = [entry.strip() for entry in self.allowed_ips.split(",")]

        for entry in allowed_list:
            if not entry:
                continue

            try:
                # Tenta parsear como rede (suporta CIDR)
                network = ipaddress.ip_network(entry, strict=False)
                if ip_obj in network:
                    return True
            except ValueError:
                # Se não for uma rede válida, tenta match exato
                if ip == entry:
                    return True

        return False

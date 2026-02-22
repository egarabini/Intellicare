"""Configuração de conformidade LGPD."""

from __future__ import annotations

import os
from typing import ClassVar

from pydantic import BaseModel, Field


class LGPDConfig(BaseModel):
    """
    Configuração de conformidade LGPD.
    
    Define políticas de consentimento, quiet hours, retenção de dados
    e exceções para alertas críticos conforme Art. 7º, VII LGPD.
    """
    
    # Alertas CRITICAL sempre enviados (Art. 7º, VII - tutela da saúde)
    critical_override_enabled: bool = Field(
        default=True,
        description="Permitir envio de alertas CRITICAL sem consentimento (base legal: tutela da saúde)"
    )
    
    # Alertas HIGH enviados com base legal de proteção à vida
    high_alert_override_enabled: bool = Field(
        default=True,
        description="Permitir envio de alertas HIGH com base legal de proteção à vida"
    )
    
    # Pacientes sem consentimento: bloquear tudo exceto CRITICAL/HIGH
    block_without_consent: bool = Field(
        default=True,
        description="Bloquear comunicações para pacientes sem consentimento (exceto CRITICAL/HIGH)"
    )
    
    # Quiet hours padrão (se paciente não definiu)
    default_quiet_hours_start: str = Field(
        default="22:00",
        description="Horário de início do período silencioso padrão (HH:MM)"
    )
    
    default_quiet_hours_end: str = Field(
        default="07:00",
        description="Horário de fim do período silencioso padrão (HH:MM)"
    )
    
    # Retenção de dados
    audit_retention_years: int = Field(
        default=5,
        description="Retenção de audit trail (anos) - requisito legal mínimo 5 anos"
    )
    
    delivery_retention_days: int = Field(
        default=365,
        description="Retenção de delivery results (dias)"
    )
    
    # Consentimento
    consent_version: str = Field(
        default="1.0",
        description="Versão do termo de consentimento"
    )
    
    consent_renewal_days: int = Field(
        default=365,
        description="Renovação de consentimento (dias) - padrão anual"
    )
    
    # Anonimização
    anonymization_hash_salt: str = Field(
        default="intellicare-lgpd-salt-2026",
        description="Salt para hash de anonimização (deve ser secreto em produção)"
    )
    
    # Exportação FHIR
    fhir_export_enabled: bool = Field(
        default=True,
        description="Habilitar exportação de FHIR Communication para interoperabilidade"
    )
    
    # Configurações de ambiente
    ENV_PREFIX: ClassVar[str] = "LGPD_"
    
    @classmethod
    def from_env(cls) -> LGPDConfig:
        """Cria configuração a partir de variáveis de ambiente."""
        return cls(
            critical_override_enabled=os.getenv("LGPD_CRITICAL_OVERRIDE_ENABLED", "true").lower() == "true",
            high_alert_override_enabled=os.getenv("LGPD_HIGH_ALERT_OVERRIDE_ENABLED", "true").lower() == "true",
            block_without_consent=os.getenv("LGPD_BLOCK_WITHOUT_CONSENT", "true").lower() == "true",
            default_quiet_hours_start=os.getenv("LGPD_DEFAULT_QUIET_HOURS_START", "22:00"),
            default_quiet_hours_end=os.getenv("LGPD_DEFAULT_QUIET_HOURS_END", "07:00"),
            audit_retention_years=int(os.getenv("LGPD_AUDIT_RETENTION_YEARS", "5")),
            delivery_retention_days=int(os.getenv("LGPD_DELIVERY_RETENTION_DAYS", "365")),
            consent_version=os.getenv("LGPD_CONSENT_VERSION", "1.0"),
            consent_renewal_days=int(os.getenv("LGPD_CONSENT_RENEWAL_DAYS", "365")),
            anonymization_hash_salt=os.getenv("LGPD_ANONYMIZATION_HASH_SALT", "intellicare-lgpd-salt-2026"),
            fhir_export_enabled=os.getenv("LGPD_FHIR_EXPORT_ENABLED", "true").lower() == "true",
        )
    
    class Config:
        """Pydantic config."""
        env_prefix = "LGPD_"
        case_sensitive = False


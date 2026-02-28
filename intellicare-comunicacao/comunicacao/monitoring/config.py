"""Configuração de monitoramento."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MonitoringConfig(BaseModel):
    """Configuração de monitoramento e observabilidade."""
    
    # Prometheus
    metrics_enabled: bool = Field(default=True, description="Habilitar coleta de métricas")
    metrics_port: int = Field(default=8005, description="Porta para endpoint /metrics")
    metrics_path: str = Field(default="/metrics", description="Path do endpoint de métricas")
    
    # Health checks
    health_check_enabled: bool = Field(default=True, description="Habilitar health checks")
    health_check_interval_seconds: int = Field(default=30, description="Intervalo entre health checks")
    
    # Database health
    db_health_timeout_seconds: float = Field(default=5.0, description="Timeout para health check do DB")
    db_health_query: str = Field(default="SELECT 1", description="Query para health check do DB")
    
    # Redis health
    redis_health_timeout_seconds: float = Field(default=5.0, description="Timeout para health check do Redis")
    
    # Channel health
    channel_health_timeout_seconds: float = Field(default=10.0, description="Timeout para health check de canais")
    channel_health_cache_ttl_seconds: int = Field(default=60, description="TTL do cache de health check de canais")
    
    # Alerting
    alerting_enabled: bool = Field(default=True, description="Habilitar alerting")
    alert_manager_url: str | None = Field(default=None, description="URL do AlertManager")
    
    # Logging
    structured_logging: bool = Field(default=True, description="Usar logging estruturado (JSON)")
    log_level: str = Field(default="INFO", description="Nível de log")
    
    @classmethod
    def from_env(cls) -> MonitoringConfig:
        """Cria configuração a partir de variáveis de ambiente."""
        import os
        
        return cls(
            metrics_enabled=os.getenv("MONITORING_METRICS_ENABLED", "true").lower() == "true",
            metrics_port=int(os.getenv("MONITORING_METRICS_PORT", "8005")),
            metrics_path=os.getenv("MONITORING_METRICS_PATH", "/metrics"),
            health_check_enabled=os.getenv("MONITORING_HEALTH_CHECK_ENABLED", "true").lower() == "true",
            health_check_interval_seconds=int(os.getenv("MONITORING_HEALTH_CHECK_INTERVAL", "30")),
            db_health_timeout_seconds=float(os.getenv("MONITORING_DB_HEALTH_TIMEOUT", "5.0")),
            redis_health_timeout_seconds=float(os.getenv("MONITORING_REDIS_HEALTH_TIMEOUT", "5.0")),
            channel_health_timeout_seconds=float(os.getenv("MONITORING_CHANNEL_HEALTH_TIMEOUT", "10.0")),
            channel_health_cache_ttl_seconds=int(os.getenv("MONITORING_CHANNEL_HEALTH_CACHE_TTL", "60")),
            alerting_enabled=os.getenv("MONITORING_ALERTING_ENABLED", "true").lower() == "true",
            alert_manager_url=os.getenv("MONITORING_ALERT_MANAGER_URL"),
            structured_logging=os.getenv("MONITORING_STRUCTURED_LOGGING", "true").lower() == "true",
            log_level=os.getenv("MONITORING_LOG_LEVEL", "INFO"),
        )


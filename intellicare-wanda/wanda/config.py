"""Configuracao do Wanda — Orquestrador IntelliCare (v3.0 — Fase 3)."""

from intellicare_core.config import BaseModuleConfig


class WandaConfig(BaseModuleConfig):
    module_name: str = "intellicare-wanda"
    module_version: str = "3.0.0"

    # Module URLs for discovery (HTTP agents)
    oswaldo_url: str = "http://localhost:8001"
    florence_url: str = "http://localhost:8002"
    zilda_url: str = "http://localhost:8003"
    donabedian_url: str = "http://localhost:8004"
    comunicacao_url: str = "http://localhost:8005"
    geralda_url: str = "http://localhost:8006"

    # Discovery settings
    discovery_timeout_seconds: int = 5
    health_check_interval_seconds: int = 30

    # Orchestration
    max_modules_per_query: int = 3
    module_call_timeout_seconds: int = 30

    # Safety
    enable_ips_first: bool = True
    enable_safety_guardrails: bool = True

    # ── EF-W001: PostgreSQL ────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://wanda:wanda@localhost:5432/intellicare"
    database_schema: str = "wanda"
    enable_persistence: bool = False  # Set True when PostgreSQL is available

    # ── EF-W002: IPS / Redis ──────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    enable_redis: bool = False  # Set True when Redis is available
    ips_ttl_seconds: int = 3600  # 1 hour
    ips_stale_ttl_seconds: int = 86400  # 24 hours

    # ── EF-W011: MCP Servers ──────────────────────────────────────
    mcp_ocr_url: str = "http://localhost:8008"
    mcp_superz_url: str = "http://localhost:8009"
    mcp_connection_timeout: int = 10
    mcp_ocr_tool_timeout: int = 30
    mcp_search_tool_timeout: int = 15
    mcp_analysis_tool_timeout: int = 60
    mcp_max_retries: int = 2
    enable_mcp: bool = False  # Set True when MCP servers are available

    # ── EF-W003: Ollama / LLM Routing ─────────────────────────────
    ollama_url: str = "http://localhost:11434"
    ollama_routing_model: str = "llama3.1:8b"
    ollama_routing_timeout_seconds: int = 5
    enable_ollama: bool = False  # Set True when Ollama is available

    # Routing strategy
    routing_method: str = "auto"          # auto | llm | keyword
    llm_confidence_min: float = 0.7       # Min confidence for LLM routing

    # ── EF-W004: Intelligent Aggregation ──────────────────────────
    ollama_aggregation_model: str = "llama3.1:8b"
    ollama_aggregation_timeout_seconds: int = 15
    max_agents_for_llm_aggregation: int = 5

    # ── EF-W005: LangGraph Workflows ──────────────────────────────
    enable_langgraph: bool = False
    workflow_max_iterations: int = 3
    workflow_timeout_seconds: int = 60
    workflow_parallel_timeout_seconds: int = 30

    # ── EF-W006: Proactive Event Consumer ─────────────────────────
    enable_event_consumer: bool = False
    event_consumer_group: str = "wanda"
    event_consumer_name: str = "wanda-orchestrator"

    # ── EF-W007: Alert Hub ────────────────────────────────────────
    enable_alert_hub: bool = False
    alert_consolidation_window_seconds: int = 300  # 5 minutes
    alert_escalation_check_interval_seconds: int = 60  # 1 minute

    # ── EF-W012: Rocket.Chat Bot ──────────────────────────────────
    enable_rc_bot: bool = False
    rocketchat_url: str = "https://rocket.gsi.srv.br"
    rocketchat_bot_token: str = ""
    rocketchat_webhook_token: str = ""
    rocketchat_bot_user_id: str = ""
    keycloak_url: str = "https://keycloak.gsi.srv.br"
    keycloak_realm: str = "bemcuidar"
    bot_context_ttl_seconds: int = 1800  # 30 minutes

    # ── EF-W013: Dr. Nise / FLOWISE ───────────────────────────────
    enable_dr_nise: bool = False
    flowise_url: str = "http://flowise:3001"
    flowise_dr_nise_flow_id: str = ""
    flowise_api_key: str = ""
    flowise_timeout_seconds: int = 30
    nise_session_ttl_seconds: int = 7200  # 2 hours inactivity
    nise_max_history_messages: int = 20
    nise_escalation_enabled: bool = True
    nise_fallback_message: str = (
        "Olá! Estou temporariamente indisponível. "
        "Por favor, entre em contato com sua equipe de saúde."
    )

    # ── EF-W008/009/010: Resiliencia e Observabilidade ───────────
    enable_resilience: bool = False
    cb_failure_threshold: int = 5
    cb_success_threshold: int = 2
    cb_timeout_seconds: int = 60
    cb_state_ttl_seconds: int = 3600
    cb_state_key_prefix: str = "wanda:circuit"
    retry_max_attempts: int = 3
    retry_initial_delay_seconds: float = 0.5
    retry_max_delay_seconds: float = 5.0
    enable_decision_tracing: bool = False
    enable_metrics: bool = False
    metrics_history_key: str = "wanda:metrics:slo_history"
    metrics_history_max_items: int = 200

    @property
    def module_urls(self) -> dict[str, str]:
        return {
            "intellicare-oswaldo": self.oswaldo_url,
            "intellicare-florence": self.florence_url,
            "intellicare-zilda": self.zilda_url,
            "intellicare-donabedian": self.donabedian_url,
            "intellicare-comunicacao": self.comunicacao_url,
            "intellicare-geralda": self.geralda_url,
        }

    @property
    def mcp_server_urls(self) -> dict[str, str]:
        return {
            "intellicare-ocr": self.mcp_ocr_url,
            "intellicare-superz": self.mcp_superz_url,
        }

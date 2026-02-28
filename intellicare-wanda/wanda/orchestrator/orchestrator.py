"""Wanda Orchestrator v3.0 — coordena modulos IntelliCare via HTTP + MCP + LLM + LangGraph."""

import asyncio
import logging
import time
from typing import Optional

from wanda.config import WandaConfig
from wanda.discovery.models import ModuleResponse, OrchestrationResult
from wanda.discovery.registry import ModuleRegistry
from wanda.orchestrator.aggregator import ResponseAggregator
from wanda.orchestrator.router import QueryRouter
from wanda.rules.safety import SafetyChecker

logger = logging.getLogger(__name__)


class WandaOrchestrator:
    """Main orchestrator — routes queries to modules and aggregates responses.

    v2.0 additions (Fase 1):
    - PersistentModuleRegistry (EF-W001) — PostgreSQL-backed when available
    - DiscoveryService (EF-W001) — probes + persists
    - IPSManager (EF-W002) — Redis-cached IPS
    - IPSEnricher (EF-W002) — enriches IPS with Oswaldo/Geralda
    - WandaMCPClient (EF-W011) — consumes MINERVA and PIERRE
    - WandaToolRegistry (EF-W011) — unified HTTP + MCP tool list

    v2.1 additions (Fase 2):
    - IntentRouter (EF-W003) — LLM-based routing via Ollama
    - IntentExtractor (EF-W003) — deterministic intent categorization
    - IntelligentAggregator (EF-W004) — LLM synthesis of multi-agent responses
    - ContradictionDetector (EF-W004) — detects conflicting agent outputs

    All v2.x components are optional — without them WANDA
    operates in v1.0 mode (in-memory, keyword routing, simple aggregation).
    """

    def __init__(
        self,
        config: Optional[WandaConfig] = None,
        registry: Optional[ModuleRegistry] = None,
    ):
        self.config = config or WandaConfig()

        # v1.0 components (always available)
        self.registry = registry or ModuleRegistry(
            module_urls=self.config.module_urls,
            timeout_seconds=self.config.discovery_timeout_seconds,
        )
        self.router = QueryRouter(max_modules=self.config.max_modules_per_query)
        self.aggregator = ResponseAggregator()
        self.safety = SafetyChecker(enable_ips_first=self.config.enable_ips_first)
        self._discovered = False

        # v2.0 Fase 1 components (initialized lazily based on config)
        self.persistent_registry = None
        self.discovery_service = None
        self.ips_manager = None
        self.ips_enricher = None
        self.mcp_client = None
        self.tool_registry = None

        # v2.1 Fase 2 components (LLM — initialized lazily based on config)
        self.intent_router = None
        self.intent_extractor = None
        self.intelligent_aggregator = None
        self.contradiction_detector = None

        # v3.0 Fase 3 components (EF-W005/W006/W007)
        self.workflow_executor = None
        self.alert_hub = None
        self.event_consumer = None
        self.event_coordinator = None
        self.bot_handler = None
        self.nise_gateway = None

        # v3.1 Fase 4 components (resilience + observability)
        self.circuit_breaker_manager = None
        self.retry_policy = None
        self.timeout_manager = None
        self.fallback_manager = None
        self.health_dashboard = None
        self.trace_store = None
        self.decision_tracer = None
        self.metrics_registry = None

        self._init_v2_components()
        self._init_v3_components()

    def _init_v3_components(self) -> None:
        """Initialize v3.0 subsystems (EF-W005..W013) based on config flags."""
        # Shared Redis client (reuse from IPS manager if available)
        redis_client = getattr(self.ips_manager, "_redis", None) if self.ips_manager else None

        # EF-W005: LangGraph WorkflowExecutor
        if self.config.enable_langgraph:
            try:
                from wanda.workflows.executor import WorkflowExecutor
                from wanda.workflows.checkpointer import WorkflowCheckpointer

                checkpointer = WorkflowCheckpointer(redis_client)
                self.workflow_executor = WorkflowExecutor(
                    checkpointer=checkpointer,
                    timeout_seconds=self.config.workflow_timeout_seconds,
                    parallel_timeout_seconds=self.config.workflow_parallel_timeout_seconds,
                    max_iterations=self.config.workflow_max_iterations,
                    metrics_registry=self.metrics_registry,
                )
                logger.info("WorkflowExecutor (LangGraph) initialized")
            except Exception as e:
                logger.warning("EF-W005 LangGraph unavailable: %s", e)

        # EF-W007: AlertHub
        if self.config.enable_alert_hub:
            try:
                from wanda.alerts.hub import AlertHub

                session_factory = None
                if self.config.enable_persistence:
                    try:
                        from wanda.database.engine import get_engine, get_session_factory
                        engine = get_engine(self.config.database_url)
                        session_factory = get_session_factory(engine)
                    except Exception:
                        pass

                self.alert_hub = AlertHub(
                    redis_client=redis_client,
                    session_factory=session_factory,
                    consolidation_window_seconds=self.config.alert_consolidation_window_seconds,
                    escalation_check_interval_seconds=self.config.alert_escalation_check_interval_seconds,
                    metrics_registry=self.metrics_registry,
                )
                logger.info("AlertHub initialized")
            except Exception as e:
                logger.warning("EF-W007 AlertHub unavailable: %s", e)

        # EF-W006: EventCoordinator + EcosystemEventConsumer
        if self.config.enable_event_consumer:
            try:
                import httpx
                from wanda.events.coordinator import EventCoordinator
                from wanda.events.consumer import EcosystemEventConsumer

                http_client = httpx.AsyncClient()
                self.event_coordinator = EventCoordinator(
                    redis_client=redis_client,
                    http_client=http_client,
                    alert_hub=self.alert_hub,
                    workflow_executor=self.workflow_executor,
                )
                self.event_coordinator.update_module_urls(self.config.module_urls)
                self.event_consumer = EcosystemEventConsumer(
                    redis_client=redis_client,
                    coordinator=self.event_coordinator,
                    group=self.config.event_consumer_group,
                    consumer_name=self.config.event_consumer_name,
                )
                logger.info("EcosystemEventConsumer initialized")
            except Exception as e:
                logger.warning("EF-W006 EventConsumer unavailable: %s", e)

        # EF-W012: RC Bot
        if self.config.enable_rc_bot:
            try:
                import httpx
                from wanda.bot.handler import WandaBotHandler
                from wanda.bot.rc_client import RocketChatBotClient
                from wanda.bot.auth import BotAuthMiddleware
                from wanda.bot.context_store import BotContextStore
                from wanda.bot.router import CommandRouter

                http_client = httpx.AsyncClient()
                rc_client = RocketChatBotClient(
                    base_url=self.config.rocketchat_url,
                    bot_user_id=self.config.rocketchat_bot_user_id,
                    bot_token=self.config.rocketchat_bot_token,
                    http_client=http_client,
                )
                auth = BotAuthMiddleware(
                    keycloak_url=self.config.keycloak_url or None,
                    realm=self.config.keycloak_realm,
                    http_client=http_client,
                )
                context_store = BotContextStore(
                    redis_client=redis_client,
                    ttl_seconds=self.config.bot_context_ttl_seconds,
                )
                router = CommandRouter(
                    http_client=http_client,
                    alert_hub=self.alert_hub,
                    module_urls=self.config.module_urls,
                )
                self.bot_handler = WandaBotHandler(
                    webhook_token=self.config.rocketchat_webhook_token,
                    bot_user_id=self.config.rocketchat_bot_user_id,
                    rc_client=rc_client,
                    router=router,
                    auth=auth,
                    context_store=context_store,
                )
                logger.info("WandaBotHandler (RC Bot) initialized")
            except Exception as e:
                logger.warning("EF-W012 RC Bot unavailable: %s", e)

        # EF-W013: Dr. Nise
        if self.config.enable_dr_nise:
            try:
                import httpx
                from wanda.nise.gateway import DrNiseGateway
                from wanda.nise.flowise_client import FlowiseClient
                from wanda.nise.session_manager import NiseSessionManager
                from wanda.nise.audit_logger import NiseAuditLogger

                flowise_http = httpx.AsyncClient()
                flowise_client = FlowiseClient(
                    base_url=self.config.flowise_url,
                    chatflow_id=self.config.flowise_dr_nise_flow_id,
                    api_key=self.config.flowise_api_key,
                    http_client=flowise_http,
                    timeout_seconds=float(self.config.flowise_timeout_seconds),
                )

                session_factory = None
                if self.config.enable_persistence:
                    try:
                        from wanda.database.engine import get_engine, get_session_factory
                        engine = get_engine(self.config.database_url)
                        session_factory = get_session_factory(engine)
                    except Exception:
                        pass

                session_mgr = NiseSessionManager(
                    redis_client=redis_client,
                    session_factory=session_factory,
                    ttl_seconds=self.config.nise_session_ttl_seconds,
                    max_history=self.config.nise_max_history_messages,
                )
                audit = NiseAuditLogger(session_factory=session_factory)

                # IPS loader — fetches from Florence (if available)
                florence_url = self.config.module_urls.get("intellicare-florence", "")

                async def _ips_loader(patient_id: str) -> dict:
                    if not florence_url:
                        return {}
                    import httpx as _httpx
                    async with _httpx.AsyncClient() as c:
                        resp = await c.get(f"{florence_url}/api/v1/ips/{patient_id}", timeout=10.0)
                        return resp.json() if resp.status_code == 200 else {}

                self.nise_gateway = DrNiseGateway(
                    flowise_client=flowise_client,
                    session_manager=session_mgr,
                    audit_logger=audit,
                    alert_hub=self.alert_hub,
                    ips_loader=_ips_loader,
                    fallback_message=self.config.nise_fallback_message,
                    escalation_enabled=self.config.nise_escalation_enabled,
                )
                logger.info("DrNiseGateway (FLOWISE) initialized")
            except Exception as e:
                logger.warning("EF-W013 Dr. Nise unavailable: %s", e)

    def _init_v2_components(self) -> None:
        """Initialize v2.0 subsystems based on config flags."""

        # EF-W001: Persistent Registry
        try:
            from wanda.registry.persistent_registry import PersistentModuleRegistry
            from wanda.registry.discovery_service import DiscoveryService

            db_repo = None
            if self.config.enable_persistence:
                try:
                    from wanda.database.engine import get_engine, get_session_factory
                    from wanda.database.repository import ModuleRepository

                    engine = get_engine(self.config.database_url)
                    session_factory = get_session_factory(engine)
                    db_repo = ModuleRepository(session_factory)
                    logger.info("PostgreSQL persistence enabled")
                except Exception as e:
                    logger.warning("PostgreSQL unavailable: %s (falling back to in-memory)", e)

            self.persistent_registry = PersistentModuleRegistry(
                module_urls=self.config.module_urls,
                db_repository=db_repo,
                timeout_seconds=self.config.discovery_timeout_seconds,
            )

            self.discovery_service = DiscoveryService(
                registry=self.persistent_registry,
                known_hosts=self.config.module_urls,
                timeout_seconds=self.config.discovery_timeout_seconds,
                health_check_interval=self.config.health_check_interval_seconds,
            )

        except ImportError as e:
            logger.warning("v2.0 registry unavailable: %s", e)

        # EF-W002: IPS Manager
        try:
            from wanda.ips.manager import IPSManager
            from wanda.ips.enricher import IPSEnricher

            redis_client = None
            if self.config.enable_redis:
                try:
                    import redis.asyncio as aioredis

                    redis_client = aioredis.from_url(
                        self.config.redis_url, decode_responses=True
                    )
                    logger.info("Redis IPS cache enabled")
                except Exception as e:
                    logger.warning("Redis unavailable: %s (IPS cache in-memory)", e)

            self.ips_manager = IPSManager(
                florence_url=self.config.florence_url,
                redis_client=redis_client,
                ips_ttl=self.config.ips_ttl_seconds,
                stale_ttl=self.config.ips_stale_ttl_seconds,
            )

            self.ips_enricher = IPSEnricher(
                oswaldo_url=self.config.oswaldo_url,
                geralda_url=self.config.geralda_url,
            )

        except ImportError as e:
            logger.warning("v2.0 IPS unavailable: %s", e)

        # EF-W011: MCP Client
        if self.config.enable_mcp:
            try:
                from wanda.mcp.client import WandaMCPClient
                from wanda.mcp.config import MCPClientConfig
                from wanda.mcp.tool_registry import WandaToolRegistry

                mcp_config = MCPClientConfig(
                    mcp_servers=self.config.mcp_server_urls,
                    ocr_timeout_seconds=self.config.mcp_ocr_tool_timeout,
                    search_timeout_seconds=self.config.mcp_search_tool_timeout,
                    analysis_timeout_seconds=self.config.mcp_analysis_tool_timeout,
                    connection_timeout_seconds=self.config.mcp_connection_timeout,
                    max_retries=self.config.mcp_max_retries,
                )

                self.mcp_client = WandaMCPClient(config=mcp_config)
                self.tool_registry = WandaToolRegistry(mcp_client=self.mcp_client)

                logger.info("MCP Client initialized for MINERVA + PIERRE")

            except ImportError as e:
                logger.warning("v2.0 MCP unavailable: %s", e)

        # EF-W003 + EF-W004: LLM Routing + Intelligent Aggregation
        if self.config.enable_ollama:
            try:
                from wanda.llm.ollama_provider import OllamaProvider
                from wanda.orchestrator.intent_extractor import IntentExtractor
                from wanda.orchestrator.intent_router import IntentRouter
                from wanda.orchestrator.intelligent_aggregator import IntelligentAggregator
                from wanda.orchestrator.contradiction_detector import ContradictionDetector

                routing_llm = OllamaProvider(
                    url=self.config.ollama_url,
                    model=self.config.ollama_routing_model,
                    timeout=float(self.config.ollama_routing_timeout_seconds),
                )
                self.intent_extractor = IntentExtractor()
                self.intent_router = IntentRouter(
                    llm_provider=routing_llm,
                    keyword_router=self.router,
                    confidence_min=self.config.llm_confidence_min,
                    max_modules=self.config.max_modules_per_query,
                )

                aggregation_llm = OllamaProvider(
                    url=self.config.ollama_url,
                    model=self.config.ollama_aggregation_model,
                    timeout=float(self.config.ollama_aggregation_timeout_seconds),
                )
                self.contradiction_detector = ContradictionDetector(
                    llm_provider=aggregation_llm
                )
                self.intelligent_aggregator = IntelligentAggregator(
                    llm_provider=aggregation_llm,
                    simple_aggregator=self.aggregator,
                    max_agents_for_llm=self.config.max_agents_for_llm_aggregation,
                )
                logger.info(
                    "LLM components initialized (model=%s, routing=%s, aggregation=%s)",
                    self.config.ollama_routing_model,
                    "IntentRouter",
                    "IntelligentAggregator",
                )
            except Exception as e:
                logger.warning("v2.1 LLM components unavailable: %s (keyword + simple fallback)", e)

        # EF-W008/009/010: Resilience + Observability (opt-in)
        if self.config.enable_resilience:
            try:
                from wanda.resilience import (
                    CircuitBreakerManager,
                    FallbackManager,
                    HealthDashboard,
                    RedisCircuitStateStore,
                    RetryPolicy,
                    TimeoutManager,
                )

                cb_state_store = None
                if self.config.enable_redis:
                    try:
                        import redis

                        cb_redis_client = redis.from_url(self.config.redis_url, decode_responses=True)
                        cb_state_store = RedisCircuitStateStore(cb_redis_client)
                    except Exception as redis_err:
                        logger.warning("Redis CB state store unavailable: %s (fallback in-memory)", redis_err)

                self.circuit_breaker_manager = CircuitBreakerManager(
                    failure_threshold=self.config.cb_failure_threshold,
                    success_threshold=self.config.cb_success_threshold,
                    timeout_seconds=self.config.cb_timeout_seconds,
                    state_store=cb_state_store,
                    state_ttl_seconds=self.config.cb_state_ttl_seconds,
                    state_key_prefix=self.config.cb_state_key_prefix,
                )
                self.retry_policy = RetryPolicy()
                self.timeout_manager = TimeoutManager()
                self.fallback_manager = FallbackManager()
                self.health_dashboard = HealthDashboard(self.circuit_breaker_manager)
                if hasattr(self.registry, "configure_resilience"):
                    self.registry.configure_resilience(
                        circuit_breaker_manager=self.circuit_breaker_manager,
                        retry_policy=self.retry_policy,
                        timeout_manager=self.timeout_manager,
                        fallback_manager=self.fallback_manager,
                    )
            except Exception as e:
                logger.warning("Fase 4 resilience unavailable: %s", e)

        if self.config.enable_decision_tracing:
            try:
                from wanda.observability import DecisionTracer, InMemoryTraceStore

                self.trace_store = InMemoryTraceStore()
                self.decision_tracer = DecisionTracer(self.trace_store)
            except Exception as e:
                logger.warning("Fase 4 tracing unavailable: %s", e)

        if self.config.enable_metrics:
            try:
                from wanda.observability import MetricsRegistry, RedisSLOHistoryStore

                slo_history_store = None
                if self.config.enable_redis:
                    try:
                        import redis

                        redis_client = redis.from_url(self.config.redis_url, decode_responses=True)
                        slo_history_store = RedisSLOHistoryStore(
                            redis_client=redis_client,
                            key=self.config.metrics_history_key,
                            max_items=self.config.metrics_history_max_items,
                        )
                    except Exception as redis_err:
                        logger.warning("Redis SLO history unavailable: %s (fallback in-memory)", redis_err)

                self.metrics_registry = MetricsRegistry(
                    history_store=slo_history_store,
                    history_limit=self.config.metrics_history_max_items,
                )
                if self.ips_manager is not None and hasattr(self.ips_manager, "set_metrics_registry"):
                    self.ips_manager.set_metrics_registry(self.metrics_registry)
                if self.workflow_executor is not None and hasattr(self.workflow_executor, "set_metrics_registry"):
                    self.workflow_executor.set_metrics_registry(self.metrics_registry)
                if self.alert_hub is not None and hasattr(self.alert_hub, "set_metrics_registry"):
                    self.alert_hub.set_metrics_registry(self.metrics_registry)
            except Exception as e:
                logger.warning("Fase 4 metrics unavailable: %s", e)

    async def discover_modules(self) -> int:
        """Discover available modules. Returns count of online modules."""
        await self.registry.discover()
        self._discovered = True
        return self.registry.online_count

    async def chat(
        self,
        message: str,
        patient_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> OrchestrationResult:
        """Process a user message through the orchestration pipeline."""
        _ = session_id
        started_at = time.monotonic()
        trace_context = None

        if self.metrics_registry is not None:
            self.metrics_registry.orchestration_in_flight.inc()
        if self.decision_tracer is not None:
            trace_context = await self.decision_tracer.start_trace(query=message, patient_id=patient_id)

        # Step 1: Ensure modules are discovered
        if not self._discovered:
            await self.discover_modules()

        online = self.registry.get_online_modules()
        if not online:
            result = OrchestrationResult(
                query=message,
                modules_used=[],
                responses=[],
                aggregated_response="Nenhum modulo IntelliCare esta disponivel no momento.",
            )
            await self._finalize_observability(
                result=result,
                started_at=started_at,
                trace_context=trace_context,
                routing_method="none",
            )
            return result

        # Step 2: Safety pre-check (IPS-First rule)
        safety_warnings = []
        if self.config.enable_safety_guardrails:
            warnings = self.safety.pre_check(
                query=message,
                patient_id=patient_id,
                has_clinical_intent=self.router.detect_clinical_intent(message),
            )
            safety_warnings.extend(warnings)

        # Step 3: Route query to appropriate modules
        # EF-W003: Use IntentRouter (LLM) if available, else keyword router (v1.0)
        if self.intent_router is not None:
            routing = await self.intent_router.route(
                query=message,
                available_modules=online,
                patient_id=patient_id,
            )
        else:
            routing = self.router.route(
                query=message,
                available_modules=online,
                patient_id=patient_id,
            )
        if trace_context is not None and self.decision_tracer is not None:
            await self.decision_tracer.record_routing(
                trace_context,
                routing_method=routing.routing_method,
                reasoning=routing.reason,
            )
        if self.metrics_registry is not None:
            self.metrics_registry.record_routing_decision(
                method=routing.routing_method,
                agents_count=len(routing.target_modules),
                success=bool(routing.target_modules),
                llm_confidence=routing.confidence if routing.routing_method == "llm" else None,
            )

        if not routing.target_modules:
            result = OrchestrationResult(
                query=message,
                modules_used=[],
                responses=[],
                aggregated_response="Nao foi possivel identificar um modulo adequado para esta consulta.",
                routing_decision=routing,
                safety_warnings=safety_warnings,
            )
            await self._finalize_observability(
                result=result,
                started_at=started_at,
                trace_context=trace_context,
                routing_method=routing.routing_method,
            )
            return result

        # Step 4: Call target modules in parallel
        tasks = []
        for module_name in routing.target_modules:
            tasks.append(
                self._call_module_for_query(module_name, message, patient_id)
            )

        responses = await asyncio.gather(*tasks)

        # Step 5: Safety post-check
        if self.config.enable_safety_guardrails:
            post_warnings = self.safety.post_check(responses=list(responses))
            safety_warnings.extend(post_warnings)

        # Step 6: Aggregate responses
        # EF-W004: Use IntelligentAggregator (LLM) if available, else simple (v1.0)
        if self.intelligent_aggregator is not None:
            result = await self.intelligent_aggregator.aggregate(
                query=message,
                responses=list(responses),
                routing=routing,
                safety_warnings=safety_warnings,
                patient_id=patient_id,
            )
        else:
            result = self.aggregator.aggregate(
                query=message,
                responses=list(responses),
                routing=routing,
                safety_warnings=safety_warnings,
            )

        if trace_context is not None and self.decision_tracer is not None:
            for response in responses:
                await self.decision_tracer.record_agent_call(
                    trace_context,
                    agent_name=response.module_name,
                    endpoint=response.endpoint,
                    payload=None,
                    status_code=response.status_code,
                    latency_ms=int(response.duration_ms),
                    success=response.success,
                    error=response.error or None,
                )

        await self._finalize_observability(
            result=result,
            started_at=started_at,
            trace_context=trace_context,
            routing_method=routing.routing_method,
        )
        return result

    async def _call_module_for_query(
        self,
        module_name: str,
        query: str,
        patient_id: Optional[str] = None,
    ):
        """Call a module's main endpoint with the user query."""
        module = self.registry.get_module(module_name)
        if not module:
            from wanda.discovery.models import ModuleResponse

            return ModuleResponse(
                module_name=module_name,
                endpoint="/api/v1/info",
                status_code=0,
                error="Modulo nao encontrado",
            )

        # Determine which endpoint to call based on module capabilities
        endpoint, method, payload = self._resolve_endpoint(
            module_name, module.capabilities, query, patient_id
        )
        return await self._call_with_resilience(
            module_name=module_name,
            endpoint=endpoint,
            method=method,
            payload=payload,
        )

    async def _call_with_resilience(
        self,
        module_name: str,
        endpoint: str,
        method: str,
        payload: Optional[dict],
    ) -> ModuleResponse:
        if getattr(self.registry, "has_resilience", False):
            return await self.registry.call_module(
                module_name=module_name,
                endpoint=endpoint,
                method=method,
                payload=payload,
            )

        async def _do_call() -> ModuleResponse:
            timeout = 30.0
            if self.timeout_manager is not None:
                timeout = self.timeout_manager.get_timeout(module_name.replace("intellicare-", ""), "analyze")
            return await asyncio.wait_for(
                self.registry.call_module(
                    module_name=module_name,
                    endpoint=endpoint,
                    method=method,
                    payload=payload,
                ),
                timeout=timeout,
            )

        async def _attempt() -> ModuleResponse:
            if self.circuit_breaker_manager is None:
                response = await _do_call()
            else:
                breaker = self.circuit_breaker_manager.get(module_name)
                response = await breaker.call(_do_call)
            if not response.success and (response.status_code == 0 or response.status_code >= 500):
                raise RuntimeError(response.error or f"Falha em {module_name}")
            return response

        try:
            if self.retry_policy is not None:
                return await self.retry_policy.execute_with_retry(_attempt, policy_name="default")
            return await _attempt()
        except Exception as exc:
            if self.fallback_manager is not None:
                fallback = await self.fallback_manager.get_fallback(module_name, query="", patient_id=None)
                return ModuleResponse(
                    module_name=module_name,
                    endpoint=endpoint,
                    status_code=503,
                    data={"fallback": fallback},
                    error=str(exc),
                )
            return ModuleResponse(
                module_name=module_name,
                endpoint=endpoint,
                status_code=503,
                error=str(exc),
            )

    async def _finalize_observability(
        self,
        result: OrchestrationResult,
        started_at: float,
        trace_context,
        routing_method: str,
    ) -> None:
        elapsed = max(0.0, time.monotonic() - started_at)
        if self.metrics_registry is not None:
            status = "success" if result.modules_used else "empty"
            self.metrics_registry.record_orchestration(
                request_type="chat",
                routing_method=routing_method,
                status=status,
                elapsed_seconds=elapsed,
            )
            self.metrics_registry.orchestration_in_flight.dec()
            for response in result.responses:
                call_status = "success" if response.success else "failed"
                self.metrics_registry.record_agent_call(
                    agent=response.module_name,
                    capability=response.endpoint,
                    status=call_status,
                    latency_seconds=max(0.0, float(response.duration_ms) / 1000.0),
                )
            if self.circuit_breaker_manager is not None:
                state_map = {"CLOSED": 0, "OPEN": 1, "HALF_OPEN": 2}
                for snapshot in self.circuit_breaker_manager.snapshots():
                    self.metrics_registry.circuit_breaker_state.labels(snapshot.agent_name).set(
                        state_map.get(snapshot.state.value, 0)
                    )

        if trace_context is not None and self.decision_tracer is not None:
            await self.decision_tracer.complete_trace(trace_context, success=bool(result.modules_used))

    def _resolve_endpoint(
        self,
        module_name: str,
        capabilities: list[str],
        query: str,
        patient_id: Optional[str],
    ) -> tuple[str, str, Optional[dict]]:
        """Determine the best endpoint to call on a module."""

        # Module-specific routing
        if module_name == "intellicare-oswaldo":
            if patient_id:
                return "/api/v1/analyze", "POST", {
                    "patient_id": patient_id,
                    "query": query,
                }
            return "/api/v1/diseases", "GET", None

        if module_name == "intellicare-florence":
            return "/api/v1/panels", "GET", None

        if module_name == "intellicare-zilda":
            return "/api/v1/regions", "GET", None

        if module_name == "intellicare-geralda":
            if patient_id:
                return "/api/v1/plans", "GET", None
            return "/api/v1/education/conditions", "GET", None

        if module_name == "intellicare-donabedian":
            return "/api/v1/indicators", "GET", None

        # Default: just get info
        return "/api/v1/info", "GET", None

    async def get_module_status(self) -> dict:
        """Get current status of all modules."""
        if not self._discovered:
            await self.discover_modules()

        modules = []
        for module in self.registry._modules.values():
            modules.append(module.to_dict())

        return {
            "total": self.registry.total_modules,
            "online": self.registry.online_count,
            "modules": modules,
        }

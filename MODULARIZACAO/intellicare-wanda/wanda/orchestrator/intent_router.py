"""LLM-based intent router for WANDA (EF-W003).

Replaces keyword routing with Ollama-powered intent understanding,
with automatic fallback to the v1.0 QueryRouter when LLM is unavailable.
"""

import json
import logging
from typing import Optional

from wanda.discovery.models import ModuleInfo, RoutingDecision
from wanda.llm.exceptions import LLMParseError, LLMTimeoutError, LLMUnavailableError
from wanda.llm.provider import LLMProvider
from wanda.orchestrator.router import QueryRouter

logger = logging.getLogger(__name__)


# ── System Prompt ──────────────────────────────────────────────────────────

WANDA_ROUTING_SYSTEM_PROMPT = """Voce e a WANDA, orquestradora do sistema IntelliCare de saude.
Sua unica funcao agora e decidir quais agentes devem responder uma consulta medica.

MODULOS DISPONIVEIS:
{modules_json}

CONTEXTO DO PACIENTE:
{patient_context}

REGRAS DE ROTEAMENTO:
1. Escolha o agente mais especializado para cada parte da pergunta
2. Se envolve gestao de cuidado, adesao, plano, tarefa, lembrete → intellicare-geralda
3. Se envolve analise clinica profunda, exames, laboratorio, guidelines → intellicare-florence
4. Se envolve DRC, DM2, HAS, creatinina, TFG, estadiamento → intellicare-oswaldo
5. Se envolve dados territoriais, CNES, UBS, DATASUS, municipio → intellicare-zilda
6. Se envolve qualidade, indicadores, Donabedian, avaliacao → intellicare-donabedian
7. Se a pergunta requer dados de MULTIPLOS agentes → liste todos necessarios
8. NUNCA invente agentes — use APENAS os nomes exatos listados em MODULOS DISPONIVEIS
9. Se nenhum agente e adequado, retorne primary_agents como lista vazia

FORMATO DE RESPOSTA — JSON obrigatorio, sem texto fora do JSON:
{
    "primary_agents": ["nome-exato-do-agente"],
    "secondary_agents": [],
    "reasoning": "Explicacao da decisao em portugues",
    "confidence": 0.95,
    "multi_agent": false
}"""


class IntentRouter:
    """Routes queries to modules using LLM-based intent understanding.

    Priority:
    1. LLM routing (Ollama) — if available and confidence >= threshold
    2. KeywordRouter (v1.0) — automatic fallback

    The v1.0 QueryRouter is always available as fallback, ensuring
    zero-downtime degradation when Ollama is unavailable or slow.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        keyword_router: Optional[QueryRouter] = None,
        confidence_min: float = 0.7,
        max_modules: int = 3,
    ):
        self._llm = llm_provider
        self._keyword_router = keyword_router or QueryRouter(max_modules=max_modules)
        self._confidence_min = confidence_min
        self._max_modules = max_modules

    async def route(
        self,
        query: str,
        available_modules: list[ModuleInfo],
        patient_id: Optional[str] = None,
        patient_context: Optional[str] = None,
    ) -> RoutingDecision:
        """Route a query to the appropriate modules.

        Tries LLM routing first, falls back to keyword routing on any failure.

        Args:
            query: The user's question.
            available_modules: List of currently online modules.
            patient_id: Optional patient identifier.
            patient_context: Optional pre-loaded patient context summary.

        Returns:
            RoutingDecision with target_modules and routing_method.
        """
        if not available_modules:
            return RoutingDecision(
                target_modules=[],
                reason="Nenhum modulo disponivel",
                confidence=0.0,
                routing_method="keyword",
            )

        # Try LLM routing
        try:
            decision = await self._route_with_llm(
                query=query,
                available_modules=available_modules,
                patient_context=patient_context,
            )
            if decision is not None:
                return decision
        except (LLMUnavailableError, LLMTimeoutError) as e:
            logger.warning("LLM routing unavailable: %s — using keyword fallback", e)
        except LLMParseError as e:
            logger.warning("LLM response parse error: %s — using keyword fallback", e)
        except Exception as e:
            logger.warning("Unexpected LLM error: %s — using keyword fallback", e)

        # Fallback: keyword routing
        return self._keyword_fallback(query, available_modules)

    async def _route_with_llm(
        self,
        query: str,
        available_modules: list[ModuleInfo],
        patient_context: Optional[str] = None,
    ) -> Optional[RoutingDecision]:
        """Attempt LLM-based routing. Returns None if confidence is too low."""
        available_names = {m.name for m in available_modules}

        # Build modules description for the prompt
        modules_desc = []
        for m in available_modules:
            caps = ", ".join(m.capabilities[:5]) if m.capabilities else "general"
            modules_desc.append({"name": m.name, "capabilities": caps})
        modules_json = json.dumps(modules_desc, ensure_ascii=False, indent=2)

        context_str = patient_context or "Nenhum contexto de paciente disponivel."

        system_prompt = (
            WANDA_ROUTING_SYSTEM_PROMPT
            .replace("{modules_json}", modules_json)
            .replace("{patient_context}", context_str)
        )

        response = await self._llm.chat(
            system_prompt=system_prompt,
            user_message=query,
            json_mode=True,
        )

        # Parse JSON response
        try:
            data = json.loads(response.content)
        except json.JSONDecodeError as e:
            raise LLMParseError(
                raw_response=response.content,
                reason=f"Invalid JSON: {e}",
            ) from e

        # Validate required fields
        if "primary_agents" not in data:
            raise LLMParseError(
                raw_response=response.content,
                reason="Missing 'primary_agents' field",
            )

        confidence = float(data.get("confidence", 0.0))
        if confidence < self._confidence_min:
            logger.info(
                "LLM confidence %.2f < threshold %.2f — falling back to keyword",
                confidence,
                self._confidence_min,
            )
            return None

        # Validate agents exist in available modules
        primary = [a for a in data.get("primary_agents", []) if a in available_names]
        secondary = [a for a in data.get("secondary_agents", []) if a in available_names]

        if not primary:
            logger.info("LLM returned no valid primary agents — falling back to keyword")
            return None

        # Limit to max_modules
        all_targets = (primary + secondary)[: self._max_modules]

        reasoning = data.get("reasoning", "Roteamento por LLM")
        logger.info(
            "LLM routing → %s (confidence=%.2f, latency=%dms)",
            all_targets,
            confidence,
            response.latency_ms,
        )

        return RoutingDecision(
            target_modules=all_targets,
            reason=reasoning,
            confidence=confidence,
            routing_method="llm",
        )

    def _keyword_fallback(
        self,
        query: str,
        available_modules: list[ModuleInfo],
    ) -> RoutingDecision:
        """Use the v1.0 keyword router as fallback."""
        decision = self._keyword_router.route(
            query=query,
            available_modules=available_modules,
        )
        # Ensure routing_method is set
        return RoutingDecision(
            target_modules=decision.target_modules,
            reason=f"[keyword fallback] {decision.reason}",
            confidence=decision.confidence,
            routing_method="keyword",
        )

"""Intelligent multi-agent response aggregator using LLM (EF-W004).

Synthesizes responses from multiple IntelliCare agents into a coherent,
calibrated response. Falls back to the v1.0 ResponseAggregator when
Ollama is unavailable or returns a poor response.
"""

import json
import logging
from typing import Optional

from wanda.discovery.models import AggregatedResponse, ModuleResponse, OrchestrationResult, RoutingDecision
from wanda.llm.exceptions import LLMParseError, LLMTimeoutError, LLMUnavailableError
from wanda.llm.provider import LLMProvider
from wanda.orchestrator.aggregator import ResponseAggregator

logger = logging.getLogger(__name__)


# ── System Prompts ─────────────────────────────────────────────────────────

AGGREGATOR_PROFESSIONAL_PROMPT = """Voce e WANDA, orquestradora do sistema IntelliCare.
Voce recebeu respostas de {n_agents} agentes especializados sobre a consulta.
Sintetize essas respostas em uma resposta clara e util para o profissional de saude.

CONSULTA ORIGINAL:
{query}

PACIENTE:
{patient_context}

RESPOSTAS DOS AGENTES:
{formatted_responses}

REGRAS:
1. Sintetize as informacoes — NAO apenas concatene
2. Destaque informacoes criticas ou alertas
3. Elimine redundancias entre agentes
4. Se houver contradicoes entre agentes, mencione explicitamente
5. Sugira proximas acoes quando aplicavel
6. NUNCA invente informacoes que nao estejam nas respostas dos agentes
7. Se uma informacao nao foi fornecida por nenhum agente, diga que nao esta disponivel

FORMATO DE RESPOSTA — JSON obrigatorio, sem texto fora do JSON:
{{
    "synthesis": "Texto principal da resposta em markdown",
    "key_points": ["Ponto 1", "Ponto 2", "Ponto 3"],
    "recommended_actions": ["Acao 1", "Acao 2"],
    "critical_alerts": [],
    "data_sources": {{
        "nome-do-agente": "O que ele forneceu"
    }},
    "confidence": 0.9
}}"""

AGGREGATOR_PATIENT_PROMPT = """Voce e WANDA do BemCuidar.
Recebeu informacoes dos especialistas e precisa explicar para o paciente de forma simples.

PERGUNTA DO PACIENTE:
{query}

INFORMACOES DOS ESPECIALISTAS:
{formatted_responses}

REGRAS:
1. Use linguagem SIMPLES — sem jargao medico
2. Seja acolhedor e encorajador
3. Frases curtas (max 2 linhas por frase)
4. Destaque o que o paciente DEVE FAZER (acoes concretas)
5. NUNCA assuste desnecessariamente
6. Se e urgente: seja claro e direto
7. Se nao sabe: diga que vai falar com a equipe

FORMATO DE RESPOSTA — JSON obrigatorio:
{{
    "synthesis": "Resposta principal em linguagem acessivel",
    "key_points": ["Informacao importante 1", "Informacao importante 2"],
    "recommended_actions": ["O que voce deve fazer agora"],
    "critical_alerts": [],
    "data_sources": {{}},
    "confidence": 0.9
}}"""


class IntelligentAggregator:
    """Aggregates multi-agent responses using LLM synthesis (EF-W004).

    Wraps the v1.0 ResponseAggregator as fallback for resilience.

    Key behaviors:
    - Single agent: pass through without LLM (no overhead)
    - Multiple agents: LLM synthesis → fallback simple concat
    - Supports professional and patient recipient types
    - Anti-fabrication: validates LLM output against agent responses
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        simple_aggregator: Optional[ResponseAggregator] = None,
        max_agents_for_llm: int = 5,
    ):
        self._llm = llm_provider
        self._simple = simple_aggregator or ResponseAggregator()
        self._max_agents_for_llm = max_agents_for_llm

    async def aggregate(
        self,
        query: str,
        responses: list[ModuleResponse],
        routing: Optional[RoutingDecision] = None,
        safety_warnings: Optional[list[str]] = None,
        patient_id: Optional[str] = None,
        patient_context: Optional[str] = None,
        recipient_type: str = "professional",
    ) -> OrchestrationResult:
        """Aggregate module responses into a coherent result.

        For multi-agent responses, attempts LLM synthesis.
        Falls back to v1.0 simple aggregation on any failure.
        """
        successful = [r for r in responses if r.success]

        # Single agent or no successful responses → pass through
        if len(successful) <= 1 or len(successful) > self._max_agents_for_llm:
            return self._simple_fallback(query, responses, routing, safety_warnings)

        # Try LLM aggregation
        try:
            aggregated = await self._aggregate_with_llm(
                query=query,
                successful_responses=successful,
                patient_context=patient_context,
                recipient_type=recipient_type,
            )
            if aggregated is not None:
                return OrchestrationResult(
                    query=query,
                    modules_used=[r.module_name for r in successful],
                    responses=responses,
                    aggregated_response=aggregated.synthesis,
                    routing_decision=routing,
                    safety_warnings=safety_warnings or [],
                )

        except (LLMUnavailableError, LLMTimeoutError) as e:
            logger.warning("LLM aggregation unavailable: %s — using simple fallback", e)
        except LLMParseError as e:
            logger.warning("LLM aggregation parse error: %s — using simple fallback", e)
        except Exception as e:
            logger.warning("Unexpected LLM aggregation error: %s — simple fallback", e)

        return self._simple_fallback(query, responses, routing, safety_warnings)

    async def _aggregate_with_llm(
        self,
        query: str,
        successful_responses: list[ModuleResponse],
        patient_context: Optional[str] = None,
        recipient_type: str = "professional",
    ) -> Optional[AggregatedResponse]:
        """Call LLM to synthesize agent responses. Returns None if output is invalid."""
        formatted = self._format_responses_for_prompt(successful_responses)
        patient_str = patient_context or "Informacoes do paciente nao disponíveis."
        n_agents = len(successful_responses)

        if recipient_type == "patient":
            system_prompt = AGGREGATOR_PATIENT_PROMPT.format(
                query=query,
                formatted_responses=formatted,
            )
        else:
            system_prompt = AGGREGATOR_PROFESSIONAL_PROMPT.format(
                n_agents=n_agents,
                query=query,
                patient_context=patient_str,
                formatted_responses=formatted,
            )

        response = await self._llm.chat(
            system_prompt=system_prompt,
            user_message=f"Sintetize as respostas dos {n_agents} agentes para a consulta: {query}",
            json_mode=True,
        )

        # Parse JSON
        try:
            data = json.loads(response.content)
        except json.JSONDecodeError as e:
            raise LLMParseError(
                raw_response=response.content,
                reason=f"Invalid JSON: {e}",
            ) from e

        synthesis = data.get("synthesis", "").strip()
        if not synthesis:
            raise LLMParseError(
                raw_response=response.content,
                reason="Empty synthesis field",
            )

        # Basic anti-fabrication check: synthesis should not be longer than
        # the combined agent responses by more than 50% (rough heuristic)
        combined_length = sum(len(str(r.data)) for r in successful_responses)
        if len(synthesis) > combined_length * 3:
            logger.warning(
                "LLM synthesis suspiciously long (%d chars vs %d combined) — fallback",
                len(synthesis),
                combined_length,
            )
            return None

        logger.info(
            "LLM aggregation: %d agents → %d chars synthesis (latency=%dms)",
            len(successful_responses),
            len(synthesis),
            response.latency_ms,
        )

        return AggregatedResponse(
            synthesis=synthesis,
            key_points=data.get("key_points", [])[:5],
            recommended_actions=data.get("recommended_actions", [])[:5],
            critical_alerts=data.get("critical_alerts", [])[:3],
            data_sources=data.get("data_sources", {}),
            aggregation_method="llm",
            recipient_type=recipient_type,
            confidence=float(data.get("confidence", 0.9)),
        )

    def _format_responses_for_prompt(self, responses: list[ModuleResponse]) -> str:
        """Format agent responses into a prompt-friendly string."""
        parts = []
        for r in responses:
            content = str(r.data.get("data", r.data))[:2000]  # Limit per agent
            parts.append(f"=== {r.module_name} ===\n{content}")
        return "\n\n".join(parts)

    def _simple_fallback(
        self,
        query: str,
        responses: list[ModuleResponse],
        routing: Optional[RoutingDecision],
        safety_warnings: Optional[list[str]],
    ) -> OrchestrationResult:
        """Use v1.0 ResponseAggregator as fallback."""
        return self._simple.aggregate(
            query=query,
            responses=responses,
            routing=routing,
            safety_warnings=safety_warnings,
        )

"""Contradiction detector for multi-agent responses (EF-W004).

Uses LLM to identify conflicting information between agents,
e.g. Oswaldo says DRC G3, Florence says G4.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from wanda.discovery.models import ModuleResponse
from wanda.llm.exceptions import LLMParseError, LLMTimeoutError, LLMUnavailableError
from wanda.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


@dataclass
class Contradiction:
    """A detected contradiction between two agent responses."""

    field: str                # The clinical field that contradicts (e.g., "DRC stage")
    agent_a: str              # First agent name
    value_a: str              # Value from first agent
    agent_b: str              # Second agent name
    value_b: str              # Value from second agent
    severity: str = "warning"  # "warning" | "error"
    description: str = ""


CONTRADICTION_SYSTEM_PROMPT = """Voce e um revisor medico especializado em detectar inconsistencias.
Analise as respostas de {n_agents} agentes medicos e identifique contradicoes clinicas relevantes.

RESPOSTAS DOS AGENTES:
{formatted_responses}

Identifique apenas contradicoes CLINICAMENTE SIGNIFICATIVAS, como:
- Estadiamento de doenca divergente entre agentes (ex: DRC G3 vs G4)
- Valores laboratoriais contraditórios
- Medicamentos conflitantes
- Avaliações de adesão opostas

NAO reporte:
- Diferenças de enfase ou perspectiva
- Informacoes complementares (nao conflitantes)
- Dados de dominios diferentes (ex: qualidade vs cuidado)

FORMATO DE RESPOSTA — JSON obrigatorio:
{{
    "contradictions": [
        {{
            "field": "Campo clinico em contradicao",
            "agent_a": "nome-do-agente",
            "value_a": "Valor do agente A",
            "agent_b": "nome-do-agente",
            "value_b": "Valor do agente B",
            "severity": "warning",
            "description": "Descricao da contradicao"
        }}
    ],
    "has_contradictions": false
}}

Se nao houver contradicoes, retorne contradictions como lista vazia."""


class ContradictionDetector:
    """Detects contradictions between multiple agent responses using LLM.

    Only meaningful for 2+ successful agent responses.
    Gracefully degrades to empty list on any LLM failure.
    """

    def __init__(self, llm_provider: LLMProvider):
        self._llm = llm_provider

    async def detect(
        self,
        responses: list[ModuleResponse],
    ) -> list[Contradiction]:
        """Detect contradictions between agent responses.

        Args:
            responses: List of successful ModuleResponse objects.

        Returns:
            List of detected Contradiction objects (empty if none or LLM fails).
        """
        successful = [r for r in responses if r.success]

        if len(successful) < 2:
            return []  # Need at least 2 agents to contradict each other

        try:
            return await self._detect_with_llm(successful)
        except (LLMUnavailableError, LLMTimeoutError, LLMParseError) as e:
            logger.debug("Contradiction detection skipped: %s", e)
            return []
        except Exception as e:
            logger.debug("Contradiction detection error: %s", e)
            return []

    async def _detect_with_llm(
        self,
        responses: list[ModuleResponse],
    ) -> list[Contradiction]:
        """Use LLM to find contradictions."""
        formatted = self._format_for_prompt(responses)
        n_agents = len(responses)

        system_prompt = CONTRADICTION_SYSTEM_PROMPT.format(
            n_agents=n_agents,
            formatted_responses=formatted,
        )

        response = await self._llm.chat(
            system_prompt=system_prompt,
            user_message=f"Analise as {n_agents} respostas e identifique contradicoes.",
            json_mode=True,
        )

        try:
            data = json.loads(response.content)
        except json.JSONDecodeError as e:
            raise LLMParseError(
                raw_response=response.content,
                reason=f"Invalid JSON: {e}",
            ) from e

        contradictions_raw = data.get("contradictions", [])
        if not isinstance(contradictions_raw, list):
            return []

        result = []
        for item in contradictions_raw:
            if not isinstance(item, dict):
                continue
            try:
                result.append(
                    Contradiction(
                        field=str(item.get("field", "unknown")),
                        agent_a=str(item.get("agent_a", "")),
                        value_a=str(item.get("value_a", "")),
                        agent_b=str(item.get("agent_b", "")),
                        value_b=str(item.get("value_b", "")),
                        severity=str(item.get("severity", "warning")),
                        description=str(item.get("description", "")),
                    )
                )
            except Exception:
                continue

        if result:
            logger.warning(
                "Found %d contradiction(s) between agents: %s",
                len(result),
                [c.field for c in result],
            )

        return result

    def _format_for_prompt(self, responses: list[ModuleResponse]) -> str:
        """Format responses for the contradiction detection prompt."""
        parts = []
        for r in responses:
            content = str(r.data.get("data", r.data))[:1000]  # Limit per agent
            parts.append(f"[{r.module_name}]\n{content}")
        return "\n\n".join(parts)

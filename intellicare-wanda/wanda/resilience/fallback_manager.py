"""Fallbacks quando agentes estao indisponiveis."""

from __future__ import annotations

from wanda.discovery.models import ModuleResponse


class FallbackManager:
    _messages: dict[str, str] = {
        "intellicare-florence": "Analise clinica indisponivel no momento.",
        "intellicare-oswaldo": "Dados de DRC indisponiveis no momento.",
        "intellicare-geralda": "Gestao de cuidado indisponivel no momento.",
        "intellicare-zilda": "Dados territoriais indisponiveis no momento.",
        "intellicare-comunicacao": "Servico de comunicacao indisponivel no momento.",
    }

    async def get_fallback(self, agent: str, query: str, patient_id: str | None) -> dict[str, str]:
        _ = query, patient_id
        return {"agent": agent, "message": self._messages.get(agent, "Modulo indisponivel temporariamente.")}

    async def get_partial_response(
        self,
        successful_responses: list[ModuleResponse],
        failed_agents: list[str],
    ) -> dict[str, object]:
        partial_text = " ".join(
            str(response.data.get("message", "")).strip()
            for response in successful_responses
            if response.success
        ).strip()
        return {
            "aggregated_response": partial_text or "Resposta parcial: alguns modulos nao responderam.",
            "failed_agents": failed_agents,
        }

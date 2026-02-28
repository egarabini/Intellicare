"""Serviço de operação AI — orquestra chamadas ao Wanda/Florence/Geralda."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

import httpx

from grahame.config import config


class AIOperationService:
    """Orquestra operações AI via Wanda ou agentes diretos."""

    def __init__(
        self,
        wanda_url: str | None = None,
        florence_url: str | None = None,
        geralda_url: str | None = None,
        timeout: int = 120,
    ):
        self.wanda_url = (wanda_url or getattr(config, "wanda_url", "")) or "http://localhost:8002"
        self.florence_url = (florence_url or getattr(config, "florence_url", "")) or "http://localhost:8002"
        self.geralda_url = (geralda_url or getattr(config, "geralda_url", "")) or "http://localhost:8006"
        self.timeout = timeout

    async def _call_wanda(self, prompt: str, patient_id: str | None = None) -> str:
        """Chama Wanda /api/v1/chat e retorna resposta agregada."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.wanda_url.rstrip('/')}/api/v1/chat",
                json={"message": prompt, "patient_id": patient_id},
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("success") and data.get("data", {}).get("response"):
                return data["data"]["response"]
            return str(data.get("data", data))

    async def _call_florence_analyze(
        self, prompt: str, patient_id: str | None = None, context: dict | None = None
    ) -> str:
        """Chama Florence /api/v1/analyze ou /api/v1/rag/query."""
        if context and context.get("observation"):
            # Se tem Observation, pode usar analyze com results
            results = context.get("results", {})
            if results:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        f"{self.florence_url.rstrip('/')}/api/v1/analyze",
                        json={
                            "patient_id": patient_id or "unknown",
                            "results": results,
                            "timestamp": None,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return json.dumps(data, ensure_ascii=False)
        # Fallback: RAG query
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.florence_url.rstrip('/')}/api/v1/rag/query",
                json={"query": prompt, "top_k": 3},
            )
            resp.raise_for_status()
            data = resp.json()
            return json.dumps(data.get("results", data), ensure_ascii=False)

    async def _call_geralda(self, prompt: str, patient_id: str | None = None) -> str:
        """Chama Geralda para plano de cuidado."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{self.geralda_url.rstrip('/')}/api/v1/patients/{patient_id or 'unknown'}/plan"
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                return json.dumps(resp.json(), ensure_ascii=False)
            except Exception:
                return f"Geralda: consulta sobre '{prompt[:50]}...' — módulo pode estar indisponível."

    async def generate_response(
        self,
        prompt: str,
        agent: str = "florence",
        context: dict | None = None,
    ) -> str:
        """Gera resposta completa (modo não-streaming)."""
        patient_id = None
        if context:
            if "patient" in context:
                ref = context["patient"]
                if isinstance(ref, str) and "Patient/" in ref:
                    patient_id = ref.split("/")[-1]
                elif isinstance(ref, dict) and ref.get("reference"):
                    patient_id = ref["reference"].split("/")[-1]

        if agent == "geralda":
            return await self._call_geralda(prompt, patient_id)
        if agent == "florence":
            return await self._call_florence_analyze(prompt, patient_id, context)
        # Default: Wanda (orquestra e escolhe)
        return await self._call_wanda(prompt, patient_id)

    async def stream_response(
        self,
        prompt: str,
        agent: str = "florence",
        context: dict | None = None,
    ) -> AsyncGenerator[str, None]:
        """Gera resposta em chunks (simulação de streaming).

        Wanda/Florence/Geralda não retornam streaming nativo — acumulamos
        a resposta e emitimos em chunks para simular SSE.
        """
        full_text = await self.generate_response(prompt, agent, context)
        # Emitir em chunks de ~50 chars para simular streaming
        chunk_size = 50
        for i in range(0, len(full_text), chunk_size):
            chunk = full_text[i : i + chunk_size]
            if chunk:
                yield chunk
            await asyncio.sleep(0.02)  # Pequeno delay para efeito de streaming

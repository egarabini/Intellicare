"""QwenClient — cliente LLM via Ollama (Qwen2.5-72B com fallback para 7B)."""

from __future__ import annotations

import json
import logging
import time
from typing import Optional

import httpx

from pierre.errors import LLMUnavailableError
from pierre.llm.prompts import (
    ANALYZE_PROMPT,
    AUDIENCE_INSTRUCTIONS,
    FORMAT_INSTRUCTIONS,
    SUMMARIZE_PROMPT,
    TRANSLATE_PROMPT,
)
from pierre.models import SummaryResult, TextAnalysisResult, TranslationResult

logger = logging.getLogger(__name__)


class QwenClient:
    """
    Cliente para Qwen2.5 via Ollama.
    Modelo primario: qwen2.5:72b (melhor qualidade)
    Modelo fallback: qwen2.5:7b (mais rapido, menor qualidade)

    Timeout: 120s para 72b, 30s para 7b
    """

    def __init__(
        self,
        ollama_url: str = "http://ollama:11434",
        model: str = "qwen2.5:72b",
        model_fallback: str = "qwen2.5:7b",
        timeout: int = 120,
        max_tokens: int = 500,
    ):
        self._ollama_url = ollama_url.rstrip("/")
        self._model = model
        self._model_fallback = model_fallback
        self._timeout = timeout
        self._max_tokens = max_tokens

    async def _chat(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> tuple[str, str]:
        """
        Envia chat para Ollama. Retorna (response_text, model_used).
        Tenta modelo primario, fallback para secundario.
        """
        target_model = model or self._model
        tokens = max_tokens or self._max_tokens

        for attempt_model in [target_model, self._model_fallback]:
            try:
                timeout = self._timeout if attempt_model == self._model else 30
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(
                        f"{self._ollama_url}/api/chat",
                        json={
                            "model": attempt_model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_message},
                            ],
                            "stream": False,
                            "options": {
                                "num_predict": tokens,
                                "temperature": 0.3,
                            },
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    content = data.get("message", {}).get("content", "")
                    return content, attempt_model
            except Exception as e:
                logger.warning("Ollama %s falhou: %s", attempt_model, e)
                if attempt_model == self._model_fallback:
                    raise LLMUnavailableError(
                        f"Ollama indisponivel — modelos {self._model} e {self._model_fallback} falharam: {e}"
                    )
                continue

        raise LLMUnavailableError("Ollama indisponivel")

    async def analyze(
        self,
        text: str,
        instruction: str,
        output_format: str = "bullet_points",
        max_tokens: int = 500,
        language: str = "pt-BR",
    ) -> TextAnalysisResult:
        """Analise de texto medico com prompt PIERRE."""
        t0 = time.monotonic()

        format_instr = FORMAT_INSTRUCTIONS.get(output_format, "")
        user_msg = f"""INSTRUCAO: {instruction}

{format_instr}

Responda em {language}.

TEXTO PARA ANALISAR:
---
{text[:100000]}
---"""

        try:
            response_text, model_used = await self._chat(ANALYZE_PROMPT, user_msg, max_tokens=max_tokens)

            # Tentar extrair key_points
            key_points = self._extract_bullet_points(response_text)
            confidence = 0.85 if len(response_text) > 50 else 0.5

            return TextAnalysisResult(
                analysis=response_text,
                key_points=key_points,
                confidence=confidence,
                model_used=model_used,
                processing_time_ms=int((time.monotonic() - t0) * 1000),
            )
        except LLMUnavailableError:
            return TextAnalysisResult(
                analysis="[ERRO] LLM indisponivel — Ollama nao acessivel ou modelo nao carregado.",
                confidence=0.0,
                model_used="none",
                processing_time_ms=int((time.monotonic() - t0) * 1000),
            )

    async def summarize(
        self,
        text: str,
        summary_type: str = "clinical_action",
        max_sentences: int = 5,
        target_audience: str = "medico",
        language: str = "pt-BR",
    ) -> SummaryResult:
        """Resume documento longo."""
        t0 = time.monotonic()

        audience_instr = AUDIENCE_INSTRUCTIONS.get(target_audience, "")
        user_msg = f"""TIPO DE RESUMO: {summary_type}
MAXIMO DE SENTENCAS: {max_sentences}
PUBLICO-ALVO: {target_audience}
{audience_instr}

Responda em {language}.

DOCUMENTO PARA RESUMIR:
---
{text[:100000]}
---"""

        try:
            response_text, model_used = await self._chat(SUMMARIZE_PROMPT, user_msg)
            key_actions = self._extract_bullet_points(response_text)

            return SummaryResult(
                summary=response_text,
                key_actions=key_actions,
                summary_type=summary_type,
                processing_time_ms=int((time.monotonic() - t0) * 1000),
            )
        except LLMUnavailableError:
            # Graceful degradation: retorna primeiros chars sem LLM
            truncated = text[:500].strip()
            return SummaryResult(
                summary=f"[RESUMO AUTOMATICO INDISPONIVEL — Ollama offline]\n\nPrimeiros 500 caracteres:\n{truncated}",
                summary_type=summary_type,
                processing_time_ms=int((time.monotonic() - t0) * 1000),
            )

    async def translate(
        self,
        text: str,
        source_language: str = "auto",
        preserve_medical_terms: bool = True,
        context: str = "medical_guideline",
        language: str = "pt-BR",
    ) -> TranslationResult:
        """Traduz texto medico para PT-BR."""
        t0 = time.monotonic()

        preserve_note = "Preserve termos medicos sem traducao consolidada." if preserve_medical_terms else ""
        user_msg = f"""IDIOMA FONTE: {source_language}
CONTEXTO: {context}
{preserve_note}

Traduza para {language}.

TEXTO:
---
{text[:50000]}
---"""

        try:
            response_text, model_used = await self._chat(TRANSLATE_PROMPT, user_msg)

            # Extrair termos preservados (palavras em ingles mantidas)
            preserved = self._detect_preserved_terms(text, response_text)

            return TranslationResult(
                translated_text=response_text,
                source_language_detected=source_language if source_language != "auto" else "en",
                medical_terms_preserved=preserved,
                confidence=0.90,
                processing_time_ms=int((time.monotonic() - t0) * 1000),
            )
        except LLMUnavailableError:
            return TranslationResult(
                translated_text=f"[TRADUCAO INDISPONIVEL — Ollama offline]\n\nTexto original:\n{text[:500]}",
                source_language_detected=source_language,
                confidence=0.0,
                processing_time_ms=int((time.monotonic() - t0) * 1000),
            )

    async def is_available(self, model: Optional[str] = None) -> bool:
        """Verifica se Ollama tem o modelo disponivel."""
        target = model or self._model
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self._ollama_url}/api/tags")
                if resp.status_code != 200:
                    return False
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return any(target in m for m in models)
        except Exception:
            return False

    @staticmethod
    def _extract_bullet_points(text: str) -> list[str]:
        """Extrai bullet points de um texto."""
        points = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith(("- ", "• ", "* ", "· ")):
                points.append(line[2:].strip())
            elif len(line) > 2 and line[0].isdigit() and line[1] in (".", ")"):
                points.append(line[2:].strip())
            elif len(line) > 3 and line[:2].isdigit() and line[2] in (".", ")"):
                points.append(line[3:].strip())
        return points[:10]  # Max 10

    @staticmethod
    def _detect_preserved_terms(original: str, translated: str) -> list[str]:
        """Detecta termos medicos mantidos sem traducao."""
        # Termos comuns que devem ser preservados
        common_medical_terms = [
            "SGLT2", "eGFR", "HbA1c", "KDIGO", "GOLD", "ACR", "IECA", "BRA",
            "TFG", "DRC", "DPOC", "HAS", "DM2", "IMC", "FHIR", "HL7",
            "GLP-1", "DPP-4", "PCR", "TSH", "PSA", "AINE", "ECA", "FDA",
            "ANVISA", "SUS", "SBN", "SBC", "CFM", "COFEN", "ANS",
        ]
        preserved = []
        for term in common_medical_terms:
            if term.lower() in original.lower() and term.lower() in translated.lower():
                preserved.append(term)
        return preserved

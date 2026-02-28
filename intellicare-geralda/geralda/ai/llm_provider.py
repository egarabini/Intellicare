"""LLM Provider Factory para Geralda.

Suporta múltiplos providers de LLM (Ollama, OpenAI, Anthropic)
com graceful degradation para modo sem IA.
"""

import logging
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel


logger = logging.getLogger(__name__)


class LLMProvider:
    """Factory para instanciar LLM conforme configuração."""

    @staticmethod
    def create(
        provider: str = "none",
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "mistral:7b",
        temperature: float = 0.3,
        context_size: int = 8192,
        timeout: int = 60,
        openai_api_key: Optional[str] = None,
        openai_model: str = "gpt-4o-mini",
    ) -> Optional[BaseChatModel]:
        """
        Cria instância de LLM conforme configuração.

        Args:
            provider: Tipo de provider ("ollama", "openai", "none")
            ollama_url: URL base do Ollama
            ollama_model: Modelo Ollama a usar
            temperature: Temperatura para geração
            context_size: Tamanho do contexto Ollama
            timeout: Timeout em segundos
            openai_api_key: API key da OpenAI
            openai_model: Modelo OpenAI

        Returns:
            BaseChatModel ou None (modo sem IA)
        """
        if provider == "none":
            logger.info("LLM disabled (mode: none)")
            return None

        elif provider == "ollama":
            try:
                from langchain_ollama import ChatOllama

                logger.info(f"Creating Ollama LLM: {ollama_model} at {ollama_url}")
                return ChatOllama(
                    model=ollama_model,
                    base_url=ollama_url,
                    temperature=temperature,
                    num_ctx=context_size,
                    timeout=timeout,
                )
            except ImportError as e:
                logger.error(f"langchain-ollama not installed: {e}")
                logger.warning("Falling back to mode without IA")
                return None
            except Exception as e:
                logger.error(f"Failed to create Ollama LLM: {e}")
                return None

        elif provider == "openai":
            if not openai_api_key:
                logger.warning("OpenAI provider selected but no API key provided")
                return None

            try:
                from langchain_openai import ChatOpenAI

                logger.info(f"Creating OpenAI LLM: {openai_model}")
                return ChatOpenAI(
                    model=openai_model,
                    api_key=openai_api_key,
                    temperature=temperature,
                )
            except ImportError as e:
                logger.error(f"langchain-openai not installed: {e}")
                logger.warning("Falling back to mode without IA")
                return None
            except Exception as e:
                logger.error(f"Failed to create OpenAI LLM: {e}")
                return None

        else:
            logger.warning(f"Unknown LLM provider: {provider}")
            return None

    @staticmethod
    async def check_availability(llm: Optional[BaseChatModel]) -> bool:
        """
        Verifica se LLM está disponível.

        Args:
            llm: Instância de LLM (pode ser None)

        Returns:
            True se disponível, False caso contrário
        """
        if llm is None:
            return False

        try:
            # Tenta invocar o LLM com um prompt simples
            from langchain_core.messages import HumanMessage

            response = await llm.ainvoke([HumanMessage(content="OK")])
            return response is not None
        except Exception as e:
            logger.warning(f"LLM not available: {e}")
            return False

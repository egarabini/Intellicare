"""Agente Geralda - Agente de acompanhamento de pacientes.

Orquestra LLM (Ollama/OpenAI) com tools LangChain para criar
uma experiência conversacional de cuidado ao paciente.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from geralda.ai.prompts import build_system_prompt, EMERGENCY_PROMPT, SAFETY_GUIDELINES
from geralda.ai.llm_provider import LLMProvider


logger = logging.getLogger(__name__)


class GeraldaAgent:
    """
    Agente de acompanhamento de pacientes.

    Usa LLM local (Ollama) ou cloud (OpenAI) para:
    - Interpretar solicitações de profissionais e pacientes
    - Executar ações através de tools LangChain
    - Gerar respostas contextualizadas em linguagem acessível
    """

    def __init__(
        self,
        llm: Optional[BaseChatModel],
        tools: Optional[list[BaseTool]] = None,
        session_factory: Optional[async_sessionmaker[AsyncSession]] = None,
    ):
        """
        Inicializa agente Geralda.

        Args:
            llm: Instância de LLM (Ollama/OpenAI ou None para modo sem IA)
            tools: Lista de tools LangChain disponíveis
            session_factory: Factory de sessões do banco de dados
        """
        self._llm = llm
        tools = tools or []
        self._tools = {tool.name: tool for tool in tools}
        self._session_factory = session_factory
        self._available_tools_desc = ", ".join(self._tools.keys())

    def _build_session(
        self,
        patient_context: str = "",
        history: Optional[list[dict]] = None,
    ) -> list[Any]:
        """
        Constrói sessão de chat com system prompt.

        Args:
            patient_context: Contexto do paciente
            history: Histórico de mensagens anteriores

        Returns:
            Lista de mensagens para o LLM
        """
        messages = []

        # System prompt com identidade e regras da Geralda
        system_prompt = build_system_prompt(
            patient_context=patient_context,
            available_tools=self._available_tools_desc,
        )
        messages.append(SystemMessage(content=system_prompt))

        # Adiciona diretrizes de segurança
        messages.append(SystemMessage(content=SAFETY_GUIDELINES))
        messages.append(SystemMessage(content=EMERGENCY_PROMPT))

        # Histórico de conversa (se fornecido)
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        return messages

    async def chat(
        self,
        message: str,
        patient_id: str,
        patient_context: str = "",
        history: Optional[list[dict]] = None,
        role: str = "patient",
    ) -> dict[str, Any]:
        """
        Processa mensagem do usuário e retorna resposta.

        Args:
            message: Mensagem do usuário
            patient_id: ID do paciente
            patient_context: Contexto clínico do paciente
            history: Histórico de conversa
            role: "patient" ou "professional"

        Returns:
            Dict com:
                - response: Resposta da Geralda
                - actions_taken: Lista de ações executadas
                - patient_id: ID do paciente
                - mode: "ai" ou "fallback"
        """
        # Modo sem IA (fallback)
        if self._llm is None:
            return await self._fallback_response(message, patient_id, role)

        try:
            # Constrói sessão de chat
            messages = self._build_session(patient_context, history)
            messages.append(HumanMessage(content=message))

            # Invoca LLM
            response = await self._llm.ainvoke(messages)
            response_text = response.content

            # TODO: Implementar invocação de tools (requer LangChain AgentExecutor)
            # Por enquanto, retorna resposta sem ações
            actions_taken = []

            return {
                "response": response_text,
                "actions_taken": actions_taken,
                "patient_id": patient_id,
                "mode": "ai",
                "timestamp": datetime.now(UTC).isoformat(),
                "metadata": {
                    "role": role,
                    "history_count": len(history or []),
                    "tools_available": list(self._tools.keys()),
                },
            }

        except Exception as e:
            logger.error(f"Error in AI mode: {e}")
            # Fallback para modo sem IA
            return await self._fallback_response(message, patient_id, role)

    async def _fallback_response(
        self,
        message: str,
        patient_id: str,
        role: str,
    ) -> dict[str, Any]:
        """
        Resposta de fallback quando LLM não está disponível.

        Args:
            message: Mensagem do usuário
            patient_id: ID do paciente
            role: "patient" ou "professional"

        Returns:
            Resposta padrão sem IA
        """
        # Detecta intenção básica por palavras-chave
        message_lower = message.lower()

        if any(word in message_lower for word in ["emergência", "urgente", "socorro", "dor no peito", "falta de ar"]):
            return {
                "response": EMERGENCY_PROMPT.strip(),
                "actions_taken": [],
                "patient_id": patient_id,
                "mode": "fallback",
                "timestamp": datetime.now(UTC).isoformat(),
                "metadata": {"role": role, "reason": "emergency_detected"},
            }

        if "plano" in message_lower and "cuidado" in message_lower:
            return {
                "response": f"Para ver seu plano de cuidado, acesse o portal ou entre em contato com sua equipe de saúde. (Modo sem IA - serviço de IA indisponível)",
                "actions_taken": [],
                "patient_id": patient_id,
                "mode": "fallback",
                "timestamp": datetime.now(UTC).isoformat(),
                "metadata": {"role": role, "reason": "care_plan_query"},
            }

        if "medicação" in message_lower or "remédio" in message_lower or "medicamento" in message_lower:
            return {
                "response": f"Para questões sobre medicação, entre em contato com sua equipe de saúde ou farmacêutico. Não altere doses sem orientação médica.",
                "actions_taken": [],
                "patient_id": patient_id,
                "mode": "fallback",
                "timestamp": datetime.now(UTC).isoformat(),
                "metadata": {"role": role, "reason": "medication_query"},
            }

        # Resposta padrão
        return {
            "response": f"Olá! Sou a Geralda, seu assistente de cuidado. No momento, meu serviço de IA não disponível (modo sem IA). Para dúvidas sobre seu plano de cuidado, entre em contato com sua equipe de saúde.",
            "actions_taken": [],
            "patient_id": patient_id,
            "mode": "fallback",
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": {"role": role, "reason": "default_fallback"},
        }

    async def create_care_plan(
        self,
        patient_id: str,
        patient_name: str,
        conditions: list,
        goals: list,
    ) -> dict[str, Any]:
        """
        Cria plano de cuidado usando IA (se disponível).

        Args:
            patient_id: ID do paciente
            patient_name: Nome do paciente
            conditions: Lista de condições
            goals: Lista de metas

        Returns:
            Resultado da criação
        """
        # Constrói prompt para criar plano
        prompt = f"""
Crie um plano de cuidado para {patient_name}.

Condições: {', '.join(str(c) for c in conditions)}
Metas: {', '.join(str(g) for g in goals)}

Forneça uma lista de 5-10 tarefas específicas e acionáveis.
"""

        if self._llm:
            try:
                response = await self._llm.ainvoke([HumanMessage(content=prompt)])
                return {
                    "success": True,
                    "suggestions": response.content,
                    "mode": "ai",
                }
            except Exception as e:
                logger.error(f"Error generating care plan: {e}")

        # Fallback
        return {
            "success": True,
            "suggestions": "Plano básico gerado (modo sem IA). Entre em contato com sua equipe para personalizar.",
            "mode": "fallback",
        }


def create_geralda_agent(
    llm_provider: str = "none",
    ollama_url: str = "http://localhost:11434",
    ollama_model: str = "mistral:7b",
    session_factory: Optional[async_sessionmaker[AsyncSession]] = None,
) -> GeraldaAgent:
    """
    Factory para criar agente Geralda.

    Args:
        llm_provider: Tipo de provider ("ollama", "openai", "none")
        ollama_url: URL do Ollama
        ollama_model: Modelo Ollama
        session_factory: Factory de sessões do banco

    Returns:
        Instância de GeraldaAgent
    """
    # Cria LLM
    llm = LLMProvider.create(
        provider=llm_provider,
        ollama_url=ollama_url,
        ollama_model=ollama_model,
    )

    # Cria tools (requer session_factory)
    tools = []
    if session_factory:
        from geralda.ai.tools.care_tools import get_care_tools
        from geralda.engine.care_manager import CareManager

        tools = get_care_tools(CareManager())

    # Cria agente
    return GeraldaAgent(
        llm=llm,
        tools=tools,
        session_factory=session_factory,
    )

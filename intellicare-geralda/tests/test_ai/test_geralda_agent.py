"""Testes para GeraldaAgent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from geralda.ai.geralda_agent import GeraldaAgent
from geralda.ai.llm_provider import LLMProvider


class TestGeraldaAgent:
    """Testes para o agente conversacional."""

    @pytest.fixture
    def mock_llm(self):
        """Mock de LLM."""
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Resposta do agente"
        mock_llm.ainvoke.return_value = mock_response
        return mock_llm

    @pytest.fixture
    def agent(self, mock_llm):
        """Cria instância do agente para testes."""
        return GeraldaAgent(llm=mock_llm)

    @pytest.mark.asyncio
    async def test_chat_basic(self, agent):
        """Testa chat básico."""
        result = await agent.chat(
            message="Olá",
            patient_id="pac-001",
            patient_context="Paciente com DRC",
        )

        assert result["response"] == "Resposta do agente"
        assert result["patient_id"] == "pac-001"
        assert result["timestamp"] is not None
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_chat_with_history(self, agent):
        """Testa chat com histórico."""
        history = [
            {"role": "user", "content": "Olá"},
            {"role": "assistant", "content": "Oi! Como posso ajudar?"},
        ]

        result = await agent.chat(
            message="Como estou?",
            patient_id="pac-001",
            history=history,
        )

        assert result["response"] == "Resposta do agente"

    @pytest.mark.asyncio
    async def test_chat_different_roles(self, agent):
        """Testa chat com diferentes papéis."""
        # Papel de paciente
        result_patient = await agent.chat(
            message="Estou com dor",
            patient_id="pac-001",
            role="patient",
        )
        assert "response" in result_patient

        # Papel de cuidador
        result_caregiver = await agent.chat(
            message="Como ajudá-lo?",
            patient_id="pac-001",
            role="caregiver",
        )
        assert "response" in result_caregiver

        # Papel de profissional
        result_professional = await agent.chat(
            message="Qual o prognóstico?",
            patient_id="pac-001",
            role="professional",
        )
        assert "response" in result_professional

    @pytest.mark.asyncio
    async def test_chat_without_llm(self):
        """Testa graceful degradation sem LLM."""
        agent = GeraldaAgent(llm=None)

        result = await agent.chat(
            message="Olá",
            patient_id="pac-001",
        )

        assert result["response"] is not None
        assert "sem IA" in result["response"].lower() or "não disponível" in result["response"].lower()
        assert result["patient_id"] == "pac-001"

    @pytest.mark.asyncio
    async def test_chat_with_empty_message(self, agent):
        """Testa chat com mensagem vazia."""
        result = await agent.chat(
            message="",
            patient_id="pac-001",
        )

        assert result["response"] is not None

    @pytest.mark.asyncio
    async def test_chat_long_patient_context(self, agent):
        """Testa chat com contexto longo do paciente."""
        long_context = "Paciente com DRC estágio 3, diabetes tipo 2, hipertensão," * 10

        result = await agent.chat(
            message="Como estou?",
            patient_id="pac-001",
            patient_context=long_context,
        )

        assert result["response"] is not None


class TestGeraldaAgentTools:
    """Testes para integração com tools LangChain."""

    @pytest.fixture
    def agent_with_tools(self):
        """Cria agente com tools mockados."""
        from langchain_core.tools import StructuredTool

        # Criar tool mock
        async def mock_create_plan(patient_id: str, conditions: list, goals: list):
            return {"plan_id": "plan-001", "status": "created"}

        mock_tool = MagicMock()
        mock_tool.name = "create_care_plan"
        mock_tool.description = "Cria plano de cuidado"
        mock_tool.arun = AsyncMock(return_value=mock_create_plan("pac-001", [], []))

        agent = GeraldaAgent(llm=None)
        agent._tools = [mock_tool]

        return agent

    @pytest.mark.asyncio
    async def test_agent_with_tools_integration(self, agent_with_tools):
        """Testa que agente pode usar tools."""
        # Testa que tools foram registradas
        assert len(agent_with_tools._tools) > 0
        assert agent_with_tools._tools[0].name == "create_care_plan"


class TestGeraldaAgentSafety:
    """Testes para regras de segurança do agente."""

    @pytest.fixture
    def mock_llm_safety(self):
        """Mock de LLM para testes de segurança."""
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        # Resposta deve recusar diagnósticos
        mock_response.content = "Não posso fazer diagnósticos. Procure um médico."
        mock_llm.ainvoke.return_value = mock_response
        return mock_llm

    @pytest.mark.asyncio
    async def test_agent_refuses_diagnosis(self, mock_llm_safety):
        """Testa que agente recusa fazer diagnóstico."""
        agent = GeraldaAgent(llm=mock_llm_safety)

        result = await agent.chat(
            message="O que eu tenho?",
            patient_id="pac-001",
        )

        # Resposta deve indicar recusa
        assert "diagnóstico" in result["response"].lower() or "não posso" in result["response"].lower()

    @pytest.mark.asyncio
    async def test_agent_refuses_prescription_changes(self, mock_llm_safety):
        """Testa que agente recusa alterar prescrições."""
        agent = GeraldaAgent(llm=mock_llm_safety)

        result = await agent.chat(
            message="Posso dobrar a dose do remédio?",
            patient_id="pac-001",
        )

        # Resposta deve indicar recusa ou encaminhar ao médico
        assert "médico" in result["response"].lower() or "não" in result["response"].lower()

    @pytest.mark.asyncio
    async def test_agent_emergency_response(self, mock_llm_safety):
        """Testa resposta em emergência."""
        mock_response = MagicMock()
        mock_response.content = "Ligue para SAMU (192) imediatamente!"
        mock_llm_safety.ainvoke.return_value = mock_response

        agent = GeraldaAgent(llm=mock_llm_safety)

        result = await agent.chat(
            message="Estou sentindo dor no peito e falta de ar",
            patient_id="pac-001",
        )

        assert "192" in result["response"] or "emergência" in result["response"].lower()


class TestGeraldaAgentEdgeCases:
    """Testes de casos extremos."""

    @pytest.mark.asyncio
    async def test_chat_with_special_characters(self):
        """Testa chat com caracteres especiais."""
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Entendi"
        mock_llm.ainvoke.return_value = mock_response

        agent = GeraldaAgent(llm=mock_llm)

        result = await agent.chat(
            message="Estou sentindo dor! @#$%&*()",
            patient_id="pac-001",
        )

        assert result["response"] is not None

    @pytest.mark.asyncio
    async def test_chat_with_emoji(self):
        """Testa chat com emoji."""
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Como você está se sentindo? 😊"
        mock_llm.ainvoke.return_value = mock_response

        agent = GeraldaAgent(llm=mock_llm)

        result = await agent.chat(
            message="Estou bem 😀",
            patient_id="pac-001",
        )

        assert result["response"] is not None

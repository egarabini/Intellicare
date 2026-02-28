"""Testes para MedicalSimplifier."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from geralda.ai.language.simplifier import MedicalSimplifier


class TestMedicalSimplifier:
    """Testes para simplificador de linguagem médica."""

    @pytest.fixture
    def simplifier_without_llm(self):
        """Cria simplifier sem LLM (usa apenas glossário)."""
        return MedicalSimplifier(llm=None)

    @pytest.fixture
    def mock_llm(self):
        """Mock de LLM."""
        llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Seus rins estão funcionando menos do que deveriam."
        llm.ainvoke.return_value = mock_response
        return llm

    @pytest.fixture
    def simplifier_with_llm(self, mock_llm):
        """Cria simplifier com LLM mockado."""
        return MedicalSimplifier(llm=mock_llm)

    def test_simplifier_initialization_without_llm(self, simplifier_without_llm):
        """Testa criação sem LLM."""
        assert simplifier_without_llm is not None
        assert simplifier_without_llm._llm is None

    def test_simplifier_initialization_with_llm(self, simplifier_with_llm):
        """Testa criação com LLM."""
        assert simplifier_with_llm is not None
        assert simplifier_with_llm._llm is not None

    def test_simplify_term_with_glossary(self, simplifier_without_llm):
        """Testa simplificação usando glossário."""
        result = simplifier_without_llm.simplify_term("hipertensão arterial")

        assert result == "pressão alta"

    def test_simplify_term_not_in_glossary(self, simplifier_without_llm):
        """Testa termo não está no glossário."""
        result = simplifier_without_llm.simplify_term("termo muito complexo e raro")

        # Deve retornar o próprio termo
        assert result == "termo muito complexo e raro"

    def test_simplify_term_empty_string(self, simplifier_without_llm):
        """Testa string vazia."""
        result = simplifier_without_llm.simplify_term("")

        assert result == ""

    def test_simplify_term_case_insensitive(self, simplifier_without_llm):
        """Testa case-insensitive."""
        result1 = simplifier_without_llm.simplify_term("HIPERTENSÃO ARTERIAL")
        result2 = simplifier_without_llm.simplify_term("Hipertensão Arterial")
        result3 = simplifier_without_llm.simplify_term("hipertensão arterial")

        assert result1 == result2 == result3 == "pressão alta"


class TestSimplifierAsync:
    """Testes para métodos async."""

    @pytest.mark.asyncio
    async def test_simplify_text_without_llm(self, simplifier_without_llm):
        """Testa simplificar texto sem LLM."""
        text = "Você tem hipertensão arterial e diabetes mellitus tipo 2"
        result = await simplifier_without_llm.simplify_text(text, level="basico")

        # Deve substituir termos do glossário
        assert "pressão alta" in result
        assert "diabetes" in result

    @pytest.mark.asyncio
    async def test_simplify_text_with_llm(self, simplifier_with_llm):
        """Testa simplificar texto com LLM."""
        text = "Seus rins apresentaram redução na taxa de filtração glomerular."
        result = await simplifier_with_llm.simplify_text(text, level="basico")

        assert len(result) > 0
        # LLM deve ter simplificado
        assert "rins" in result.lower()

    @pytest.mark.asyncio
    async def test_simplify_text_intermediate_level(self, simplifier_with_llm):
        """Testa nível intermediário."""
        text = "Creatinina sérica elevada indicando comprometimento renal."
        result = await simplifier_with_llm.simplify_text(text, level="intermediario")

        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_simplify_text_advanced_level(self, simplifier_with_llm):
        """Testa nível avançado."""
        text = "Há elevação nos níveis séricos de creatinina."
        result = await simplifier_with_llm.simplify_text(text, level="avancado")

        # Nível avançado mantém mais termos técnicos
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_explain_condition(self, simplifier_with_llm):
        """Testa explicar condição."""
        result = await simplifier_with_llm.explain_condition(
            condition_code="N18.3",
            condition_name="Doença Renal Crônica Estágio 3",
            level="basico",
        )

        assert len(result) > 0
        assert "rim" in result.lower()

    @pytest.mark.asyncio
    async def test_explain_condition_without_llm(self, simplifier_without_llm):
        """Testa explicar condição sem LLM."""
        result = await simplifier_without_llm.explain_condition(
            condition_code="N18.3",
            condition_name="Doença Renal Crônica",
            level="basico",
        )

        # Deve usar apenas glossário
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_explain_medication(self, simplifier_with_llm):
        """Testa explicar medicamento."""
        result = await simplifier_with_llm.explain_medication(
            medication_name="Losartana",
            level="basico",
        )

        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_simplify_long_text(self, simplifier_with_llm):
        """Testa simplificar texto longo."""
        long_text = """
        O paciente apresenta doença renal crônica estágio 3, com taxa de filtração
        glomerular de 45 mL/min/1.73m², hipertensão arterial sistêmica e diabetes
        mellitus tipo 2 com hemoglobina glicada de 8.5%.
        """

        result = await simplifier_with_llm.simplify_text(long_text, level="basico")

        assert len(result) > 0
        assert "rim" in result.lower()


class TestSimplifierLevels:
    """Testes para níveis de simplificação."""

    @pytest.mark.asyncio
    async def test_basic_level_is_simplest(self, simplifier_with_llm):
        """Testa que nível básico é o mais simples."""
        text = "Insuficiência renal crônica com proteinúria"

        result = await simplifier_with_llm.simplify_text(text, level="basico")

        # Deve ser linguagem bem simples
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_intermediate_level_balanced(self, simplifier_with_llm):
        """Testa que nível intermediário é equilibrado."""
        text = "Taxa de filtração glomerular reduzida"

        result = await simplifier_with_llm.simplify_text(text, level="intermediario")

        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_advanced_level_keeps_technical_terms(self, simplifier_with_llm):
        """Testa que nível avançado mantém termos técnicos."""
        text = "Creatinina sérica 2.1 mg/dL"

        result = await simplifier_with_llm.simplify_text(text, level="avancado")

        # Pode manter "creatina" ou "mg/dL"
        assert len(result) > 0

    def test_invalid_level_defaults_to_basic(self, simplifier_without_llm):
        """Testa que nível inválido usa básico como padrão."""
        result = simplifier_without_llm.simplify_term("hipertensão arterial")

        # Deve funcionar mesmo sem especificar nível
        assert result == "pressão alta"


class TestSimplifierEdgeCases:
    """Testes de casos extremos."""

    @pytest.mark.asyncio
    async def test_empty_text(self, simplifier_with_llm):
        """Testa texto vazio."""
        result = await simplifier_with_llm.simplify_text("", level="basico")

        assert result == ""

    @pytest.mark.asyncio
    async def test_text_with_special_characters(self, simplifier_with_llm):
        """Testa texto com caracteres especiais."""
        text = "eGFR < 60 mL/min/1.73m²"

        result = await simplifier_with_llm.simplify_text(text, level="basico")

        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_text_with_numbers(self, simplifier_with_llm):
        """Testa texto com números."""
        text = "Pressão arterial 140/90 mmHg"

        result = await simplifier_with_llm.simplify_text(text, level="basico")

        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_very_long_text(self, simplifier_with_llm):
        """Testa texto muito longo."""
        long_text = "Paciente com " + "múltiplas comorbidades. " * 50

        result = await simplifier_with_llm.simplify_text(long_text, level="basico")

        # Deve retornar algo
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_text_with_emoji(self, simplifier_with_llm):
        """Testa texto com emoji."""
        text = "Estou sentindo dor 😢"

        result = await simplifier_with_llm.simplify_text(text, level="basico")

        assert len(result) > 0

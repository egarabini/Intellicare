"""Testes para system prompt e prompts de cuidado."""

import pytest

from geralda.ai.prompts.system_prompt import GERALDA_SYSTEM_PROMPT
from geralda.ai.prompts.care_prompts import (
    CREATE_CARE_PLAN_PROMPT,
    EXPLAIN_TASK_PROMPT,
    ADHERENCE_ANALYSIS_PROMPT,
    MOTIVATIONAL_MESSAGE_PROMPT,
)


class TestSystemPrompt:
    """Testes para system prompt da Geralda."""

    def test_system_prompt_exists(self):
        """Testa que system prompt está definido."""
        assert GERALDA_SYSTEM_PROMPT is not None
        assert len(GERALDA_SYSTEM_PROMPT) > 0

    def test_system_prompt_has_identity(self):
        """Testa que system prompt define identidade."""
        assert "Geralda" in GERALDA_SYSTEM_PROMPT
        assert "IntelliCare" in GERALDA_SYSTEM_PROMPT

    def test_system_prompt_has_safety_rules(self):
        """Testa que system prompt tem regras de segurança."""
        assert "NUNCA" in GERALDA_SYSTEM_PROMPT or "regras" in GERALDA_SYSTEM_PROMPT.lower()

    def test_system_prompt_has_role_definition(self):
        """Testa que system prompt define papel."""
        assert "acompanhamento" in GERALDA_SYSTEM_PROMPT.lower()


class TestCarePrompts:
    """Testes para prompts de cuidado."""

    def test_create_care_plan_prompt_exists(self):
        """Testa que prompt para criar plano existe."""
        assert CREATE_CARE_PLAN_PROMPT is not None
        assert len(CREATE_CARE_PLAN_PROMPT) > 0
        assert "plano de cuidado" in CREATE_CARE_PLAN_PROMPT.lower()

    def test_explain_task_prompt_exists(self):
        """Testa que prompt para explicar tarefa existe."""
        assert EXPLAIN_TASK_PROMPT is not None
        assert len(EXPLAIN_TASK_PROMPT) > 0
        assert "explique" in EXPLAIN_TASK_PROMPT.lower()

    def test_adherence_analysis_prompt_exists(self):
        """Testa que prompt para análise de adesão existe."""
        assert ADHERENCE_ANALYSIS_PROMPT is not None
        assert len(ADHERENCE_ANALYSIS_PROMPT) > 0
        assert "adesão" in ADHERENCE_ANALYSIS_PROMPT.lower()

    def test_motivational_message_prompt_exists(self):
        """Testa que prompt para mensagem motivacional existe."""
        assert MOTIVATIONAL_MESSAGE_PROMPT is not None
        assert len(MOTIVATIONAL_MESSAGE_PROMPT) > 0
        assert "motivacional" in MOTIVATIONAL_MESSAGE_PROMPT.lower()


class TestPromptPlaceholders:
    """Testes para placeholders em prompts."""

    def test_plan_prompt_handles_empty_lists(self):
        """Testa prompt com listas vazias."""
        prompt = create_plan_prompt(
            conditions=[],
            goals=[],
        )

        assert prompt is not None
        assert len(prompt) > 0

    def test_plan_prompt_handles_special_characters(self):
        """Testa prompt com caracteres especiais."""
        prompt = create_plan_prompt(
            conditions=["DRC estágio 3 (CKD-EPI <60)"],
            goals=["eGFR >45 mL/min/1.73m²"],
        )

        assert "(" in prompt or ")" in prompt
        assert "²" in prompt or "2" in prompt

    def test_education_prompt_handles_long_text(self):
        """Testa prompt com texto longo."""
        long_topic = "Dieta para pacientes com doença renal crônica estágio 3 com restrição de sódio, potássio e fósforo"
        prompt = education_search_prompt(
            condition="DRC",
            topic=long_topic,
            reading_level="basico",
        )

        assert long_topic in prompt


class TestPromptFormatting:
    """Testes para formatação de prompts."""

    def test_system_prompt_has_proper_structure(self):
        """Testa que system prompt tem estrutura adequada."""
        # Deve ter quebras de linha
        assert "\n" in GERALDA_SYSTEM_PROMPT

        # Deve ter seções
        sections = GERALDA_SYSTEM_PROMPT.split("\n\n")
        assert len(sections) > 1

    def test_care_prompts_are_not_empty(self):
        """Testa que prompts de cuidado não são vazios."""
        prompts = [
            create_plan_prompt(["DRC"], ["Controle"]),
            adherence_check_prompt(5, 3, 2),
            education_search_prompt("DRC", "Dieta", "basico"),
            reminder_customization_prompt("Tomar remédio", "08:00", "curto"),
            task_explanation_prompt("Exame", "Check", "DRC"),
        ]

        for prompt in prompts:
            assert len(prompt) > 0
            assert isinstance(prompt, str)


class TestPromptSafety:
    """Testes para segurança em prompts."""

    def test_system_prompt_emphasizes_safety(self):
        """Testa que system prompt enfatiza segurança."""
        # Deve mencionar limites
        safety_keywords = ["médico", "profissional", "emergência", "samu"]
        has_safety = any(keyword in GERALDA_SYSTEM_PROMPT.lower() for keyword in safety_keywords)
        assert has_safety

    def test_prompts_do_not_encourage_dangerous_behavior(self):
        """Testa que prompts não encorajam comportamentos perigosos."""
        # Prompts não devem sugerir automedicação
        prompt = reminder_customization_prompt(
            task="Tomar medicamento",
            time="08:00",
            patient_preference="curto",
        )

        # Não deve sugerir alterar doses
        assert "aumentar" not in prompt.lower() or "dose" not in prompt.lower()

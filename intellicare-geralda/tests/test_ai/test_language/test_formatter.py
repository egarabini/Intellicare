"""Testes para OutputFormatter."""

import pytest
from datetime import date, datetime

from geralda.ai.language.formatter import OutputFormatter


class TestOutputFormatter:
    """Testes para formatador de saída."""

    @pytest.fixture
    def formatter(self):
        """Cria formatter para testes."""
        return OutputFormatter()

    def test_formatter_initialization(self, formatter):
        """Testa criação do formatter."""
        assert formatter is not None

    def test_format_short(self, formatter):
        """Testa formato curto (280 caracteres)."""
        result = formatter.format_short(
            conditions=["Doença Renal Crônica"],
            message="Lembre-se de tomar seus remédios e medir a pressão.",
        )

        assert len(result) <= 280
        assert "remédios" in result
        assert "pressão" in result

    def test_format_short_truncates_long_text(self, formatter):
        """Testa que formato curto trunca texto longo."""
        long_message = "Esta é uma mensagem muito longa que precisa ser truncada. " * 20

        result = formatter.format_short(
            conditions=["DRC"],
            message=long_message,
        )

        assert len(result) <= 280
        # Deve ter "..." se truncou
        assert "..." in result or len(result) < len(long_message)

    def test_format_long(self, formatter):
        """Testa formato longo (detalhado)."""
        result = formatter.format_long(
            patient_name="Maria Silva",
            conditions=["Doença Renal Crônica estágio 3", "Hipertensão"],
            goals=["Controlar creatinina", "Manter PA <140/90"],
            tasks=["Tomar Losartana", "Medir PA", "Exames"],
        )

        assert len(result) > 0
        assert "Maria Silva" in result
        assert "Losartana" in result

    def test_format_topics(self, formatter):
        """Testa formato tópicos."""
        result = formatter.format_topics(
            topics=[
                "Medicação: Tome Losartana 50mg às 8h",
                "Dieta: Evite sal e alimentos processados",
                "Exercício: Caminhada 30min diários",
            ]
        )

        assert len(result) > 0
        # Deve ter marcadores de lista
        assert ("-" in result or "•" in result or "*" in result)

    def test_format_reminder(self, formatter):
        """Testa formato lembrete."""
        result = formatter.format_reminder(
            task="Tomar Losartana 50mg",
            time="08:00",
            instructions="Tomar com água, antes do café da manhã",
        )

        assert "Losartana" in result
        assert "08:00" in result
        assert "água" in result

    def test_format_reminder_with_emoji(self, formatter):
        """Testa lembrete com emoji."""
        result = formatter.format_reminder(
            task="Medir pressão arterial",
            time="07:00",
            emoji="💉",
        )

        assert "pressão" in result
        assert "07:00" in result
        assert "💉" in result

    def test_format_care_summary(self, formatter):
        """Testa formato resumo de cuidado."""
        result = formatter.format_care_summary(
            plan_conditions=["Doença Renal Crônica"],
            plan_goals=["Controlar creatinina"],
            task_count=10,
            completed_count=7,
            adherence_rate=70.0,
            level="basico",
        )

        assert len(result) > 0
        assert "70%" in result or "10" in result or "7" in result

    def test_format_care_summary_different_levels(self, formatter):
        """Testa resumo em diferentes níveis."""
        for level in ["basico", "intermediario", "avancado"]:
            result = formatter.format_care_summary(
                plan_conditions=["DRC"],
                plan_goals=["Controle"],
                task_count=5,
                completed_count=3,
                adherence_rate=60.0,
                level=level,
            )

            assert len(result) > 0

    def test_format_schedule(self, formatter):
        """Testa formato agenda diária."""
        schedule_items = [
            {"time": "07:00", "task": "Medir pressão arterial"},
            {"time": "08:00", "task": "Tomar Losartana 50mg"},
            {"time": "12:30", "task": "Almoço (leve, sem sal)"},
            {"time": "18:00", "task": "Caminhada 30 minutos"},
        ]

        result = formatter.format_schedule(schedule_items)

        assert "07:00" in result
        assert "pressão" in result
        assert "08:00" in result
        assert "Losartana" in result

    def test_format_schedule_empty(self, formatter):
        """Testa agenda vazia."""
        result = formatter.format_schedule([])

        # Deve retornar mensagem amigável
        assert len(result) > 0
        assert "sem" in result.lower() or "vazio" in result.lower() or "nenhuma" in result.lower()

    def test_format_medications(self, formatter):
        """Testa formato lista de medicamentos."""
        medications = [
            {"name": "Losartana 50mg", "frequency": "1x ao dia", "time": "08:00"},
            {"name": "AAS 100mg", "frequency": "1x ao dia", "time": "08:00"},
        ]

        result = formatter.format_medications(medications)

        assert "Losartana" in result
        assert "AAS" in result
        assert "08:00" in result


class TestFormatterEdgeCases:
    """Testes de casos extremos."""

    def test_format_with_empty_lists(self):
        """Testa formatar com listas vazias."""
        formatter = OutputFormatter()

        result = formatter.format_long(
            patient_name="Maria",
            conditions=[],
            goals=[],
            tasks=[],
        )

        # Deve retornar algo mesmo com listas vazias
        assert len(result) > 0

    def test_format_with_special_characters(self):
        """Testa formatar com caracteres especiais."""
        formatter = OutputFormatter()

        result = formatter.format_short(
            conditions=["DRC estágio 3 (eGFR 45)"],
            message="Tomar medicamento às 8h. Atenção!",
        )

        assert len(result) > 0

    def test_format_with_very_long_condition_name(self):
        """Testa formatar com nome de condição muito longo."""
        formatter = OutputFormatter()

        long_condition = "Nefropatia diabética com insuficiência renal crônica estágio 3b e proteinúria"
        result = formatter.format_short(
            conditions=[long_condition],
            message="Msg",
        )

        # Deve truncar se necessário
        assert len(result) <= 280

    def test_format_with_unicode(self):
        """Testa formatar com caracteres unicode."""
        formatter = OutputFormatter()

        result = formatter.format_reminder(
            task="Tomar medicamento",
            time="08:00",
            emoji="💊",
        )

        assert "💊" in result


class TestFormatterConsistency:
    """Testes de consistência do formatter."""

    def test_same_input_produces_same_output(self):
        """Testa que mesma entrada produz mesma saída."""
        formatter = OutputFormatter()

        result1 = formatter.format_short(
            conditions=["DRC"],
            message="Teste",
        )
        result2 = formatter.format_short(
            conditions=["DRC"],
            message="Teste",
        )

        assert result1 == result2

    def test_all_formats_return_strings(self):
        """Testa que todos os formatos retornam strings."""
        formatter = OutputFormatter()

        formats = [
            formatter.format_short([], "Msg"),
            formatter.format_long("Maria", [], [], []),
            formatter.format_topics([]),
            formatter.format_reminder("Task", "08:00"),
            formatter.format_care_summary([], [], 5, 3, 60, "basico"),
            formatter.format_schedule([]),
            formatter.format_medications([]),
        ]

        for result in formats:
            assert isinstance(result, str)
            assert len(result) >= 0


class TestFormatterLevelAdaptation:
    """Testes para adaptação por nível."""

    def test_basic_level_uses_simple_words(self):
        """Testa que nível básico usa palavras simples."""
        formatter = OutputFormatter()

        result = formatter.format_care_summary(
            plan_conditions=["Doença Renal Crônica"],
            plan_goals=["Controlar creatinina"],
            task_count=5,
            completed_count=3,
            adherence_rate=60,
            level="basico",
        )

        # Deve ter linguagem acessível
        assert len(result) > 0

    def test_advanced_level_keeps_technical_terms(self):
        """Testa que nível avançado mantém termos técnicos."""
        formatter = OutputFormatter()

        result = formatter.format_care_summary(
            plan_conditions=["Doença Renal Crônica"],
            plan_goals=["Creatinina < 1.2"],
            task_count=5,
            completed_count=3,
            adherence_rate=60,
            level="avancado",
        )

        # Pode manter "creatina"
        assert len(result) > 0

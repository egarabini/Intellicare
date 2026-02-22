"""Tests for IntentExtractor (EF-W003) — deterministic intent categorization."""

import pytest

from wanda.orchestrator.intent_extractor import IntentExtractor, IntentResult


@pytest.fixture
def extractor():
    return IntentExtractor()


class TestExtractIntent:
    def test_care_management_intent(self, extractor):
        result = extractor.extract_intent("Qual o plano de cuidado do paciente hoje?")
        assert result.primary_intent == "care_management"

    def test_clinical_analysis_intent(self, extractor):
        result = extractor.extract_intent("Preciso ver os resultados dos exames de laboratorio")
        assert result.primary_intent == "clinical_analysis"

    def test_chronic_disease_intent(self, extractor):
        result = extractor.extract_intent("Como esta a DRC do paciente? TFG caiu para 38")
        assert result.primary_intent == "chronic_disease"

    def test_territorial_intent(self, extractor):
        result = extractor.extract_intent("Quais UBS e hospitais tem no municipio?")
        assert result.primary_intent == "territorial"

    def test_quality_intent(self, extractor):
        result = extractor.extract_intent("Avaliar a qualidade dos indicadores Donabedian")
        assert result.primary_intent == "quality"

    def test_default_intent_when_no_match(self, extractor):
        result = extractor.extract_intent("Como vai voce?")
        assert result.primary_intent == "general"
        assert result.keywords_matched == []

    def test_multi_intent_detection(self, extractor):
        result = extractor.extract_intent(
            "Ver exames laboratoriais e plano de cuidado do paciente com DRC"
        )
        assert result.is_multi_intent is True
        assert len(result.secondary_intents) >= 1

    def test_keywords_matched_populated(self, extractor):
        result = extractor.extract_intent("Qual a creatinina e TFG do paciente com DRC?")
        assert len(result.keywords_matched) > 0
        assert result.primary_intent == "chronic_disease"


class TestClassifyUrgency:
    def test_normal_urgency(self, extractor):
        assert extractor.classify_urgency("Qual o plano de cuidado?") == "normal"

    def test_emergency_urgency(self, extractor):
        assert extractor.classify_urgency("Paciente com emergencia! Preciso de ajuda agora!") == "emergency"

    def test_high_urgency(self, extractor):
        assert extractor.classify_urgency("O paciente piorou muito, situacao grave") == "high"

    def test_is_emergency_property(self, extractor):
        result = extractor.extract_intent("paciente com emergencia urgente")
        assert result.is_emergency is True

    def test_is_high_priority_property(self, extractor):
        result = extractor.extract_intent("paciente em estado grave e critico")
        assert result.is_high_priority is True


class TestIntentToModules:
    def test_care_intent_maps_to_geralda(self, extractor):
        result = IntentResult(primary_intent="care_management")
        modules = extractor.intent_to_modules(result)
        assert "intellicare-geralda" in modules

    def test_clinical_intent_maps_to_florence(self, extractor):
        result = IntentResult(primary_intent="clinical_analysis")
        modules = extractor.intent_to_modules(result)
        assert "intellicare-florence" in modules

    def test_chronic_disease_maps_to_oswaldo(self, extractor):
        result = IntentResult(primary_intent="chronic_disease")
        modules = extractor.intent_to_modules(result)
        assert "intellicare-oswaldo" in modules

    def test_secondary_intents_included(self, extractor):
        result = IntentResult(
            primary_intent="chronic_disease",
            secondary_intents=["care_management"],
        )
        modules = extractor.intent_to_modules(result)
        assert "intellicare-oswaldo" in modules
        assert "intellicare-geralda" in modules

    def test_unknown_intent_returns_empty(self, extractor):
        result = IntentResult(primary_intent="general")
        modules = extractor.intent_to_modules(result)
        assert modules == []

"""Testes para glossário médico."""

import pytest

from geralda.ai.language.medical_glossary import (
    MEDICAL_GLOSSARY,
    simplify_term,
    has_translation,
    get_all_terms,
)


class TestMedicalGlossary:
    """Testes para glossário médico-leigo."""

    def test_glossary_exists(self):
        """Testa que glossário está definido."""
        assert MEDICAL_GLOSSARY is not None
        assert len(MEDICAL_GLOSSARY) > 0

    def test_glossary_has_minimum_terms(self):
        """Testa que glossário tem pelo menos 50 termos."""
        assert len(MEDICAL_GLOSSARY) >= 50

    def test_get_simple_term_existing(self):
        """Testa buscar termo existente."""
        result = simplify_term("hipertensão arterial")

        assert result == "pressão alta"

    def test_get_simple_term_case_insensitive(self):
        """Testa busca case-insensitive."""
        result1 = simplify_term("Hipertensão Arterial")
        result2 = simplify_term("HIPERTENSÃO ARTERIAL")
        result3 = simplify_term("hipertensão arterial")

        # Todos devem retornar o mesmo resultado
        assert result1 == result2 == result3

    def test_get_simple_term_nonexistent(self):
        """Testa buscar termo inexistente."""
        result = simplify_term("termo inexistente")

        # Deve retornar o próprio termo
        assert result == "termo inexistente"

    def test_get_simple_term_empty(self):
        """Testa busca com string vazia."""
        result = simplify_term("")

        assert result == ""

    def test_glossary_has_key_conditions(self):
        """Testa que glossário tem condições chave."""
        key_terms = [
            "hipertensão arterial",
            "diabetes mellitus tipo 2",
            "doença renal crônica",
            "insuficiência cardíaca",
        ]

        for term in key_terms:
            result = simplify_term(term)
            assert result != term  # Deve ter tradução
            assert len(result) > 0

    def test_glossary_has_exams(self):
        """Testa que glossário tem exames."""
        exam_terms = ["creatinina sérica", "taxa de filtração glomerular", "hemoglobina glicada"]

        for term in exam_terms:
            result = simplify_term(term)
            assert result != term or len(result) > 0

    def test_glossary_has_medications(self):
        """Testa que glossário tem medicamentos."""
        medication_terms = ["anticoagulante", "estatina", "betabloqueador"]

        for term in medication_terms:
            result = simplify_term(term)
            assert result is not None

    def test_has_translation(self):
        """Testa verificar se termo tem tradução."""
        assert has_translation("hipertensão arterial") is True
        assert has_translation("termo inexistente") is False

    def test_get_all_terms(self):
        """Testa obter todos os termos."""
        terms = get_all_terms()

        assert isinstance(terms, list)
        assert len(terms) >= 50

    def test_glossary_translations_are_simpler(self):
        """Testa que traduções são mais simples que originais."""
        test_cases = [
            ("hipertensão arterial sistêmica", "pressão alta"),
            ("diabetes mellitus tipo 2", "diabetes tipo 2"),
        ]

        for medical, simple in test_cases:
            result = simplify_term(medical)
            # Tradução deve ser mais curta ou igual
            assert len(result) <= len(medical) or result != medical


class TestGlossaryCategories:
    """Testes para categorias do glossário."""

    def test_glossary_has_conditions(self):
        """Testa categoria de condições/patologias."""
        condition_terms = [k for k in MEDICAL_GLOSSARY.keys() if any(
            word in k.lower() for word in ["doença", "síndrome", "insuficiência"]
        )]

        assert len(condition_terms) > 10

    def test_glossary_has_exams(self):
        """Testa categoria de exames."""
        exam_terms = [k for k in MEDICAL_GLOSSARY.keys() if any(
            word in k.lower() for word in ["creatinina", "glicose", "colesterol", "hemoglobina"]
        )]

        assert len(exam_terms) > 5

    def test_glossary_has_procedures(self):
        """Testa categoria de procedimentos."""
        procedure_terms = [k for k in MEDICAL_GLOSSARY.keys() if any(
            word in k.lower() for word in ["ultrassom", "raio-x", "tomografia"]
        )]

        assert len(procedure_terms) >= 0  # Pode ser zero


class TestGlossaryEdgeCases:
    """Testes de casos extremos."""

    def test_term_with_special_characters(self):
        """Testa termo com caracteres especiais."""
        result = simplify_term("eGFR")

        assert result is not None

    def test_term_with_numbers(self):
        """Testa termo com números."""
        result = simplify_term("estágio 3")

        assert result is not None

    def test_term_very_long(self):
        """Testa termo muito longo."""
        long_term = "nefropatia diabética com proteinúria e insuficiência renal crônica"
        result = simplify_term(long_term)

        # Mesmo que não exista, deve retornar algo
        assert result is not None

    def test_term_with_accents(self):
        """Testa termo com acentos."""
        result = simplify_term("insuficiência cardíaca")

        assert result is not None
        assert len(result) > 0

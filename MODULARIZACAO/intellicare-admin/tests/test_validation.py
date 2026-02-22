"""Tests for CNPJ validation and slug generation."""

import pytest
from admin.models.tenant import validate_cnpj, generate_slug


class TestValidateCNPJ:
    """Test CNPJ validation with check digit verification."""

    def test_valid_cnpj_formatted(self):
        """Valid CNPJ with formatting."""
        assert validate_cnpj("11.222.333/0001-81") is True

    def test_valid_cnpj_unformatted(self):
        """Valid CNPJ without formatting."""
        assert validate_cnpj("11222333000181") is True

    def test_invalid_cnpj_wrong_digits(self):
        """CNPJ with wrong check digits."""
        assert validate_cnpj("11.222.333/0001-99") is False

    def test_invalid_cnpj_too_short(self):
        """CNPJ with too few digits."""
        assert validate_cnpj("123456") is False

    def test_invalid_cnpj_all_same(self):
        """CNPJ with all same digits (e.g. 11111111111111)."""
        assert validate_cnpj("11111111111111") is False

    def test_invalid_cnpj_empty(self):
        """Empty string CNPJ."""
        assert validate_cnpj("") is False

    def test_valid_cnpj_real_example(self):
        """Known valid CNPJ (Petrobras)."""
        assert validate_cnpj("33.000.167/0001-01") is True

    def test_invalid_cnpj_first_digit_wrong(self):
        """CNPJ where only first check digit is wrong."""
        assert validate_cnpj("11.222.333/0001-71") is False


class TestGenerateSlug:
    """Test slug generation from company names."""

    def test_simple_name(self):
        slug = generate_slug("Hospital Einstein")
        assert slug == "hospital_einstein"

    def test_accented_name(self):
        slug = generate_slug("Clínica São José")
        assert slug == "clinica_sao_jose"

    def test_special_characters(self):
        slug = generate_slug("UBS #1 - Centro & Sul")
        assert slug == "ubs_1_centro_sul"

    def test_leading_trailing_spaces(self):
        slug = generate_slug("  Hospital Norte  ")
        assert slug == "hospital_norte"

    def test_cedilla(self):
        slug = generate_slug("Fundação Saúde")
        assert slug == "fundacao_saude"

    def test_max_length(self):
        long_name = "A" * 200
        slug = generate_slug(long_name)
        assert len(slug) <= 63

    def test_multiple_spaces(self):
        slug = generate_slug("Hospital    do   Campo")
        assert slug == "hospital_do_campo"

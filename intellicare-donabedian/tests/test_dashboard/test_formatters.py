"""
Tests for Dashboard Formatters.
"""

import pytest
from datetime import date, datetime

from donabedian.dashboard.utils.formatters import (
    format_score,
    format_percentage,
    format_date,
    format_value,
    format_integer,
    format_triad_name,
    format_pillar_name,
    format_status,
)


@pytest.mark.unit
@pytest.mark.dashboard
class TestFormatters:
    """Test cases for dashboard formatters."""
    
    def test_format_score_valid(self):
        """Test format_score with valid values."""
        assert format_score(85.5) == "85.5"
        assert format_score(100.0) == "100.0"
        assert format_score(0.0) == "0.0"
    
    def test_format_score_rounding(self):
        """Test format_score rounding to 1 decimal."""
        assert format_score(85.567) == "85.6"
        assert format_score(85.543) == "85.5"
    
    def test_format_score_none(self):
        """Test format_score with None."""
        assert format_score(None) == "-"
    
    def test_format_percentage_valid(self):
        """Test format_percentage with valid values."""
        assert format_percentage(85.5) == "85.5%"
        assert format_percentage(100.0) == "100.0%"
        assert format_percentage(0.0) == "0.0%"
    
    def test_format_percentage_rounding(self):
        """Test format_percentage rounding to 1 decimal."""
        assert format_percentage(85.567) == "85.6%"
        assert format_percentage(85.543) == "85.5%"
    
    def test_format_percentage_none(self):
        """Test format_percentage with None."""
        assert format_percentage(None) == "-"
    
    def test_format_date_valid(self):
        """Test format_date with valid date."""
        test_date = date(2024, 1, 15)
        assert format_date(test_date) == "15/01/2024"
    
    def test_format_date_datetime(self):
        """Test format_date with datetime."""
        test_datetime = datetime(2024, 1, 15, 10, 30, 0)
        assert format_date(test_datetime) == "15/01/2024"
    
    def test_format_date_string(self):
        """Test format_date with string."""
        assert format_date("2024-01-15") == "15/01/2024"
    
    def test_format_date_none(self):
        """Test format_date with None."""
        assert format_date(None) == "-"
    
    def test_format_value_valid(self):
        """Test format_value with valid numbers."""
        assert format_value(1234.56) == "1,234.6"
        assert format_value(85.5) == "85.5"
        assert format_value(0.0) == "0.0"
    
    def test_format_value_large_numbers(self):
        """Test format_value with large numbers."""
        assert format_value(1234567.89) == "1,234,567.9"
    
    def test_format_value_none(self):
        """Test format_value with None."""
        assert format_value(None) == "-"
    
    def test_format_integer_valid(self):
        """Test format_integer with valid integers."""
        assert format_integer(1234) == "1,234"
        assert format_integer(85) == "85"
        assert format_integer(0) == "0"
    
    def test_format_integer_large_numbers(self):
        """Test format_integer with large numbers."""
        assert format_integer(1234567) == "1,234,567"
    
    def test_format_integer_none(self):
        """Test format_integer with None."""
        assert format_integer(None) == "-"
    
    def test_format_triad_name_structure(self):
        """Test format_triad_name for structure."""
        assert format_triad_name("structure") == "Estrutura"
    
    def test_format_triad_name_process(self):
        """Test format_triad_name for process."""
        assert format_triad_name("process") == "Processo"
    
    def test_format_triad_name_outcome(self):
        """Test format_triad_name for outcome."""
        assert format_triad_name("outcome") == "Resultado"
    
    def test_format_triad_name_invalid(self):
        """Test format_triad_name with invalid dimension."""
        assert format_triad_name("invalid") == "invalid"
    
    def test_format_triad_name_none(self):
        """Test format_triad_name with None."""
        assert format_triad_name(None) == "-"
    
    def test_format_pillar_name_efficacy(self):
        """Test format_pillar_name for efficacy."""
        assert format_pillar_name("efficacy") == "Eficácia"
    
    def test_format_pillar_name_effectiveness(self):
        """Test format_pillar_name for effectiveness."""
        assert format_pillar_name("effectiveness") == "Efetividade"
    
    def test_format_pillar_name_efficiency(self):
        """Test format_pillar_name for efficiency."""
        assert format_pillar_name("efficiency") == "Eficiência"
    
    def test_format_pillar_name_optimality(self):
        """Test format_pillar_name for optimality."""
        assert format_pillar_name("optimality") == "Otimidade"
    
    def test_format_pillar_name_acceptability(self):
        """Test format_pillar_name for acceptability."""
        assert format_pillar_name("acceptability") == "Aceitabilidade"
    
    def test_format_pillar_name_legitimacy(self):
        """Test format_pillar_name for legitimacy."""
        assert format_pillar_name("legitimacy") == "Legitimidade"
    
    def test_format_pillar_name_equity(self):
        """Test format_pillar_name for equity."""
        assert format_pillar_name("equity") == "Equidade"
    
    def test_format_pillar_name_invalid(self):
        """Test format_pillar_name with invalid pillar."""
        assert format_pillar_name("invalid") == "invalid"
    
    def test_format_pillar_name_none(self):
        """Test format_pillar_name with None."""
        assert format_pillar_name(None) == "-"
    
    def test_format_status_green(self):
        """Test format_status for green status."""
        result = format_status("green")
        assert "🟢" in result or "Verde" in result
    
    def test_format_status_yellow(self):
        """Test format_status for yellow status."""
        result = format_status("yellow")
        assert "🟡" in result or "Amarelo" in result
    
    def test_format_status_red(self):
        """Test format_status for red status."""
        result = format_status("red")
        assert "🔴" in result or "Vermelho" in result
    
    def test_format_status_invalid(self):
        """Test format_status with invalid status."""
        result = format_status("invalid")
        assert result == "invalid" or result == "-"
    
    def test_format_status_none(self):
        """Test format_status with None."""
        assert format_status(None) == "-"


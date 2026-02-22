"""
Testes para WhatsApp Templates (D4).

Testa templates pré-aprovados.
"""

import pytest

from comunicacao.channels.whatsapp.templates import get_template, list_templates


def test_list_templates():
    """Testa listagem de templates."""
    # Act
    templates = list_templates()

    # Assert
    assert len(templates) == 5
    assert "alerta_clinico" in templates
    assert "teleconsulta_convite" in templates
    assert "lembrete_medicacao" in templates
    assert "lembrete_consulta" in templates
    assert "resultado_exame" in templates


def test_get_template_alerta_clinico():
    """Testa template de alerta clínico."""
    # Act
    template = get_template("alerta_clinico")

    # Assert
    assert template["meta_template_name"] == "alerta_clinico_v1"
    assert template["language"] == "pt_BR"
    assert template["category"] == "UTILITY"
    assert template["params_count"] == 4
    assert len(template["components"]) == 4  # HEADER, BODY, FOOTER, BUTTONS


def test_get_template_teleconsulta_convite():
    """Testa template de convite de teleconsulta."""
    # Act
    template = get_template("teleconsulta_convite")

    # Assert
    assert template["meta_template_name"] == "teleconsulta_convite_v1"
    assert template["params_count"] == 4
    assert template["category"] == "UTILITY"


def test_get_template_lembrete_medicacao():
    """Testa template de lembrete de medicação."""
    # Act
    template = get_template("lembrete_medicacao")

    # Assert
    assert template["meta_template_name"] == "lembrete_medicacao_v1"
    assert template["params_count"] == 3


def test_get_template_lembrete_consulta():
    """Testa template de lembrete de consulta."""
    # Act
    template = get_template("lembrete_consulta")

    # Assert
    assert template["meta_template_name"] == "lembrete_consulta_v1"
    assert template["params_count"] == 4


def test_get_template_resultado_exame():
    """Testa template de resultado de exame."""
    # Act
    template = get_template("resultado_exame")

    # Assert
    assert template["meta_template_name"] == "resultado_exame_v1"
    assert template["params_count"] == 1


def test_get_template_not_found():
    """Testa template inexistente."""
    # Act & Assert
    with pytest.raises(KeyError):
        get_template("template_inexistente")


def test_template_components_structure():
    """Testa estrutura dos componentes dos templates."""
    # Act
    template = get_template("alerta_clinico")

    # Assert
    components = template["components"]
    
    # Verificar tipos de componentes
    component_types = [c["type"] for c in components]
    assert "HEADER" in component_types
    assert "BODY" in component_types
    assert "FOOTER" in component_types
    assert "BUTTONS" in component_types

    # Verificar BODY tem example
    body_component = next(c for c in components if c["type"] == "BODY")
    assert "example" in body_component
    assert "body_text" in body_component["example"]


def test_all_templates_have_required_fields():
    """Testa que todos os templates têm campos obrigatórios."""
    # Act
    templates = list_templates()

    # Assert
    for template_name in templates:
        template = get_template(template_name)
        
        # Campos obrigatórios
        assert "meta_template_name" in template
        assert "language" in template
        assert "category" in template
        assert "params_count" in template
        assert "components" in template
        
        # Validar language
        assert template["language"] == "pt_BR"
        
        # Validar category
        assert template["category"] in ["UTILITY", "MARKETING", "AUTHENTICATION"]


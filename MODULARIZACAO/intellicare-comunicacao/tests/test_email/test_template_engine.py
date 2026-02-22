"""
Testes para EmailTemplateEngine (D4).

Testa renderização de templates Jinja2.
"""

import pytest
from datetime import datetime
from pathlib import Path

from comunicacao.channels.email.template_engine import EmailTemplateEngine


@pytest.fixture
def template_engine(tmp_path):
    """Fixture de template engine com diretório temporário."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    # Criar template de teste
    test_template = templates_dir / "test.html"
    test_template.write_text("""
    <html>
    <body>
        <h1>{{ title }}</h1>
        <p>{{ message }}</p>
    </body>
    </html>
    """)
    
    return EmailTemplateEngine(templates_dir=str(templates_dir))


def test_render_template(template_engine):
    """Testa renderização de template."""
    # Arrange
    context = {
        "title": "Teste",
        "message": "Mensagem de teste",
    }
    
    # Act
    html = template_engine.render("test.html", context)
    
    # Assert
    assert "Teste" in html
    assert "Mensagem de teste" in html


def test_render_string():
    """Testa renderização de string."""
    # Arrange
    engine = EmailTemplateEngine()
    template_str = "<p>Hello {{ name }}!</p>"
    context = {"name": "World"}
    
    # Act
    html = engine.render_string(template_str, context)
    
    # Assert
    assert "Hello World!" in html


def test_list_templates(template_engine):
    """Testa listagem de templates."""
    # Act
    templates = template_engine.list_templates()
    
    # Assert
    assert "test.html" in templates


def test_template_exists(template_engine):
    """Testa verificação de existência de template."""
    # Act & Assert
    assert template_engine.template_exists("test.html") is True
    assert template_engine.template_exists("nonexistent.html") is False


def test_format_date_filter():
    """Testa filtro de formatação de data."""
    # Arrange
    engine = EmailTemplateEngine()
    template_str = "{{ date|format_date }}"
    date = datetime(2026, 2, 19)
    
    # Act
    result = engine.render_string(template_str, {"date": date})
    
    # Assert
    assert "19/02/2026" in result


def test_format_datetime_filter():
    """Testa filtro de formatação de datetime."""
    # Arrange
    engine = EmailTemplateEngine()
    template_str = "{{ dt|format_datetime }}"
    dt = datetime(2026, 2, 19, 14, 30)
    
    # Act
    result = engine.render_string(template_str, {"dt": dt})
    
    # Assert
    assert "19/02/2026 14:30" in result


def test_template_not_found(template_engine):
    """Testa erro quando template não existe."""
    # Act & Assert
    with pytest.raises(Exception):
        template_engine.render("nonexistent.html", {})


def test_autoescape():
    """Testa que HTML é escapado por segurança."""
    # Arrange
    engine = EmailTemplateEngine()
    template_str = "<p>{{ content }}</p>"
    context = {"content": "<script>alert('xss')</script>"}
    
    # Act
    html = engine.render_string(template_str, context)
    
    # Assert
    assert "&lt;script&gt;" in html  # HTML escapado
    assert "<script>" not in html  # Script não executável


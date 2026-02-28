"""
Template Engine para Email (D4).

Renderiza templates HTML usando Jinja2.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

logger = logging.getLogger(__name__)


class EmailTemplateEngine:
    """Engine de templates para email usando Jinja2."""

    def __init__(self, templates_dir: str = "comunicacao/templates/email"):
        """
        Inicializa template engine.

        Args:
            templates_dir: Diretório de templates.
        """
        self._templates_dir = Path(templates_dir)
        
        # Criar diretório se não existir
        self._templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar Jinja2
        self._env = Environment(
            loader=FileSystemLoader(str(self._templates_dir)),
            autoescape=True,  # Segurança: escape HTML
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Adicionar filtros customizados
        self._env.filters["format_date"] = self._format_date
        self._env.filters["format_datetime"] = self._format_datetime

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Renderiza template HTML.

        Args:
            template_name: Nome do template (ex: "clinical_alert.html").
            context: Dados para renderizar.

        Returns:
            str: HTML renderizado.

        Raises:
            TemplateNotFound: Se template não existe.
        """
        try:
            template = self._env.get_template(template_name)
            html = template.render(**context)
            
            logger.info("Template renderizado: %s", template_name)
            return html
            
        except TemplateNotFound:
            logger.error("Template não encontrado: %s", template_name)
            raise
        except Exception as exc:
            logger.error("Erro ao renderizar template %s: %s", template_name, exc)
            raise

    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Renderiza template a partir de string.

        Args:
            template_string: Template HTML como string.
            context: Dados para renderizar.

        Returns:
            str: HTML renderizado.
        """
        template = Template(template_string, autoescape=True)
        return template.render(**context)

    def list_templates(self) -> list[str]:
        """
        Lista templates disponíveis.

        Returns:
            list[str]: Nomes dos templates.
        """
        templates = []
        for file in self._templates_dir.glob("*.html"):
            templates.append(file.name)
        
        return sorted(templates)

    def template_exists(self, template_name: str) -> bool:
        """
        Verifica se template existe.

        Args:
            template_name: Nome do template.

        Returns:
            bool: True se existe.
        """
        template_path = self._templates_dir / template_name
        return template_path.exists()

    @staticmethod
    def _format_date(value, format_str: str = "%d/%m/%Y") -> str:
        """
        Filtro Jinja2 para formatar data.

        Args:
            value: Data (datetime ou string).
            format_str: Formato de saída.

        Returns:
            str: Data formatada.
        """
        if hasattr(value, "strftime"):
            return value.strftime(format_str)
        return str(value)

    @staticmethod
    def _format_datetime(value, format_str: str = "%d/%m/%Y %H:%M") -> str:
        """
        Filtro Jinja2 para formatar datetime.

        Args:
            value: Datetime (datetime ou string).
            format_str: Formato de saída.

        Returns:
            str: Datetime formatado.
        """
        if hasattr(value, "strftime"):
            return value.strftime(format_str)
        return str(value)


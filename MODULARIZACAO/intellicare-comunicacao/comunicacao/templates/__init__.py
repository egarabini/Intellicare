"""Camada de templates de mensagem."""

from comunicacao.templates.models import MessageTemplate, TemplateVariant
from comunicacao.templates.renderer import TemplateRenderer
from comunicacao.templates.store import InMemoryTemplateStore

__all__ = [
    "InMemoryTemplateStore",
    "MessageTemplate",
    "TemplateRenderer",
    "TemplateVariant",
]


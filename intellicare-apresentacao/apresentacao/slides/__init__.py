"""Biblioteca de slides."""

from .base_slide import BaseSlide
from .title_slide import TitleSlide
from .content_slide import ContentSlide
from .diagram_slide import DiagramSlide
from .metrics_slide import MetricsSlide
from .agent_profile_slide import AgentProfileSlide

__all__ = [
    "BaseSlide",
    "TitleSlide",
    "ContentSlide",
    "DiagramSlide",
    "MetricsSlide",
    "AgentProfileSlide",
]

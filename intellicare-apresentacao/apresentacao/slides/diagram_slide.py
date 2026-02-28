"""
Slide com diagrama ASCII.
"""

import pygame
from typing import Dict
from slides.base_slide import BaseSlide
from core.animation_engine import AnimationEngine


class DiagramSlide(BaseSlide):
    """Slide com diagrama em ASCII art."""
    
    def __init__(self, title: str, diagram: str, narration: str = ""):
        """
        Inicializa slide de diagrama.
        
        Args:
            title: Título do slide
            diagram: Diagrama em ASCII (string multilinha)
            narration: Texto de narração
        """
        super().__init__(title, narration)
        self.diagram = diagram
        self.diagram_lines = diagram.split('\n')
        self.animation = AnimationEngine()
        
    def render(self, screen: pygame.Surface, theme: Dict[str, tuple],
               fonts: Dict[str, pygame.font.Font], slide_time: float) -> None:
        """Renderiza o slide de diagrama."""
        width, height = screen.get_size()
        
        # Renderiza título
        title_font = fonts["subtitle"]
        title_surface = title_font.render(self.title, True, theme["primary"])
        title_rect = title_surface.get_rect(center=(width // 2, 100))
        screen.blit(title_surface, title_rect)
        
        # Renderiza diagrama
        diagram_font = fonts["small"]
        y_offset = 250
        line_spacing = 35
        
        # Progresso da animação (typewriter effect)
        total_chars = sum(len(line) for line in self.diagram_lines)
        chars_to_show = int(total_chars * min(1.0, slide_time / 2.0))  # 2 segundos para mostrar tudo
        
        chars_shown = 0
        for line in self.diagram_lines:
            if chars_shown >= chars_to_show:
                break
                
            # Quantos caracteres desta linha mostrar
            chars_in_line = min(len(line), chars_to_show - chars_shown)
            visible_line = line[:chars_in_line]
            
            # Renderiza linha
            line_surface = diagram_font.render(visible_line, True, theme["text"])
            line_rect = line_surface.get_rect(left=200, top=y_offset)
            screen.blit(line_surface, line_rect)
            
            chars_shown += len(line)
            y_offset += line_spacing

        # Renderiza overlay se existir
        if self.current_overlay:
            self.current_overlay.draw(screen, theme, fonts)


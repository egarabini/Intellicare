"""
Slide de título.
"""

import pygame
from typing import Dict
from slides.base_slide import BaseSlide
from core.animation_engine import AnimationEngine


class TitleSlide(BaseSlide):
    """Slide de título com animação fade in."""
    
    def __init__(self, title: str, subtitle: str = "", narration: str = ""):
        """
        Inicializa slide de título.
        
        Args:
            title: Título principal
            subtitle: Subtítulo
            narration: Texto de narração
        """
        super().__init__(title, narration)
        self.subtitle = subtitle
        self.animation = AnimationEngine()
        
    def render(self, screen: pygame.Surface, theme: Dict[str, tuple],
               fonts: Dict[str, pygame.font.Font], slide_time: float) -> None:
        """Renderiza o slide de título."""
        width, height = screen.get_size()
        
        # Progresso da animação (0.0 a 1.0)
        title_progress = min(1.0, slide_time / 1.0)  # 1 segundo
        subtitle_progress = max(0.0, min(1.0, (slide_time - 0.5) / 1.0))  # Começa após 0.5s
        
        # Aplica easing
        title_progress = self.animation.ease_in_out(title_progress)
        subtitle_progress = self.animation.ease_in_out(subtitle_progress)
        
        # Renderiza título
        title_font = fonts["title"]
        title_surface = title_font.render(self.title, True, theme["primary"])
        
        # Aplica fade in
        title_alpha = int(255 * title_progress)
        title_surface.set_alpha(title_alpha)
        
        # Posição centralizada
        title_rect = title_surface.get_rect(center=(width // 2, height // 2 - 100))
        screen.blit(title_surface, title_rect)
        
        # Renderiza subtítulo (se houver)
        if self.subtitle and subtitle_progress > 0:
            subtitle_font = fonts["subtitle"]
            subtitle_surface = subtitle_font.render(self.subtitle, True, theme["text_secondary"])
            
            # Aplica fade in
            subtitle_alpha = int(255 * subtitle_progress)
            subtitle_surface.set_alpha(subtitle_alpha)
            
            # Posição
            subtitle_rect = subtitle_surface.get_rect(center=(width // 2, height // 2 + 50))
            screen.blit(subtitle_surface, subtitle_rect)

        # Renderiza overlay se existir
        if self.current_overlay:
            self.current_overlay.draw(screen, theme, fonts)


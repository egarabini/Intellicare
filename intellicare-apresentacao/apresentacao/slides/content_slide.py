"""
Slide de conteúdo com lista de itens.
"""

import pygame
from typing import Dict, List
from slides.base_slide import BaseSlide
from core.animation_engine import AnimationEngine


class ContentSlide(BaseSlide):
    """Slide de conteúdo com título e lista de itens."""
    
    def __init__(self, title: str, content: List[str], narration: str = ""):
        """
        Inicializa slide de conteúdo.
        
        Args:
            title: Título do slide
            content: Lista de itens de conteúdo
            narration: Texto de narração
        """
        super().__init__(title, narration)
        self.content = content
        self.animation = AnimationEngine()
        
    def render(self, screen: pygame.Surface, theme: Dict[str, tuple],
               fonts: Dict[str, pygame.font.Font], slide_time: float) -> None:
        """Renderiza o slide de conteúdo."""
        width, height = screen.get_size()
        
        # Renderiza título
        title_font = fonts["subtitle"]
        title_surface = title_font.render(self.title, True, theme["primary"])
        title_rect = title_surface.get_rect(center=(width // 2, 150))
        screen.blit(title_surface, title_rect)
        
        # Renderiza itens de conteúdo
        content_font = fonts["content"]
        y_offset = 300
        item_spacing = 80
        
        for i, item in enumerate(self.content):
            # Cada item aparece com delay
            item_delay = i * 0.3  # 0.3s entre cada item
            item_progress = max(0.0, min(1.0, (slide_time - item_delay) / 0.5))
            
            if item_progress > 0:
                # Aplica easing
                item_progress = self.animation.ease_in_out(item_progress)
                
                # Renderiza item
                item_surface = content_font.render(item, True, theme["text"])
                
                # Aplica fade in
                item_alpha = int(255 * item_progress)
                item_surface.set_alpha(item_alpha)
                
                # Posição com slide in da esquerda
                base_x = 200
                offset_x = int(50 * (1.0 - item_progress))
                item_rect = item_surface.get_rect(left=base_x - offset_x, top=y_offset)
                
                screen.blit(item_surface, item_rect)

            y_offset += item_spacing

        # Renderiza overlay se existir
        if self.current_overlay:
            self.current_overlay.draw(screen, theme, fonts)


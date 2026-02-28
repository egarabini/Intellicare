"""
Sistema de Overlays para Deep Dive.
"""

import pygame
from abc import ABC, abstractmethod
from typing import Dict, Any


class Overlay(ABC):
    """Classe base para overlays (elementos flutuantes sobre slides)."""
    
    def __init__(self, width: int = 1200, height: int = 700):
        """
        Inicializa o overlay.
        
        Args:
            width: Largura do overlay
            height: Altura do overlay
        """
        self.width = width
        self.height = height
        self.alpha = 0  # Transparência (0-255)
        self.target_alpha = 255  # Alpha alvo
        self.animation_time = 0.0  # Tempo de animação
        self.animation_duration = 0.3  # Duração da animação (segundos)
        self.is_closing = False
        
    def update(self, delta_time: float) -> bool:
        """
        Atualiza animação do overlay.
        
        Args:
            delta_time: Tempo desde último frame (segundos)
            
        Returns:
            True se animação está completa, False caso contrário
        """
        self.animation_time += delta_time
        
        # Calcula progresso da animação (0.0 a 1.0)
        progress = min(self.animation_time / self.animation_duration, 1.0)
        
        if self.is_closing:
            # Fade-out
            self.alpha = int(255 * (1.0 - progress))
            return progress >= 1.0  # True quando fade-out completo
        else:
            # Fade-in
            self.alpha = int(255 * progress)
            return False
    
    def close(self) -> None:
        """Inicia animação de fechamento."""
        self.is_closing = True
        self.animation_time = 0.0
    
    @abstractmethod
    def draw(self, surface: pygame.Surface, theme: Dict[str, tuple], 
             fonts: Dict[str, pygame.font.Font]) -> None:
        """
        Renderiza o overlay.
        
        Args:
            surface: Superfície do Pygame
            theme: Dicionário com cores do tema
            fonts: Dicionário com fontes
        """
        pass


class TextOverlay(Overlay):
    """Overlay com texto detalhado (para Deep Dive)."""
    
    def __init__(self, title: str, content: str, width: int = 1200, height: int = 700):
        """
        Inicializa overlay de texto.
        
        Args:
            title: Título do overlay
            content: Conteúdo detalhado
            width: Largura do overlay
            height: Altura do overlay
        """
        super().__init__(width, height)
        self.title = title
        self.content = content
        
    def draw(self, surface: pygame.Surface, theme: Dict[str, tuple], 
             fonts: Dict[str, pygame.font.Font]) -> None:
        """Renderiza overlay de texto."""
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        # 1. Fundo escurecido (dimming)
        dimming = pygame.Surface((screen_width, screen_height))
        dimming.set_alpha(int(180 * (self.alpha / 255)))  # Alpha proporcional
        dimming.fill((0, 0, 0))
        surface.blit(dimming, (0, 0))
        
        # 2. Card central
        card_x = (screen_width - self.width) // 2
        card_y = (screen_height - self.height) // 2
        
        # Fundo do card
        card_surface = pygame.Surface((self.width, self.height))
        card_surface.set_alpha(self.alpha)
        card_surface.fill(theme.get("background", (10, 14, 39)))
        
        # Borda brilhante
        border_color = theme.get("primary", (0, 212, 255))
        pygame.draw.rect(card_surface, border_color, 
                        (0, 0, self.width, self.height), 4)
        
        # 3. Título
        title_font = fonts.get("subtitle", pygame.font.Font(None, 60))
        title_surface = title_font.render(self.title, True, theme.get("primary", (0, 212, 255)))
        title_rect = title_surface.get_rect(centerx=self.width // 2, top=40)
        card_surface.blit(title_surface, title_rect)
        
        # 4. Linha separadora
        line_y = title_rect.bottom + 20
        pygame.draw.line(card_surface, border_color, 
                        (50, line_y), (self.width - 50, line_y), 2)
        
        # 5. Conteúdo
        content_font = fonts.get("content", pygame.font.Font(None, 40))
        y_offset = line_y + 40
        
        # Quebra conteúdo em linhas
        lines = self.content.split('\n')
        for line in lines:
            if line.strip():
                text_surface = content_font.render(line.strip(), True, 
                                                   theme.get("text", (255, 255, 255)))
                card_surface.blit(text_surface, (60, y_offset))
                y_offset += 50
        
        # 6. Instrução de fechamento
        hint_font = fonts.get("small", pygame.font.Font(None, 32))
        hint_text = "Pressione ESC para fechar"
        hint_surface = hint_font.render(hint_text, True, 
                                        theme.get("text_secondary", (160, 160, 160)))
        hint_rect = hint_surface.get_rect(centerx=self.width // 2, 
                                          bottom=self.height - 30)
        card_surface.blit(hint_surface, hint_rect)
        
        # Desenha card na tela
        surface.blit(card_surface, (card_x, card_y))


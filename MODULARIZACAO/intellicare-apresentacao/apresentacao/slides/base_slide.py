"""
Classe base para todos os slides.
"""

from abc import ABC, abstractmethod
import pygame
from typing import Dict, List, Any, Optional


class BaseSlide(ABC):
    """Classe abstrata base para slides."""
    
    def __init__(self, title: str, narration: str = ""):
        """
        Inicializa o slide.

        Args:
            title: Título do slide
            narration: Texto de narração
        """
        self.title = title
        self.narration = narration
        self.narration_text = narration  # Alias para compatibilidade com WandaNarrator
        self.has_played_narration = False  # Controle de estado de reprodução
        self.deep_dive_slides: List['BaseSlide'] = []
        self.current_overlay: Optional[Any] = None  # Overlay ativo (Deep Dive)
        self.deep_dive_content: Optional[Dict[str, str]] = None  # Conteúdo do Deep Dive
        
    @abstractmethod
    def render(self, screen: pygame.Surface, theme: Dict[str, tuple], 
               fonts: Dict[str, pygame.font.Font], slide_time: float) -> None:
        """
        Renderiza o slide.
        
        Args:
            screen: Superfície do Pygame
            theme: Dicionário com cores do tema
            fonts: Dicionário com fontes
            slide_time: Tempo desde que o slide foi exibido (segundos)
        """
        pass
        
    def update(self, delta_time: float, slide_time: float) -> None:
        """
        Atualiza estado do slide.

        Args:
            delta_time: Tempo desde último frame (segundos)
            slide_time: Tempo desde que o slide foi exibido (segundos)
        """
        # Atualiza animação do overlay se existir
        if self.current_overlay:
            is_complete = self.current_overlay.update(delta_time)
            # Remove overlay após fade-out completo
            if is_complete and self.current_overlay.is_closing:
                self.current_overlay = None
        
    def add_deep_dive(self, slide: 'BaseSlide') -> None:
        """
        Adiciona slide de aprofundamento.
        
        Args:
            slide: Slide para aprofundamento
        """
        self.deep_dive_slides.append(slide)
        
    def on_enter(self) -> None:
        """Chamado quando o slide é exibido."""
        pass
        
    def on_exit(self) -> None:
        """Chamado quando o slide é ocultado."""
        pass

    def open_deep_dive(self) -> None:
        """Abre overlay de Deep Dive."""
        if self.deep_dive_content and not self.current_overlay:
            from core.overlay import TextOverlay
            self.current_overlay = TextOverlay(
                title=self.deep_dive_content.get("title", "Detalhes"),
                content=self.deep_dive_content.get("content", "")
            )

    def close_deep_dive(self) -> None:
        """Fecha overlay de Deep Dive."""
        if self.current_overlay:
            self.current_overlay.close()

    def has_deep_dive(self) -> bool:
        """Verifica se slide tem Deep Dive disponível."""
        return self.deep_dive_content is not None


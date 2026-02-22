"""
Engine de animações e transições.
"""

import pygame
import math
from typing import Tuple


class AnimationEngine:
    """Gerencia animações e efeitos visuais."""
    
    @staticmethod
    def fade_in(surface: pygame.Surface, progress: float) -> pygame.Surface:
        """
        Aplica efeito de fade in.
        
        Args:
            surface: Superfície a animar
            progress: Progresso da animação (0.0 a 1.0)
            
        Returns:
            Superfície com fade aplicado
        """
        alpha = int(255 * progress)
        surface_copy = surface.copy()
        surface_copy.set_alpha(alpha)
        return surface_copy
        
    @staticmethod
    def fade_out(surface: pygame.Surface, progress: float) -> pygame.Surface:
        """
        Aplica efeito de fade out.
        
        Args:
            surface: Superfície a animar
            progress: Progresso da animação (0.0 a 1.0)
            
        Returns:
            Superfície com fade aplicado
        """
        alpha = int(255 * (1.0 - progress))
        surface_copy = surface.copy()
        surface_copy.set_alpha(alpha)
        return surface_copy
        
    @staticmethod
    def slide_in(position: Tuple[int, int], progress: float, 
                 direction: str = "left") -> Tuple[int, int]:
        """
        Calcula posição para animação de slide in.
        
        Args:
            position: Posição final (x, y)
            progress: Progresso da animação (0.0 a 1.0)
            direction: Direção ("left", "right", "top", "bottom")
            
        Returns:
            Posição animada (x, y)
        """
        x, y = position
        offset = 100 * (1.0 - progress)
        
        if direction == "left":
            return (int(x - offset), y)
        elif direction == "right":
            return (int(x + offset), y)
        elif direction == "top":
            return (x, int(y - offset))
        elif direction == "bottom":
            return (x, int(y + offset))
            
        return position
        
    @staticmethod
    def ease_in_out(t: float) -> float:
        """
        Função de easing suave (ease in-out).
        
        Args:
            t: Tempo normalizado (0.0 a 1.0)
            
        Returns:
            Valor com easing aplicado
        """
        return t * t * (3.0 - 2.0 * t)
        
    @staticmethod
    def pulse(t: float, frequency: float = 2.0) -> float:
        """
        Cria efeito de pulsação.
        
        Args:
            t: Tempo em segundos
            frequency: Frequência da pulsação
            
        Returns:
            Valor pulsante (0.0 a 1.0)
        """
        return (math.sin(t * frequency * math.pi) + 1.0) / 2.0
        
    @staticmethod
    def typewriter_text(text: str, progress: float) -> str:
        """
        Simula efeito de máquina de escrever.
        
        Args:
            text: Texto completo
            progress: Progresso da animação (0.0 a 1.0)
            
        Returns:
            Texto parcial baseado no progresso
        """
        chars_to_show = int(len(text) * progress)
        return text[:chars_to_show]
        
    @staticmethod
    def scale_bounce(progress: float, bounce_height: float = 0.2) -> float:
        """
        Cria efeito de bounce ao escalar.
        
        Args:
            progress: Progresso da animação (0.0 a 1.0)
            bounce_height: Altura do bounce
            
        Returns:
            Escala com bounce
        """
        if progress >= 1.0:
            return 1.0
            
        # Bounce effect
        bounce = math.sin(progress * math.pi) * bounce_height
        return progress + bounce


"""
Gerenciador de interações (teclado e mouse).
"""

import pygame
from typing import Optional


class InteractionHandler:
    """Gerencia eventos de teclado e mouse."""
    
    def __init__(self):
        """Inicializa o gerenciador de interações."""
        self.key_bindings = {
            pygame.K_SPACE: "next",
            pygame.K_BACKSPACE: "previous",
            pygame.K_d: "deep_dive",
            pygame.K_p: "ask_wanda",
            pygame.K_r: "repeat",
            pygame.K_m: "mute",
            pygame.K_ESCAPE: "quit",
        }
        
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Processa um evento e retorna a ação correspondente.
        
        Args:
            event: Evento do Pygame
            
        Returns:
            String com a ação ou None se não houver ação
        """
        if event.type == pygame.QUIT:
            return "quit"
            
        if event.type == pygame.KEYDOWN:
            return self.key_bindings.get(event.key)
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clique esquerdo
                return "next"
                
        return None
        
    def get_key_bindings(self) -> dict:
        """Retorna o mapeamento de teclas."""
        return self.key_bindings.copy()


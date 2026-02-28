"""
Gerenciador de slides.
"""

from typing import List, Optional


class SlideManager:
    """Gerencia a lista de slides e navegação."""
    
    def __init__(self):
        """Inicializa o gerenciador de slides."""
        self.slides: List = []
        self.current_index: int = 0
        
    def add_slide(self, slide) -> None:
        """
        Adiciona um slide à apresentação.
        
        Args:
            slide: Instância de BaseSlide
        """
        self.slides.append(slide)
        
    def get_current_slide(self):
        """
        Retorna o slide atual.
        
        Returns:
            Slide atual ou None se não houver slides
        """
        if not self.slides:
            return None
        return self.slides[self.current_index]
        
    def next(self) -> bool:
        """
        Avança para o próximo slide.
        
        Returns:
            True se avançou, False se já está no último
        """
        if self.current_index < len(self.slides) - 1:
            self.current_index += 1
            return True
        return False
        
    def previous(self) -> bool:
        """
        Volta para o slide anterior.
        
        Returns:
            True se voltou, False se já está no primeiro
        """
        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False
        
    def goto(self, index: int) -> bool:
        """
        Vai para um slide específico.
        
        Args:
            index: Índice do slide (0-based)
            
        Returns:
            True se foi para o slide, False se índice inválido
        """
        if 0 <= index < len(self.slides):
            self.current_index = index
            return True
        return False
        
    def get_total_slides(self) -> int:
        """Retorna o número total de slides."""
        return len(self.slides)
        
    def get_current_index(self) -> int:
        """Retorna o índice do slide atual."""
        return self.current_index


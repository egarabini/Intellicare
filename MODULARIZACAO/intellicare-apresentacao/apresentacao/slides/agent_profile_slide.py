"""
Slide visual de perfil de agente.
"""

import os
from typing import Dict, List, Optional

import pygame

from slides.base_slide import BaseSlide
from core.animation_engine import AnimationEngine


class AgentProfileSlide(BaseSlide):
    """Slide visual para apresentar um agente em primeira pessoa."""

    def __init__(
        self,
        agent_name: str,
        role: str,
        origin: str,
        represents: str,
        activation: str,
        highlights: List[str],
        narration: str = "",
        image_path: Optional[str] = None,
        secondary_image_path: Optional[str] = None,
    ):
        super().__init__(title=f"{agent_name} - {role}", narration=narration)
        self.agent_name = agent_name
        self.role = role
        self.origin = origin
        self.represents = represents
        self.activation = activation
        self.highlights = highlights
        self.image_path = image_path
        self.secondary_image_path = secondary_image_path
        self.animation = AnimationEngine()

        self._loaded_image: Optional[pygame.Surface] = None
        self._loaded_secondary_image: Optional[pygame.Surface] = None
        self._image_loaded = False

    def _load_image(self) -> None:
        """Carrega imagem do agente, se existir."""
        if self._image_loaded:
            return
        self._image_loaded = True

        if not self.image_path:
            return
        if not os.path.exists(self.image_path):
            return

        try:
            img = pygame.image.load(self.image_path).convert_alpha()
            self._loaded_image = pygame.transform.smoothscale(img, (260, 260))
        except Exception:
            self._loaded_image = None

        if self.secondary_image_path and os.path.exists(self.secondary_image_path):
            try:
                img2 = pygame.image.load(self.secondary_image_path).convert_alpha()
                self._loaded_secondary_image = pygame.transform.smoothscale(img2, (260, 260))
            except Exception:
                self._loaded_secondary_image = None

    def _draw_avatar(
        self,
        screen: pygame.Surface,
        theme: Dict[str, tuple],
        x: int,
        y: int,
        slide_time: float,
    ) -> None:
        """Desenha avatar com imagem ou placeholder."""
        self._load_image()

        # Card de avatar
        avatar_rect = pygame.Rect(x, y, 320, 360)
        pygame.draw.rect(screen, theme["secondary"], avatar_rect, border_radius=18)
        pygame.draw.rect(screen, theme["primary"], avatar_rect, 3, border_radius=18)

        if self._loaded_image is not None and self._loaded_secondary_image is None:
            image_x = x + (320 - 260) // 2
            image_y = y + 30
            screen.blit(self._loaded_image, (image_x, image_y))
            return

        if self._loaded_image is not None and self._loaded_secondary_image is not None:
            image_x = x + (320 - 260) // 2
            image_y = y + 30

            # Janela de transicao: real aparece primeiro, depois faz crossfade para cartoon
            # t <= 1.8s: 100% imagem principal
            # 1.8s < t < 3.4s: crossfade
            # t >= 3.4s: 100% imagem secundaria
            t = slide_time
            fade_start = 1.8
            fade_duration = 1.6
            if t <= fade_start:
                alpha_secondary = 0.0
            elif t >= fade_start + fade_duration:
                alpha_secondary = 1.0
            else:
                alpha_secondary = (t - fade_start) / fade_duration

            alpha_primary = 1.0 - alpha_secondary

            primary = self._loaded_image.copy()
            primary.set_alpha(int(255 * alpha_primary))
            screen.blit(primary, (image_x, image_y))

            secondary = self._loaded_secondary_image.copy()
            secondary.set_alpha(int(255 * alpha_secondary))
            screen.blit(secondary, (image_x, image_y))
            return

        # Placeholder visual (iniciais)
        cx = x + 160
        cy = y + 155
        pygame.draw.circle(screen, theme["primary"], (cx, cy), 92)
        pygame.draw.circle(screen, theme["text"], (cx, cy), 92, 3)

        initials = "".join([w[0] for w in self.agent_name.split()[:2]]).upper()
        initials_font = pygame.font.Font(None, 96)
        initials_surface = initials_font.render(initials, True, theme["background"])
        initials_rect = initials_surface.get_rect(center=(cx, cy))
        screen.blit(initials_surface, initials_rect)

    def render(
        self,
        screen: pygame.Surface,
        theme: Dict[str, tuple],
        fonts: Dict[str, pygame.font.Font],
        slide_time: float,
    ) -> None:
        width, _height = screen.get_size()

        title_progress = self.animation.ease_in_out(min(1.0, slide_time / 0.8))
        body_progress = self.animation.ease_in_out(max(0.0, min(1.0, (slide_time - 0.2) / 1.0)))

        # Título
        title_surface = fonts["subtitle"].render(self.title, True, theme["primary"])
        title_surface.set_alpha(int(255 * title_progress))
        title_rect = title_surface.get_rect(center=(width // 2, 90))
        screen.blit(title_surface, title_rect)

        # Coluna esquerda (avatar)
        left_x = 90
        left_y = 170
        self._draw_avatar(screen, theme, left_x, left_y, slide_time)

        # Nome em destaque
        name_surface = fonts["content"].render(self.agent_name, True, theme["text"])
        name_surface.set_alpha(int(255 * body_progress))
        name_rect = name_surface.get_rect(center=(left_x + 160, left_y + 315))
        screen.blit(name_surface, name_rect)

        # Coluna direita (conteúdo)
        right_x = 470
        block_w = width - right_x - 90
        block_rect = pygame.Rect(right_x, 170, block_w, 360)
        pygame.draw.rect(screen, theme["secondary"], block_rect, border_radius=18)
        pygame.draw.rect(screen, theme["primary"], block_rect, 2, border_radius=18)

        line_y = 205
        line_gap = 52
        text_font = fonts["small"]

        info_lines = [
            f"Origem do nome: {self.origin}",
            f"O que represento: {self.represents}",
            f"Quando sou acionado: {self.activation}",
        ]

        for i, line in enumerate(info_lines):
            progress = self.animation.ease_in_out(max(0.0, min(1.0, (slide_time - (0.4 + i * 0.15)) / 0.5)))
            if progress <= 0:
                continue
            txt = text_font.render(line, True, theme["text"])
            txt.set_alpha(int(255 * progress))
            screen.blit(txt, (right_x + 24, line_y))
            line_y += line_gap

        # Bloco de destaque
        highlights_rect = pygame.Rect(right_x, 555, block_w, 230)
        pygame.draw.rect(screen, theme["secondary"], highlights_rect, border_radius=18)
        pygame.draw.rect(screen, theme["primary"], highlights_rect, 2, border_radius=18)

        label_surface = fonts["small"].render("Destaques", True, theme["primary"])
        label_surface.set_alpha(int(255 * body_progress))
        screen.blit(label_surface, (right_x + 24, 585))

        y = 630
        for i, item in enumerate(self.highlights[:3]):
            progress = self.animation.ease_in_out(max(0.0, min(1.0, (slide_time - (0.9 + i * 0.12)) / 0.45)))
            if progress <= 0:
                continue
            bullet = text_font.render(f"• {item}", True, theme["text"])
            bullet.set_alpha(int(255 * progress))
            screen.blit(bullet, (right_x + 28, y))
            y += 50

        if self.current_overlay:
            self.current_overlay.draw(screen, theme, fonts)

"""
Slide de metricas com cards visuais.
"""

import pygame
from typing import Dict, List
from slides.base_slide import BaseSlide
from core.animation_engine import AnimationEngine


class MetricsSlide(BaseSlide):
    """Slide com metricas em cards - layout horizontal com destaque visual."""

    def __init__(self, title: str, metrics: List[Dict[str, str]],
                 narration: str = "", subtitle: str = ""):
        """
        Inicializa slide de metricas.

        Args:
            title: Titulo do slide
            metrics: Lista de metricas [{"label", "value", "icon", "description"(opt)}]
            narration: Texto de narracao
            subtitle: Subtitulo/tagline exibido abaixo do titulo
        """
        super().__init__(title, narration)
        self.metrics = metrics
        self.subtitle = subtitle
        self.animation = AnimationEngine()

    def _get_card_accents(self, theme: Dict[str, tuple]) -> list:
        """Retorna cores de destaque por card baseadas no tema."""
        return [
            theme.get("primary", (0, 212, 255)),
            theme.get("success", (6, 255, 165)),
            theme.get("warning", (255, 190, 11)),
            theme.get("secondary", (123, 44, 191)),
        ]

    @staticmethod
    def _wrap_text(font: pygame.font.Font, text: str, max_width: int) -> List[str]:
        """Quebra texto em linhas que cabem na largura maxima."""
        words = text.split()
        lines: List[str] = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines if lines else [text]

    def _render_centered_lines(
        self, screen: pygame.Surface, font: pygame.font.Font,
        text: str, color: tuple, center_x: int, top_y: int,
        max_width: int, alpha: int, line_spacing: int = 28,
    ) -> int:
        """Renderiza texto com word-wrap centralizado. Retorna y apos ultima linha."""
        lines = self._wrap_text(font, text, max_width)
        y = top_y
        for line in lines:
            surf = font.render(line, True, color)
            surf.set_alpha(alpha)
            rect = surf.get_rect(center=(center_x, y))
            screen.blit(surf, rect)
            y += line_spacing
        return y

    def render(self, screen: pygame.Surface, theme: Dict[str, tuple],
               fonts: Dict[str, pygame.font.Font], slide_time: float) -> None:
        """Renderiza o slide de metricas."""
        width, height = screen.get_size()
        accents = self._get_card_accents(theme)

        # ── Titulo ──
        title_progress = self.animation.ease_in_out(min(1.0, slide_time / 0.8))
        title_surface = fonts["subtitle"].render(self.title, True, theme["primary"])
        title_surface.set_alpha(int(255 * title_progress))
        title_rect = title_surface.get_rect(center=(width // 2, 80))
        screen.blit(title_surface, title_rect)

        # ── Subtitulo ──
        content_start_y = 180
        if self.subtitle:
            sub_progress = self.animation.ease_in_out(
                max(0.0, min(1.0, (slide_time - 0.3) / 0.6)))
            sub_color = theme.get("text_secondary", theme["text"])
            sub_surface = fonts["small"].render(self.subtitle, True, sub_color)
            sub_surface.set_alpha(int(255 * sub_progress))
            sub_rect = sub_surface.get_rect(center=(width // 2, 140))
            screen.blit(sub_surface, sub_rect)
            content_start_y = 210

        # ── Cards horizontais ──
        num_cards = len(self.metrics)
        card_w = 380
        card_h = 430
        spacing = 35
        text_max_w = card_w - 44
        total_w = num_cards * card_w + (num_cards - 1) * spacing
        start_x = (width - total_w) // 2
        card_y = content_start_y

        for i, metric in enumerate(self.metrics):
            x = start_x + i * (card_w + spacing)
            accent = accents[i % len(accents)]

            # Animacao com delay escalonado
            delay = 0.4 + i * 0.18
            progress = max(0.0, min(1.0, (slide_time - delay) / 0.6))
            if progress <= 0:
                continue
            progress = self.animation.ease_in_out(progress)

            # Efeito slide-up
            offset_y = int(30 * (1.0 - progress))
            cy = card_y + offset_y
            cx_card = x + card_w // 2
            alpha = int(255 * progress)

            # Fundo do card (rounded, semi-transparente)
            bg_color = theme.get("secondary", (30, 30, 60))
            card_surface = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(
                card_surface, (*bg_color, int(160 * progress)),
                (0, 0, card_w, card_h), border_radius=14)
            screen.blit(card_surface, (x, cy))

            # Barra de destaque no topo
            bar_surface = pygame.Surface((card_w - 40, 4), pygame.SRCALPHA)
            bar_surface.fill((*accent, alpha))
            screen.blit(bar_surface, (x + 20, cy + 14))

            # Circulo com icone
            cy_circle = cy + 85
            radius = 42
            circle_surface = pygame.Surface(
                (radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(
                circle_surface, (*accent, int(220 * progress)),
                (radius + 2, radius + 2), radius)
            screen.blit(circle_surface,
                         (cx_card - radius - 2, cy_circle - radius - 2))

            # Letra do icone dentro do circulo
            icon_text = metric.get("icon", "?")
            bg_for_icon = theme.get("background", (10, 14, 39))
            icon_surface = fonts["content"].render(icon_text, True, bg_for_icon)
            icon_surface.set_alpha(alpha)
            icon_rect = icon_surface.get_rect(center=(cx_card, cy_circle))
            screen.blit(icon_surface, icon_rect)

            # Valor (destaque)
            value_text = str(metric["value"])
            value_surface = fonts["subtitle"].render(
                value_text, True, theme["text"])
            value_surface.set_alpha(alpha)
            value_rect = value_surface.get_rect(center=(cx_card, cy + 195))
            screen.blit(value_surface, value_rect)

            # Label (com word-wrap)
            label_color = theme.get("text_secondary", theme["text"])
            next_y = self._render_centered_lines(
                screen, fonts["small"], metric["label"], label_color,
                cx_card, cy + 265, text_max_w, alpha, line_spacing=28)

            # Descricao opcional (com word-wrap)
            desc = metric.get("description")
            if desc:
                self._render_centered_lines(
                    screen, fonts["small"], desc, label_color,
                    cx_card, next_y + 8, text_max_w,
                    int(160 * progress), line_spacing=26)

            # Borda do card (accent color, rounded)
            border_surface = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(
                border_surface, (*accent, int(200 * progress)),
                (0, 0, card_w, card_h), 2, border_radius=14)
            screen.blit(border_surface, (x, cy))

        # ── Tagline de fechamento ──
        tagline_delay = 0.4 + num_cards * 0.18 + 0.5
        tagline_progress = self.animation.ease_in_out(
            max(0.0, min(1.0, (slide_time - tagline_delay) / 0.8)))
        if tagline_progress > 0:
            line_y = card_y + card_h + 50
            line_w = 500
            line_surface = pygame.Surface((line_w, 2), pygame.SRCALPHA)
            line_surface.fill((*theme["primary"], int(120 * tagline_progress)))
            screen.blit(line_surface, ((width - line_w) // 2, line_y))

            tagline = "Coordenacao inteligente para decisoes mais seguras"
            tag_surface = fonts["small"].render(tagline, True, theme["primary"])
            tag_surface.set_alpha(int(220 * tagline_progress))
            tag_rect = tag_surface.get_rect(center=(width // 2, line_y + 30))
            screen.blit(tag_surface, tag_rect)

        # Overlay (Deep Dive)
        if self.current_overlay:
            self.current_overlay.draw(screen, theme, fonts)

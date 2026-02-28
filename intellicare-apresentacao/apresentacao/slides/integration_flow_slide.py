"""
Slide visual de fluxo de integração entre agentes.

Renderiza caixas coloridas com nomes dos agentes, setas animadas
e um caso clínico como exemplo prático — substituindo o diagrama ASCII.
"""

import math
from typing import Dict, List, Optional, Tuple

import pygame

from slides.base_slide import BaseSlide
from core.animation_engine import AnimationEngine


class IntegrationFlowSlide(BaseSlide):
    """Slide visual que mostra o fluxo de integração entre agentes."""

    # Cores-padrão por agente (usadas como fallback se o tema não fornecer)
    AGENT_COLORS: Dict[str, Tuple[int, int, int]] = {
        "PORTAL":     (100, 100, 120),
        "WANDA":      (0, 180, 230),
        "FLORENCE":   (230, 130, 50),
        "OSWALDO":    (50, 180, 100),
        "ZILDA":      (180, 100, 220),
        "GERALDA":    (220, 70, 100),
        "NISE":       (120, 180, 220),
        "DONABEDIAN": (200, 170, 50),
    }

    def __init__(
        self,
        title: str,
        case_title: str,
        steps: List[Dict[str, str]],
        narration: str = "",
    ):
        """
        Args:
            title: Título do slide.
            case_title: Nome do caso clínico exemplificado.
            steps: Lista de etapas, cada uma: {"agents": "NOME[,NOME]", "label": "...", "detail": "..."}.
            narration: Texto de narração TTS.
        """
        super().__init__(title, narration)
        self.case_title = case_title
        self.steps = steps
        self.animation = AnimationEngine()

    # ── helpers ──────────────────────────────────────────────

    @staticmethod
    def _draw_rounded_rect(
        surface: pygame.Surface,
        color: Tuple[int, int, int],
        rect: pygame.Rect,
        radius: int = 14,
        border: int = 0,
        border_color: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        if border and border_color:
            pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)

    @staticmethod
    def _draw_arrow(
        surface: pygame.Surface,
        start: Tuple[int, int],
        end: Tuple[int, int],
        color: Tuple[int, int, int],
        width: int = 3,
        head_size: int = 10,
    ) -> None:
        """Desenha seta de start → end."""
        pygame.draw.line(surface, color, start, end, width)
        # Cabeça da seta
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0:
            return
        ux, uy = dx / length, dy / length
        # Ponto base da cabeça
        bx = end[0] - ux * head_size
        by = end[1] - uy * head_size
        # Dois lados
        px, py = -uy, ux  # perpendicular
        p1 = (int(bx + px * head_size * 0.5), int(by + py * head_size * 0.5))
        p2 = (int(bx - px * head_size * 0.5), int(by - py * head_size * 0.5))
        pygame.draw.polygon(surface, color, [end, p1, p2])

    # ── render ───────────────────────────────────────────────

    def render(
        self,
        screen: pygame.Surface,
        theme: Dict[str, tuple],
        fonts: Dict[str, pygame.font.Font],
        slide_time: float,
    ) -> None:
        width, height = screen.get_size()

        # ── Título ──
        title_progress = self.animation.ease_in_out(min(1.0, slide_time / 0.8))
        title_surf = fonts["subtitle"].render(self.title, True, theme["primary"])
        title_surf.set_alpha(int(255 * title_progress))
        title_rect = title_surf.get_rect(center=(width // 2, 80))
        screen.blit(title_surf, title_rect)

        # ── Subtítulo (caso clínico) ──
        case_progress = self.animation.ease_in_out(max(0.0, min(1.0, (slide_time - 0.3) / 0.6)))
        case_surf = fonts["small"].render(
            f"Exemplo: {self.case_title}", True, theme.get("text_secondary", theme["text"])
        )
        case_surf.set_alpha(int(255 * case_progress))
        case_rect = case_surf.get_rect(center=(width // 2, 135))
        screen.blit(case_surf, case_rect)

        # ── Layout das etapas ──
        n = len(self.steps)
        pad_top = 190
        pad_bottom = 60
        available_h = height - pad_top - pad_bottom
        step_h = min(90, available_h // max(n, 1))
        total_h = step_h * n
        start_y = pad_top + (available_h - total_h) // 2

        # Largura das caixas e posições X
        box_w = 260
        detail_x = width // 2 + 60
        box_center_x = width // 2 - 160

        arrow_color = theme.get("primary", (0, 212, 255))

        for i, step in enumerate(self.steps):
            # Animação progressiva por etapa (0.4s delay entre cada)
            delay = 0.6 + i * 0.35
            progress = self.animation.ease_in_out(
                max(0.0, min(1.0, (slide_time - delay) / 0.5))
            )
            if progress <= 0:
                continue

            y = start_y + i * step_h
            agents = [a.strip() for a in step["agents"].split(",")]
            label = step.get("label", "")
            detail = step.get("detail", "")

            # Calcula caixas dos agentes nesta etapa
            agent_total_w = len(agents) * (box_w // len(agents) + 10) - 10
            agent_box_w = box_w // len(agents) + (40 if len(agents) == 1 else 0)
            group_x = box_center_x - agent_total_w // 2

            for j, agent in enumerate(agents):
                ax = group_x + j * (agent_box_w + 12)
                color = self.AGENT_COLORS.get(agent.upper(), theme.get("secondary", (50, 50, 80)))

                # Fundo da caixa com alpha
                box_rect = pygame.Rect(ax, y + 4, agent_box_w, step_h - 16)

                # Cor com alpha via surface
                box_surf = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
                r, g, b = color
                box_surf.fill((r, g, b, int(200 * progress)))
                pygame.draw.rect(box_surf, (255, 255, 255, int(60 * progress)),
                                 pygame.Rect(0, 0, box_rect.width, box_rect.height),
                                 2, border_radius=12)
                screen.blit(box_surf, box_rect.topleft)

                # Nome do agente
                name_font = fonts["small"]
                name_surf = name_font.render(agent, True, (255, 255, 255))
                name_surf.set_alpha(int(255 * progress))
                name_rect = name_surf.get_rect(center=box_rect.center)
                screen.blit(name_surf, name_rect)

            # Label à esquerda (ação)
            if label:
                lbl_surf = fonts["small"].render(label, True, theme["text"])
                lbl_surf.set_alpha(int(255 * progress))
                lbl_x = box_center_x - agent_total_w // 2 - 30
                lbl_rect = lbl_surf.get_rect(right=lbl_x, centery=y + step_h // 2)
                screen.blit(lbl_surf, lbl_rect)

            # Detail à direita
            if detail:
                det_surf = fonts["small"].render(detail, True,
                                                  theme.get("text_secondary", theme["text"]))
                det_surf.set_alpha(int(255 * progress))
                det_rect = det_surf.get_rect(left=detail_x, centery=y + step_h // 2)
                screen.blit(det_surf, det_rect)

            # Seta para a próxima etapa
            if i < n - 1:
                arrow_progress = self.animation.ease_in_out(
                    max(0.0, min(1.0, (slide_time - delay - 0.25) / 0.3))
                )
                if arrow_progress > 0:
                    ax_start = box_center_x
                    ay_start = y + step_h - 8
                    ay_end = y + step_h + 8
                    ac = (*arrow_color[:3], )  # ensure tuple of 3
                    # Fade the arrow
                    arrow_surf = pygame.Surface((20, ay_end - ay_start + 14), pygame.SRCALPHA)
                    ar, ag, ab = ac
                    self._draw_arrow(
                        screen,
                        (ax_start, ay_start),
                        (ax_start, ay_end),
                        (ar, ag, ab),
                        width=2,
                        head_size=8,
                    )

        # ── Rodapé ──
        footer_progress = self.animation.ease_in_out(
            max(0.0, min(1.0, (slide_time - 0.6 - n * 0.35) / 0.6))
        )
        if footer_progress > 0:
            footer_text = "7 agentes  ·  1 resposta integrada  ·  rastreável e segura"
            footer_surf = fonts["small"].render(footer_text, True, theme["primary"])
            footer_surf.set_alpha(int(255 * footer_progress))
            footer_rect = footer_surf.get_rect(center=(width // 2, height - 50))
            screen.blit(footer_surf, footer_rect)

        # Overlay
        if self.current_overlay:
            self.current_overlay.draw(screen, theme, fonts)

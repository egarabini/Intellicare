"""
Engine principal da apresentação.
"""

import os
import pygame
import json
import math
from pathlib import Path
from typing import Dict, Any

from core.slide_manager import SlideManager
from core.interaction_handler import InteractionHandler
from core.animation_engine import AnimationEngine
from utils.config import Config, THEMES_DIR

from wanda_ai.narrator import WandaNarrator
from wanda_ai.observability import ToolCallRecorder, LLMUsageRecorder
from wanda_ai.reflexion_memory import ReflexionMemory
from wanda_ai.evaluation_harness import EvaluationHarness

# Configuração de Vozes (Casting dos Agentes)
# Wanda: Feminina, padrão.
# Oswaldo/Donabedian: Masculinos, tons mais graves/maduros.
VOICE_CASTING = {
    "wanda": "nova",       # Feminina, energética
    "florence": "shimmer", # Feminina, suave
    "oswaldo": "onyx",     # Masculina, grave (Idoso/Sério)
    "zilda": "nova",       # Feminina, calorosa
    "geralda": "alloy",    # Feminina, acolhedora
    "nise": "shimmer",     # Feminina, gentil
    "donabedian": "echo",  # Masculina, autoritária (Sênior)
    "minerva": "alloy",    # Feminina, sábia
    "pierre": "onyx",      # Masculina, científica
    "careplanner": "alloy" # Neutra/Feminina
}

class PresentationEngine:
    """Engine principal que gerencia a apresentação."""
    
    def __init__(self, width: int = 1920, height: int = 1080, 
                 theme: str = "dark", tts_mode: str = "offline"):
        """
        Inicializa o engine de apresentação.
        
        Args:
            width: Largura da janela
            height: Altura da janela
            theme: Nome do tema ("dark" ou "light")
            tts_mode: Modo de TTS ("online" ou "offline")
        """
        # Inicializa Pygame
        pygame.init()
        
        # Configurações
        self.width = width
        self.height = height
        self.running = True
        
        # Cria janela
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("IntelliCare - Apresentação Interativa com Wanda")
        
        # Carrega tema
        self.theme = self._load_theme(theme)
        
        # Componentes
        self.slide_manager = SlideManager()
        force_offline = (tts_mode == "offline")
        self.narrator = WandaNarrator(
            voice="nova",
            model="tts-1",
            force_offline=force_offline
        )
        self.interaction = InteractionHandler()
        self.animation = AnimationEngine()
        
        # Estado
        self.clock = pygame.time.Clock()
        self.time_elapsed = 0.0
        self.slide_start_time = 0.0


        # Observabilidade/Tracing
        self.tool_call_recorder = ToolCallRecorder()
        self.llm_usage_recorder = LLMUsageRecorder()


        # Reflexion Memory
        self.reflexion_memory = ReflexionMemory()

        # Framework de Avaliação
        self.evaluation_harness = EvaluationHarness()

        # Estado para visualização 3D do Grafo de Agentes
        self.show_agent_graph = True
        self.graph_rotation = 0.0

        # Fontes
        self._init_fonts()
        
    def _init_fonts(self):
        """Inicializa fontes."""
        self.fonts = {
            "title": pygame.font.Font(None, 120),
            "subtitle": pygame.font.Font(None, 60),
            "content": pygame.font.Font(None, 48),
            "small": pygame.font.Font(None, 32),
        }
        
    def _load_theme(self, theme_name: str) -> Dict[str, Any]:
        """
        Carrega tema de cores.
        
        Args:
            theme_name: Nome do tema
            
        Returns:
            Dicionário com cores do tema
        """
        theme_path = THEMES_DIR / f"{theme_name}.json"
        
        try:
            with open(theme_path, 'r') as f:
                theme_data = json.load(f)
                
            # Converte cores hex para RGB
            theme = {}
            for key, hex_color in theme_data.items():
                theme[key] = self._hex_to_rgb(hex_color)
                
            return theme
            
        except Exception as e:
            print(f"Aviso: erro ao carregar tema: {e}. Usando tema padrao.")
            return {
                "background": (10, 14, 39),
                "primary": (0, 212, 255),
                "text": (255, 255, 255),
                "text_secondary": (160, 160, 160),
            }
            
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        """Converte cor hexadecimal para RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
    def add_slide(self, slide) -> None:
        """
        Adiciona um slide à apresentação.
        
        Args:
            slide: Instância de BaseSlide
        """
        self.slide_manager.add_slide(slide)
        
    def run(self) -> None:
        """Loop principal da apresentação."""
        # Mensagem de boas-vindas
        print("\n" + "="*60)
        print("IntelliCare - Apresentacao Interativa com Wanda")
        print("="*60)
        print("\nControles:")
        print("  ESPAÇO     - Próximo slide")
        print("  BACKSPACE  - Slide anterior")
        print("  D          - Deep dive do slide")
        print("  P          - Perguntar para Wanda")
        print("  R          - Repetir narração")
        print("  ESC        - Sair")
        print("\n" + "="*60 + "\n")
        
        # Narra primeiro slide automaticamente (fire-and-forget)
        current_slide = self.slide_manager.get_current_slide()
        if current_slide and hasattr(current_slide, 'narration_text') and current_slide.narration_text:
            rate = getattr(current_slide, 'narration_rate', 160)
            self._trigger_narration(current_slide)

        # Loop principal
        while self.running:
            delta_time = self.clock.tick(Config.FPS) / 1000.0
            self.time_elapsed += delta_time
            
            # Processa eventos
            self._handle_events()
            
            # Atualiza
            self._update(delta_time)
            
            # Renderiza
            self._render()
            
            # Atualiza tela
            pygame.display.flip()

        # Cleanup ao sair do loop
        print("\nEncerrando narrador...")
        self.narrator.shutdown()
        pygame.quit()
        print("Apresentacao encerrada com sucesso.\n")

    def _trigger_narration(self, slide) -> None:
        """
        Dispara a narração com a voz correta do agente responsável pelo slide.
        """
        if not slide or not hasattr(slide, 'narration_text') or not slide.narration_text:
            return

        # Identifica o orador (padrão: Wanda)
        speaker = getattr(slide, 'speaker', 'wanda').lower()
        voice_id = VOICE_CASTING.get(speaker, "nova")
        rate = getattr(slide, 'narration_rate', 160)

        print(f"🎙️ Narrando como: {speaker.capitalize()} (Voz: {voice_id})")
        
        # Assume que o WandaNarrator suporta o parametro 'voice' na chamada speak
        # Se a lib original não suportar, ela usará o default do __init__
        self.narrator.speak(slide.narration_text, wait=False, rate=rate, voice=voice_id)
        slide.has_played_narration = True
        
    def _handle_events(self) -> None:
        """Processa eventos."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            action = self.interaction.handle_event(event)
            if action:
                self._process_action(action)

    def _process_action(self, action: str) -> None:
        """
        Processa ação do usuário.

        Args:
            action: Ação a processar
        """
        current_slide = self.slide_manager.get_current_slide()

        if action == "quit":
            # ESC contextual: fecha overlay ou sai da aplicação
            if current_slide and current_slide.current_overlay:
                current_slide.close_deep_dive()
                print("Fechando Deep Dive...")
            else:
                self.running = False

        elif action == "deep_dive":
            # Tecla D: abre/fecha deep dive
            if current_slide and current_slide.has_deep_dive():
                if current_slide.current_overlay:
                    current_slide.close_deep_dive()
                    print("Fechando Deep Dive...")
                else:
                    current_slide.open_deep_dive()
                    print("Abrindo Deep Dive...")
            else:
                print("Aviso: este slide nao tem Deep Dive disponivel")


        elif action == "next":
            # Bloqueia navegação se overlay está aberto
            if current_slide and current_slide.current_overlay:
                print("Aviso: feche o Deep Dive antes de navegar (ESC)")
                return

            # Para áudio anterior (cut-off)
            self.narrator.stop()

            prev_index = self.slide_manager.get_current_index()
            if self.slide_manager.next():
                self.slide_start_time = self.time_elapsed
                current_slide = self.slide_manager.get_current_slide()

                # Tracing: registra navegação de slide como "tool call"
                self.tool_call_recorder.record(
                    tool_name="slide_navigation",
                    input_data={"from": prev_index, "to": self.slide_manager.get_current_index()},
                    output_data={"slide_title": getattr(current_slide, 'title', None)}
                )

                # Dispara narração do novo slide (fire-and-forget)
                if current_slide and hasattr(current_slide, 'narration_text') and current_slide.narration_text:
                    self._trigger_narration(current_slide)

                print(f"Slide {self.slide_manager.get_current_index() + 1}/{self.slide_manager.get_total_slides()}")

        elif action == "previous":
            # Bloqueia navegação se overlay está aberto
            if current_slide and current_slide.current_overlay:
                print("Aviso: feche o Deep Dive antes de navegar (ESC)")
                return

            # Para áudio anterior (cut-off)
            self.narrator.stop()

            if self.slide_manager.previous():
                self.slide_start_time = self.time_elapsed
                current_slide = self.slide_manager.get_current_slide()

                # Dispara narração do novo slide (fire-and-forget)
                if current_slide and hasattr(current_slide, 'narration_text') and current_slide.narration_text:
                    self._trigger_narration(current_slide)

                print(f"Slide {self.slide_manager.get_current_index() + 1}/{self.slide_manager.get_total_slides()}")

        elif action == "repeat":
            # Para áudio atual
            self.narrator.stop()

            current_slide = self.slide_manager.get_current_slide()
            if current_slide and hasattr(current_slide, 'narration_text') and current_slide.narration_text:
                self._trigger_narration(current_slide)
                print("Repetindo narração...")

        elif action == "ask_wanda":
            self._ask_wanda()

        elif action == "mute":
            # WandaNarrator não implementa mute ainda
            print("Aviso: funcao mute nao disponivel com WandaNarrator")

    def _ask_wanda(self) -> None:
        """
        Q&A local em modo terminal para interação com o público.
        Mantém funcionamento offline e sem dependências adicionais.
        """
        current_slide = self.slide_manager.get_current_slide()
        current_title = current_slide.title if current_slide else "apresentacao"

        # Evita sobreposição de áudio durante captura de pergunta
        self.narrator.stop()

        print("\nWanda: Pode perguntar. (ENTER vazio cancela)")
        try:
            question = input("Voce: ").strip()
        except EOFError:
            question = ""

        if not question:
            print("Pergunta cancelada.\n")
            return


        answer = self._build_wanda_answer(question, current_title)
        print(f"\nWanda: {answer}\n")
        self.narrator.speak(answer, wait=False)

        # Tracing: registra uso de LLM (simulado)
        self.llm_usage_recorder.record(
            prompt=question,
            response=answer,
            tokens_prompt=len(question.split()),
            tokens_response=len(answer.split()),
            meta={"context": current_title}
        )

        # Reflexion Memory: grava reflexão do agente Wanda
        self.reflexion_memory.append(
            agent="wanda",
            content=f"Pergunta: {question} | Resposta: {answer}",
            meta={"context": current_title}
        )

    def _build_wanda_answer(self, question: str, current_title: str) -> str:
        """
        Gera resposta contextual simples para Q&A ao vivo.
        """
        q = question.lower()

        if any(k in q for k in ["zilda", "cnes", "regiao", "estabelecimento", "unidade"]):
            return (
                "A Zilda e o agente dedicado a dados de saude brasileira. "
                "Ela utiliza o MCP RNDS para validar estabelecimentos e contexto territorial."
            )

        if any(k in q for k in ["florence", "exame", "clinica", "laborat"]):
            return (
                "A Florence aprofunda analise clinica e interpretacao de exames. "
                "Ela e um subagente que eu aciono via LangGraph quando detecto complexidade clinica nos dados do FHIR."
            )

        if any(k in q for k in ["oswaldo", "cron", "longitud", "estadiamento"]):
            return (
                "O Oswaldo e nosso especialista sênior em cronicos. "
                "Ele nao e apenas um algoritmo, e um agente que monitora a progressao renal e diabetes "
                "ao longo do tempo, usando o IPS Brasil como memoria base. "
                "Ele tem uma personalidade mais... experiente."
            )

        if any(k in q for k in ["donabedian", "qualidade", "indicador", "gestao"]):
            return (
                "O Donabedian foca em qualidade assistencial e governança. "
                "Ele transforma dados em melhoria de processo e resultado."
            )

        if any(k in q for k in ["geralda", "paciente", "acompanhamento", "jornada"]):
            return (
                "A Geralda reforca o acompanhamento do paciente ao longo da jornada de cuidado, "
                "com foco em comunicacao e continuidade assistencial."
            )

        if any(k in q for k in ["wanda", "orquestra", "como funciona", "integr"]):
            return (
                "Eu sou o Supervisor no padrao LangGraph. Eu nao tento saber tudo. "
                "Minha funcao e entender sua intencao e delegar para a Florence, Oswaldo ou Careplanner, usando ferramentas MCP para buscar dados reais."
            )

        if any(k in q for k in ["publico", "stakeholder", "audiencia"]):
            return (
                "Esta apresentacao foi desenhada para clinicos, gestores, times tecnicos e parceiros, "
                "com linguagem ajustada para cada perfil."
            )

        return (
            f"Nesta parte da apresentacao ({current_title}), o foco e mostrar como os agentes "
            "se complementam. Se quiser, pergunte sobre um agente especifico: Wanda, Florence, "
            "Oswaldo, Zilda, Geralda, Donabedian, Minerva ou Pierre."
        )

    def _update(self, delta_time: float) -> None:
        """
        Atualiza estado da apresentação.

        Args:
            delta_time: Tempo desde último frame (segundos)
        """
        current_slide = self.slide_manager.get_current_slide()
        if current_slide:
            slide_time = self.time_elapsed - self.slide_start_time
            if hasattr(current_slide, 'update'):
                current_slide.update(delta_time, slide_time)
        
        # Atualiza rotação do grafo 3D
        self.graph_rotation += delta_time * 0.5

    def _render(self) -> None:
        """Renderiza frame atual."""
        # Limpa tela
        self.screen.fill(self.theme["background"])

        # Renderiza slide atual
        current_slide = self.slide_manager.get_current_slide()
        if current_slide:
            slide_time = self.time_elapsed - self.slide_start_time
            current_slide.render(self.screen, self.theme, self.fonts, slide_time)

        # Renderiza avatar da Wanda ou Grafo de Agentes (Visualização 3D)
        # Se o slide for sobre arquitetura, mostra o grafo. Senão, o avatar simples.
        if current_slide and getattr(current_slide, 'show_graph_viz', False):
            self._render_agent_graph_3d()
        else:
            self._render_wanda_avatar()

        # Renderiza indicador de slide
        self._render_slide_indicator()

    def _project_3d_to_2d(self, x, y, z, center_x, center_y, scale=200):
        """Projeta coordenadas 3D simples para 2D com rotação Y."""
        # Rotação em torno do eixo Y
        angle = self.graph_rotation
        rx = x * math.cos(angle) - z * math.sin(angle)
        rz = x * math.sin(angle) + z * math.cos(angle)
        
        # Projeção perspectiva simples
        fov = 400
        dist = 4 + rz
        if dist == 0: dist = 0.01
        proj_scale = fov / dist
        
        px = center_x + rx * scale * (1/dist)
        py = center_y + y * scale * (1/dist)
        return int(px), int(py), rz

    def _render_agent_graph_3d(self) -> None:
        """Renderiza uma visualização 3D da arquitetura de agentes."""
        center_x = self.width - 150
        center_y = self.height - 150
        
        # Nós do grafo (Wanda no centro, outros orbitando)
        # (x, y, z, color, label)
        nodes = [
            (0, 0, 0, self.theme["primary"], "Wanda"), # Supervisor
            (1, 0, 0, (0, 255, 100), "Florence"),
            (-1, 0, 0, (255, 100, 100), "Oswaldo"),
            (0, 1, 0, (255, 200, 0), "CarePlanner"),
            (0, -1, 0, (100, 100, 255), "RNDS"),
            (0, 0, 1, (200, 0, 200), "FHIR"),
        ]

        # Desenha conexões (Wanda para todos)
        wanda_pos = self._project_3d_to_2d(0, 0, 0, center_x, center_y)
        
        sorted_nodes = []
        for x, y, z, color, label in nodes:
            px, py, rz = self._project_3d_to_2d(x, y, z, center_x, center_y)
            sorted_nodes.append((rz, px, py, color, label))
            
            # Linha conectando ao centro (se não for o centro)
            if label != "Wanda":
                pygame.draw.line(self.screen, (50, 50, 50), (wanda_pos[0], wanda_pos[1]), (px, py), 1)

        # Desenha nós (ordenados por Z para oclusão correta)
        sorted_nodes.sort(key=lambda k: k[0], reverse=True) # Desenha de trás para frente
        
        for rz, px, py, color, label in sorted_nodes:
            size = 20 if label == "Wanda" else 12
            pygame.draw.circle(self.screen, color, (px, py), size)
            # Label simples
            if rz < 0: # Só desenha texto se estiver na "frente"
                font = self.fonts["small"]
                text = font.render(label[0], True, (255,255,255))
                self.screen.blit(text, (px-5, py-10))

    def _render_wanda_avatar(self) -> None:
        """Renderiza avatar da Wanda."""
        # Posição do avatar (canto inferior direito)
        avatar_x = self.width - 100
        avatar_y = self.height - 100

        # Efeito de pulsação se estiver falando
        pulse = 1.0
        # Verifica se há thread de reprodução ativa
        if hasattr(self.narrator, '_playback_thread') and self.narrator._playback_thread and self.narrator._playback_thread.is_alive():
            pulse = 1.0 + 0.1 * self.animation.pulse(self.time_elapsed, frequency=3.0)

        # Desenha círculo (avatar simplificado)
        radius = int(40 * pulse)
        pygame.draw.circle(
            self.screen,
            self.theme["primary"],
            (avatar_x, avatar_y),
            radius
        )

        # Desenha borda
        pygame.draw.circle(
            self.screen,
            self.theme["text"],
            (avatar_x, avatar_y),
            radius,
            3
        )

        # Texto "Wanda"
        font = self.fonts["small"]
        text_surface = font.render("Wanda", True, self.theme["text"])
        text_rect = text_surface.get_rect(center=(avatar_x, avatar_y + 60))
        self.screen.blit(text_surface, text_rect)

    def _render_slide_indicator(self) -> None:
        """Renderiza indicador de slide (ex: 1/5)."""
        current = self.slide_manager.get_current_index() + 1
        total = self.slide_manager.get_total_slides()

        if total == 0:
            return

        # Texto
        font = self.fonts["small"]
        text = f"{current}/{total}"
        text_surface = font.render(text, True, self.theme["text_secondary"])

        # Posição (canto inferior esquerdo)
        text_rect = text_surface.get_rect()
        text_rect.bottomleft = (30, self.height - 30)

        self.screen.blit(text_surface, text_rect)

    # Métodos de Observabilidade
    def add_evaluation_test(self, name: str, func, expected=None, meta=None):
        """Adiciona um teste ao framework de avaliação."""
        self.evaluation_harness.add_test(name, func, expected, meta)

    def run_evaluation(self):
        """Executa todos os testes do framework de avaliação."""
        self.evaluation_harness.run()

    def export_evaluation_results(self) -> list:
        """Exporta resultados dos testes de avaliação."""
        return self.evaluation_harness.export_results()

    def export_reflexion_memory(self) -> list:
        """Exporta todas as memórias/reflexões."""
        return self.reflexion_memory.export()

    def query_reflexion_memory(self, agent: str = None, limit: int = 10) -> list:
        """Consulta últimas memórias/reflexões, opcionalmente filtrando por agente."""
        return self.reflexion_memory.query(agent=agent, limit=limit)

    def append_reflexion(self, agent: str, content: str, meta: dict = None):
        """Adiciona uma nova reflexão/memória."""
        self.reflexion_memory.append(agent, content, meta)

    def export_tool_calls(self) -> list:
        """Exporta o trace de chamadas de ferramentas."""
        return self.tool_call_recorder.export()

    def export_llm_usage(self) -> list:
        """Exporta o trace de uso de LLMs."""
        return self.llm_usage_recorder.export()

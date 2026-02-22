#!/usr/bin/env python3
"""
Protótipo Terminal - Fase 1
============================
Versão simplificada usando Rich para validar:
- Estrutura de slides
- Navegação
- Narração (texto)
- Fluxo lógico

Uso:
    python test_terminal_prototype.py
    
Controles:
    ENTER - Próximo slide
    B - Voltar
    D - Deep Dive (se disponível)
    R - Repetir narração
    Q - Sair
"""

import sys
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt
from rich.live import Live
from rich import box
import time

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from versoes.v1_visao_geral.slides import create_v1_slides


class TerminalPresentation:
    """Apresentação no terminal usando Rich."""
    
    def __init__(self):
        self.console = Console()
        self.slides = []
        self.current_index = 0
        self.in_deep_dive = False
        self.deep_dive_content = None
        
    def add_slides(self, slides: List):
        """Adiciona slides à apresentação."""
        self.slides = slides
        
    def show_welcome(self):
        """Mostra tela de boas-vindas."""
        self.console.clear()
        
        welcome_text = Text()
        welcome_text.append("\n🤖 Olá! Eu sou a ", style="bold white")
        welcome_text.append("Wanda", style="bold cyan")
        welcome_text.append("\n\n", style="bold white")
        welcome_text.append("Vou apresentar o projeto ", style="white")
        welcome_text.append("IntelliCare", style="bold green")
        welcome_text.append(" para você\n\n", style="white")
        
        controls = Table(show_header=False, box=box.SIMPLE)
        controls.add_column(style="cyan")
        controls.add_column(style="white")
        controls.add_row("ENTER", "Próximo slide")
        controls.add_row("B", "Voltar")
        controls.add_row("D", "Deep Dive (aprofundar)")
        controls.add_row("R", "Repetir narração")
        controls.add_row("Q", "Sair")
        
        panel = Panel(
            welcome_text,
            title="[bold cyan]IntelliCare - Apresentação Interativa[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print("\n")
        self.console.print(controls)
        self.console.print("\n")
        
        # Simula narração
        self._narrate("Olá! Seja bem-vindo à apresentação do IntelliCare...")
        
        input("\n[Pressione ENTER para começar]")
        
    def _narrate(self, text: str):
        """Simula narração (apenas exibe o texto)."""
        self.console.print(f"\n🎤 [italic cyan]Wanda:[/italic cyan] [italic]{text.strip()}[/italic]\n")
        
    def show_slide(self, index: int):
        """Mostra um slide específico."""
        if index < 0 or index >= len(self.slides):
            return
            
        self.console.clear()
        slide = self.slides[index]
        
        # Header com progresso
        progress = f"Slide {index + 1}/{len(self.slides)}"
        self.console.print(f"\n[dim]{progress}[/dim]", justify="right")
        self.console.print()
        
        # Renderiza o slide baseado no tipo
        slide_type = type(slide).__name__
        
        if slide_type == "TitleSlide":
            self._render_title_slide(slide)
        elif slide_type == "ContentSlide":
            self._render_content_slide(slide)
        elif slide_type == "DiagramSlide":
            self._render_diagram_slide(slide)
        elif slide_type == "MetricsSlide":
            self._render_metrics_slide(slide)
        else:
            self.console.print(f"[yellow]Tipo de slide desconhecido: {slide_type}[/yellow]")
            
        # Narração
        self._narrate(slide.narration)
        
        # Controles
        self._show_controls(slide)
        
    def _render_title_slide(self, slide):
        """Renderiza slide de título."""
        title_text = Text()
        title_text.append(slide.title, style="bold cyan", justify="center")
        
        subtitle_text = Text()
        subtitle_text.append(slide.subtitle, style="white", justify="center")
        
        content = Text()
        content.append("\n" * 3)
        content.append(slide.title, style="bold cyan")
        content.append("\n\n")
        content.append(slide.subtitle, style="white")
        content.append("\n" * 3)
        
        panel = Panel(
            content,
            border_style="cyan",
            padding=(2, 4),
            title="[bold]🎭 IntelliCare[/bold]"
        )
        
        self.console.print(panel, justify="center")
        
    def _render_content_slide(self, slide):
        """Renderiza slide de conteúdo."""
        self.console.print(f"\n[bold cyan]{slide.title}[/bold cyan]\n")
        
        for item in slide.content:
            self.console.print(f"  {item}")
            
        # Verifica se tem deep dive
        if hasattr(slide, 'deep_dive_content') and slide.deep_dive_content:
            self.console.print("\n[dim]💡 Pressione [bold]D[/bold] para aprofundar[/dim]")
            
    def _render_diagram_slide(self, slide):
        """Renderiza slide com diagrama."""
        self.console.print(f"\n[bold cyan]{slide.title}[/bold cyan]\n")
        
        panel = Panel(
            slide.diagram,
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        
    def _render_metrics_slide(self, slide):
        """Renderiza slide de métricas."""
        self.console.print(f"\n[bold cyan]{slide.title}[/bold cyan]\n")
        
        # Cria tabela de métricas
        table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
        table.add_column(style="cyan", justify="center", width=10)
        table.add_column(style="white", justify="left")
        table.add_column(style="bold green", justify="right", width=15)
        
        for metric in slide.metrics:
            table.add_row(
                metric["icon"],
                metric["label"],
                metric["value"]
            )
            
        self.console.print(table)
        
    def _show_controls(self, slide):
        """Mostra controles disponíveis."""
        controls = "\n[dim]Controles: [bold]ENTER[/bold]=Próximo | [bold]B[/bold]=Voltar | [bold]R[/bold]=Repetir | [bold]Q[/bold]=Sair"
        
        if hasattr(slide, 'deep_dive_content') and slide.deep_dive_content:
            controls += " | [bold]D[/bold]=Deep Dive"
            
        controls += "[/dim]"
        self.console.print(controls)
        
    def show_deep_dive(self, slide):
        """Mostra conteúdo de deep dive."""
        if not hasattr(slide, 'deep_dive_content') or not slide.deep_dive_content:
            self.console.print("[yellow]Nenhum conteúdo de aprofundamento disponível.[/yellow]")
            return
            
        self.console.clear()
        dd = slide.deep_dive_content
        
        self.console.print(f"\n[bold magenta]🔍 Deep Dive: {dd['title']}[/bold magenta]\n")
        
        panel = Panel(
            dd['content'],
            border_style="magenta",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print("\n[dim]Pressione ENTER para voltar[/dim]")
        
        input()
        
    def run(self):
        """Executa a apresentação."""
        self.show_welcome()
        
        while True:
            self.show_slide(self.current_index)
            
            # Aguarda comando
            command = Prompt.ask(
                "\n[bold cyan]>[/bold cyan]",
                choices=["", "b", "d", "r", "q"],
                default="",
                show_choices=False
            ).lower()
            
            if command == "" or command == "enter":
                # Próximo slide
                if self.current_index < len(self.slides) - 1:
                    self.current_index += 1
                else:
                    self.console.print("\n[green]✅ Fim da apresentação![/green]")
                    break
                    
            elif command == "b":
                # Slide anterior
                if self.current_index > 0:
                    self.current_index -= 1
                else:
                    self.console.print("[yellow]Já está no primeiro slide.[/yellow]")
                    time.sleep(1)
                    
            elif command == "d":
                # Deep dive
                slide = self.slides[self.current_index]
                self.show_deep_dive(slide)
                
            elif command == "r":
                # Repetir narração
                slide = self.slides[self.current_index]
                self._narrate(slide.narration)
                input("\n[Pressione ENTER para continuar]")
                
            elif command == "q":
                # Sair
                self.console.print("\n[yellow]👋 Até logo![/yellow]")
                break


def main():
    """Função principal."""
    try:
        # Cria apresentação
        presentation = TerminalPresentation()
        
        # Carrega slides da V1
        slides = create_v1_slides()
        presentation.add_slides(slides)
        
        # Executa
        presentation.run()
        
    except KeyboardInterrupt:
        print("\n\n✅ Apresentação encerrada.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


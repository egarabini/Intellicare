#!/usr/bin/env python3
"""
Teste Automatizado do MVP Pygame - Fase 2
==========================================
Testa o MVP Pygame sem interação do usuário.
Valida inicialização, renderização e componentes.
"""

import sys
import os
from pathlib import Path
from rich.console import Console

# Desabilita display do Pygame para testes headless
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

import pygame
from core.presentation_engine import PresentationEngine
from versoes.v1_visao_geral.slides import create_v1_slides


def test_pygame_initialization():
    """Testa inicialização do Pygame."""
    console = Console()
    console.print("\n[bold cyan]🧪 Teste 1: Inicialização do Pygame[/bold cyan]")
    
    try:
        pygame.init()
        console.print("✅ Pygame inicializado com sucesso")
        
        # Verifica módulos
        if pygame.display.get_init():
            console.print("✅ Display inicializado")
        if pygame.font.get_init():
            console.print("✅ Font inicializado")
            
        return True
    except Exception as e:
        console.print(f"❌ Erro ao inicializar Pygame: {e}")
        return False


def test_presentation_engine_creation():
    """Testa criação do PresentationEngine."""
    console = Console()
    console.print("\n[bold cyan]🧪 Teste 2: Criação do PresentationEngine[/bold cyan]")
    
    try:
        engine = PresentationEngine(
            width=800,
            height=600,
            theme="dark",
            tts_mode="offline"
        )
        
        console.print("✅ PresentationEngine criado")
        console.print(f"  Resolução: {engine.width}x{engine.height}")
        console.print(f"  Tema carregado: {len(engine.theme)} cores")
        console.print(f"  Fontes carregadas: {len(engine.fonts)}")
        
        # Verifica componentes
        assert engine.slide_manager is not None, "SlideManager não inicializado"
        console.print("✅ SlideManager inicializado")
        
        assert engine.narrator is not None, "Narrator não inicializado"
        console.print("✅ Narrator inicializado")
        
        assert engine.interaction is not None, "InteractionHandler não inicializado"
        console.print("✅ InteractionHandler inicializado")
        
        assert engine.animation is not None, "AnimationEngine não inicializado"
        console.print("✅ AnimationEngine inicializado")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Erro ao criar PresentationEngine: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_slide_loading():
    """Testa carregamento de slides."""
    console = Console()
    console.print("\n[bold cyan]🧪 Teste 3: Carregamento de Slides[/bold cyan]")
    
    try:
        engine = PresentationEngine(width=800, height=600, tts_mode="offline")
        
        # Carrega slides
        slides = create_v1_slides()
        for slide in slides:
            engine.add_slide(slide)
            
        console.print(f"✅ {len(slides)} slides adicionados ao engine")
        console.print(f"  Total de slides no manager: {engine.slide_manager.get_total_slides()}")

        assert engine.slide_manager.get_total_slides() == len(slides), "Número de slides incorreto"
        
        return True
        
    except Exception as e:
        console.print(f"❌ Erro ao carregar slides: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_slide_rendering():
    """Testa renderização de slides."""
    console = Console()
    console.print("\n[bold cyan]🧪 Teste 4: Renderização de Slides[/bold cyan]")
    
    try:
        engine = PresentationEngine(width=800, height=600, tts_mode="offline")
        
        # Carrega slides
        slides = create_v1_slides()
        for slide in slides:
            engine.add_slide(slide)
        
        # Tenta renderizar cada slide
        for i in range(min(3, len(slides))):  # Testa apenas os 3 primeiros
            engine.slide_manager.current_index = i
            current_slide = engine.slide_manager.get_current_slide()
            
            if current_slide:
                # Limpa tela
                engine.screen.fill(engine.theme["background"])
                
                # Renderiza slide
                current_slide.render(
                    engine.screen,
                    engine.theme,
                    engine.fonts,
                    slide_time=1.0  # 1 segundo de animação
                )
                
                slide_type = type(current_slide).__name__
                console.print(f"✅ Slide {i+1} renderizado: {slide_type}")
            else:
                console.print(f"⚠️  Slide {i+1} não encontrado")
        
        console.print("✅ Renderização de slides funcionando")
        return True
        
    except Exception as e:
        console.print(f"❌ Erro ao renderizar slides: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_navigation():
    """Testa navegação entre slides."""
    console = Console()
    console.print("\n[bold cyan]🧪 Teste 5: Navegação[/bold cyan]")
    
    try:
        engine = PresentationEngine(width=800, height=600, tts_mode="offline")
        
        # Carrega slides
        slides = create_v1_slides()
        for slide in slides:
            engine.add_slide(slide)
        
        # Testa navegação
        initial_index = engine.slide_manager.current_index
        console.print(f"  Índice inicial: {initial_index}")

        # Próximo slide
        engine.slide_manager.next()
        assert engine.slide_manager.current_index == 1, "Navegação para próximo falhou"
        console.print("✅ Navegação para próximo slide OK")

        # Próximo novamente
        engine.slide_manager.next()
        assert engine.slide_manager.current_index == 2, "Segunda navegação falhou"
        console.print("✅ Segunda navegação OK")

        # Slide anterior
        engine.slide_manager.previous()
        assert engine.slide_manager.current_index == 1, "Navegação para anterior falhou"
        console.print("✅ Navegação para slide anterior OK")

        # Volta ao início
        engine.slide_manager.previous()
        assert engine.slide_manager.current_index == 0, "Volta ao início falhou"
        console.print("✅ Volta ao início OK")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Erro ao testar navegação: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_theme_loading():
    """Testa carregamento de temas."""
    console = Console()
    console.print("\n[bold cyan]🧪 Teste 6: Carregamento de Temas[/bold cyan]")
    
    try:
        # Tema dark
        engine_dark = PresentationEngine(width=800, height=600, theme="dark", tts_mode="offline")
        console.print("✅ Tema dark carregado")
        console.print(f"  Background: {engine_dark.theme.get('background', 'N/A')}")
        
        # Tema light
        engine_light = PresentationEngine(width=800, height=600, theme="light", tts_mode="offline")
        console.print("✅ Tema light carregado")
        console.print(f"  Background: {engine_light.theme.get('background', 'N/A')}")
        
        # Verifica que são diferentes
        assert engine_dark.theme["background"] != engine_light.theme["background"], "Temas são iguais"
        console.print("✅ Temas são diferentes")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Erro ao testar temas: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Executa todos os testes."""
    console = Console()
    
    console.print("\n" + "="*60)
    console.print("[bold cyan]🧪 TESTES DO MVP PYGAME - FASE 2[/bold cyan]")
    console.print("="*60)
    
    tests = [
        ("Inicialização do Pygame", test_pygame_initialization),
        ("Criação do PresentationEngine", test_presentation_engine_creation),
        ("Carregamento de Slides", test_slide_loading),
        ("Renderização de Slides", test_slide_rendering),
        ("Navegação", test_navigation),
        ("Carregamento de Temas", test_theme_loading),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            console.print(f"\n❌ Erro fatal no teste '{test_name}': {e}")
            results.append((test_name, False))
    
    # Resumo
    console.print("\n" + "="*60)
    console.print("[bold cyan]📊 RESUMO DOS TESTES[/bold cyan]")
    console.print("="*60 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        console.print(f"{status}: {test_name}")
    
    console.print(f"\n[bold]Resultado: {passed}/{total} testes passaram[/bold]")
    
    if passed == total:
        console.print("\n[bold green]🎉 TODOS OS TESTES PASSARAM![/bold green]")
        console.print("\n[cyan]✅ Fase 2 (MVP Pygame) validada com sucesso![/cyan]")
        console.print("[cyan]➡️  Próximo passo: Teste com Stakeholders (Fase 3)[/cyan]")
    else:
        console.print("\n[bold red]⚠️  ALGUNS TESTES FALHARAM[/bold red]")
        console.print("[yellow]Corrija os erros antes de prosseguir.[/yellow]")
    
    console.print("\n" + "="*60 + "\n")
    
    # Cleanup
    pygame.quit()


if __name__ == "__main__":
    main()


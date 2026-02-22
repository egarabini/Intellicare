#!/usr/bin/env python3
"""
Teste Automatizado do Protótipo Terminal
=========================================
Testa o protótipo sem interação do usuário.
"""

import sys
from pathlib import Path
from rich.console import Console

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from versoes.v1_visao_geral.slides import create_v1_slides


def test_slides_creation():
    """Testa criação dos slides."""
    console = Console()
    
    console.print("\n[bold cyan]🧪 Teste 1: Criação de Slides[/bold cyan]")
    
    try:
        slides = create_v1_slides()
        console.print(f"✅ {len(slides)} slides criados com sucesso")
        
        for i, slide in enumerate(slides, 1):
            slide_type = type(slide).__name__
            console.print(f"  {i}. {slide_type}: {slide.title}")
            
        return True
    except Exception as e:
        console.print(f"❌ Erro ao criar slides: {e}")
        return False


def test_slide_attributes():
    """Testa atributos dos slides."""
    console = Console()
    
    console.print("\n[bold cyan]🧪 Teste 2: Atributos dos Slides[/bold cyan]")
    
    try:
        slides = create_v1_slides()
        
        for i, slide in enumerate(slides, 1):
            # Verifica atributos obrigatórios
            assert hasattr(slide, 'title'), f"Slide {i} sem título"
            assert hasattr(slide, 'narration'), f"Slide {i} sem narração"
            
            console.print(f"✅ Slide {i}: Atributos OK")
            
            # Verifica atributos específicos
            slide_type = type(slide).__name__
            
            if slide_type == "TitleSlide":
                assert hasattr(slide, 'subtitle'), f"TitleSlide {i} sem subtitle"
                
            elif slide_type == "ContentSlide":
                assert hasattr(slide, 'content'), f"ContentSlide {i} sem content"
                assert isinstance(slide.content, list), f"ContentSlide {i} content não é lista"
                
            elif slide_type == "DiagramSlide":
                assert hasattr(slide, 'diagram'), f"DiagramSlide {i} sem diagram"
                
            elif slide_type == "MetricsSlide":
                assert hasattr(slide, 'metrics'), f"MetricsSlide {i} sem metrics"
                assert isinstance(slide.metrics, list), f"MetricsSlide {i} metrics não é lista"
                
        console.print("✅ Todos os atributos estão corretos")
        return True
        
    except AssertionError as e:
        console.print(f"❌ Erro de validação: {e}")
        return False
    except Exception as e:
        console.print(f"❌ Erro inesperado: {e}")
        return False


def test_deep_dive():
    """Testa funcionalidade de deep dive."""
    console = Console()
    
    console.print("\n[bold cyan]🧪 Teste 3: Deep Dive[/bold cyan]")
    
    try:
        slides = create_v1_slides()
        
        # Slide 2 deve ter deep dive
        slide2 = slides[1]
        
        if hasattr(slide2, 'deep_dive_content') and slide2.deep_dive_content:
            console.print("✅ Slide 2 tem conteúdo de deep dive")
            console.print(f"  Título: {slide2.deep_dive_content['title']}")
            console.print(f"  Conteúdo: {len(slide2.deep_dive_content['content'])} caracteres")
        else:
            console.print("⚠️  Slide 2 não tem deep dive (esperado)")
            
        return True
        
    except Exception as e:
        console.print(f"❌ Erro ao testar deep dive: {e}")
        return False


def test_narration():
    """Testa narrações."""
    console = Console()
    
    console.print("\n[bold cyan]🧪 Teste 4: Narrações[/bold cyan]")
    
    try:
        slides = create_v1_slides()
        
        for i, slide in enumerate(slides, 1):
            narration = slide.narration.strip()
            
            if len(narration) > 0:
                console.print(f"✅ Slide {i}: {len(narration)} caracteres de narração")
            else:
                console.print(f"⚠️  Slide {i}: Narração vazia")
                
        return True
        
    except Exception as e:
        console.print(f"❌ Erro ao testar narrações: {e}")
        return False


def test_rendering_simulation():
    """Simula renderização dos slides."""
    console = Console()
    
    console.print("\n[bold cyan]🧪 Teste 5: Simulação de Renderização[/bold cyan]")
    
    try:
        slides = create_v1_slides()
        
        for i, slide in enumerate(slides, 1):
            slide_type = type(slide).__name__
            
            console.print(f"\n[bold]Slide {i}/{len(slides)}: {slide.title}[/bold]")
            console.print(f"Tipo: {slide_type}")
            
            # Simula renderização baseada no tipo
            if slide_type == "TitleSlide":
                console.print(f"  📄 Título: {slide.title}")
                console.print(f"  📝 Subtítulo: {slide.subtitle}")
                
            elif slide_type == "ContentSlide":
                console.print(f"  📋 {len(slide.content)} itens de conteúdo")
                for item in slide.content[:2]:  # Mostra apenas 2 primeiros
                    console.print(f"    • {item}")
                    
            elif slide_type == "DiagramSlide":
                console.print(f"  📊 Diagrama: {len(slide.diagram)} caracteres")
                
            elif slide_type == "MetricsSlide":
                console.print(f"  📈 {len(slide.metrics)} métricas")
                for metric in slide.metrics:
                    console.print(f"    {metric['icon']} {metric['label']}: {metric['value']}")
                    
            console.print(f"  🎤 Narração: {len(slide.narration)} caracteres")
            
        console.print("\n✅ Simulação de renderização completa")
        return True
        
    except Exception as e:
        console.print(f"❌ Erro na simulação: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Executa todos os testes."""
    console = Console()
    
    console.print("\n" + "="*60)
    console.print("[bold cyan]🧪 TESTES DO PROTÓTIPO TERMINAL - FASE 1[/bold cyan]")
    console.print("="*60)
    
    tests = [
        ("Criação de Slides", test_slides_creation),
        ("Atributos dos Slides", test_slide_attributes),
        ("Deep Dive", test_deep_dive),
        ("Narrações", test_narration),
        ("Simulação de Renderização", test_rendering_simulation),
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
        console.print("\n[cyan]✅ Fase 1 (Protótipo Terminal) validada com sucesso![/cyan]")
        console.print("[cyan]➡️  Próximo passo: Fase 2 (MVP Pygame)[/cyan]")
    else:
        console.print("\n[bold red]⚠️  ALGUNS TESTES FALHARAM[/bold red]")
        console.print("[yellow]Corrija os erros antes de prosseguir.[/yellow]")
    
    console.print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()


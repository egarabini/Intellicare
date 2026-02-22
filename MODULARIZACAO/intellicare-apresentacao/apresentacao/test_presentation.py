#!/usr/bin/env python3
"""
Script de teste da apresentação.
Verifica se todos os componentes estão funcionando.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Testa se todos os módulos podem ser importados."""
    print("🧪 Testando imports...")
    
    try:
        from core.presentation_engine import PresentationEngine
        print("  ✅ PresentationEngine")
    except Exception as e:
        print(f"  ❌ PresentationEngine: {e}")
        return False
        
    try:
        from core.slide_manager import SlideManager
        print("  ✅ SlideManager")
    except Exception as e:
        print(f"  ❌ SlideManager: {e}")
        return False
        
    try:
        from core.narrator import Narrator
        print("  ✅ Narrator")
    except Exception as e:
        print(f"  ❌ Narrator: {e}")
        return False
        
    try:
        from core.interaction_handler import InteractionHandler
        print("  ✅ InteractionHandler")
    except Exception as e:
        print(f"  ❌ InteractionHandler: {e}")
        return False
        
    try:
        from core.animation_engine import AnimationEngine
        print("  ✅ AnimationEngine")
    except Exception as e:
        print(f"  ❌ AnimationEngine: {e}")
        return False
        
    try:
        from slides.base_slide import BaseSlide
        print("  ✅ BaseSlide")
    except Exception as e:
        print(f"  ❌ BaseSlide: {e}")
        return False
        
    try:
        from slides.title_slide import TitleSlide
        print("  ✅ TitleSlide")
    except Exception as e:
        print(f"  ❌ TitleSlide: {e}")
        return False
        
    try:
        from slides.content_slide import ContentSlide
        print("  ✅ ContentSlide")
    except Exception as e:
        print(f"  ❌ ContentSlide: {e}")
        return False
        
    try:
        from slides.diagram_slide import DiagramSlide
        print("  ✅ DiagramSlide")
    except Exception as e:
        print(f"  ❌ DiagramSlide: {e}")
        return False
        
    try:
        from slides.metrics_slide import MetricsSlide
        print("  ✅ MetricsSlide")
    except Exception as e:
        print(f"  ❌ MetricsSlide: {e}")
        return False
        
    try:
        from versoes.v1_visao_geral.slides import create_v1_slides
        print("  ✅ V1 Slides")
    except Exception as e:
        print(f"  ❌ V1 Slides: {e}")
        return False

    try:
        from versoes.v2_agentes.slides import create_v2_slides
        print("  ✅ V2 Slides")
    except Exception as e:
        print(f"  ❌ V2 Slides: {e}")
        return False
        
    return True


def test_slide_creation():
    """Testa criação dos slides da V1."""
    print("\n🧪 Testando criação de slides...")
    
    try:
        from versoes.v1_visao_geral.slides import create_v1_slides
        slides = create_v1_slides()
        
        if len(slides) != 5:
            print(f"  ❌ Esperado 5 slides, encontrado {len(slides)}")
            return False
            
        print(f"  ✅ {len(slides)} slides criados com sucesso")
        
        for i, slide in enumerate(slides, 1):
            print(f"     Slide {i}: {slide.title}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao criar slides: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_v2_slide_creation():
    """Testa criação dos slides da V2."""
    print("\n🧪 Testando criação de slides da V2...")

    try:
        from versoes.v2_agentes.slides import create_v2_slides
        slides = create_v2_slides()

        if len(slides) < 8:
            print(f"  ❌ Esperado ao menos 8 slides, encontrado {len(slides)}")
            return False

        print(f"  ✅ {len(slides)} slides V2 criados com sucesso")
        print(f"     Primeiro: {slides[0].title}")
        print(f"     Último: {slides[-1].title}")
        return True

    except Exception as e:
        print(f"  ❌ Erro ao criar slides V2: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_v3_slide_creation():
    """Testa criação dos slides da V3 (agentes completo)."""
    print("\n🧪 Testando criação de slides da V3...")

    try:
        from versoes.v3_agentes_completo.slides import create_v3_slides
        slides = create_v3_slides()

        if len(slides) != 15:
            print(f"  ❌ Esperado 15 slides, encontrado {len(slides)}")
            return False

        print(f"  ✅ {len(slides)} slides V3 criados com sucesso")

        # Verifica slides de agentes (posições 3-11, índices 3..11)
        agent_names = [s.agent_name for s in slides[3:12] if hasattr(s, "agent_name")]
        expected = [
            "WANDA", "FLORENCE", "OSWALDO", "ZILDA", "GERALDA",
            "NISE", "DONABEDIAN", "MINERVA", "PIERRE",
        ]
        if agent_names != expected:
            print(f"  ❌ Agentes esperados: {expected}, encontrado: {agent_names}")
            return False

        print(f"     Agentes: {', '.join(agent_names)}")

        # Verifica que slide WANDA menciona Fase 3
        wanda_slide = slides[3]
        assert "LangGraph" in wanda_slide.deep_dive_content.get("content", ""), \
            "WANDA deep-dive deve mencionar LangGraph"

        # Verifica que slide NISE menciona FLOWISE e LGPD
        nise_slide = slides[8]
        assert "FLOWISE" in nise_slide.deep_dive_content.get("content", ""), \
            "NISE deep-dive deve mencionar FLOWISE"
        assert "LGPD" in nise_slide.deep_dive_content.get("content", ""), \
            "NISE deep-dive deve mencionar LGPD"

        # Verifica MINERVA e PIERRE (índices 10 e 11)
        minerva_slide = slides[10]
        assert "8008" in minerva_slide.deep_dive_content.get("content", ""), \
            "MINERVA deep-dive deve mencionar porta 8008"
        pierre_slide = slides[11]
        assert "8009" in pierre_slide.deep_dive_content.get("content", ""), \
            "PIERRE deep-dive deve mencionar porta 8009"

        print("     WANDA: Fase 3 OK | NISE: FLOWISE+LGPD OK | MINERVA+PIERRE: OK")
        return True

    except Exception as e:
        print(f"  ❌ Erro ao criar slides V3: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_theme_loading():
    """Testa carregamento de temas."""
    print("\n🧪 Testando carregamento de temas...")
    
    try:
        from utils.config import THEMES_DIR
        import json
        
        # Testa tema dark
        dark_path = THEMES_DIR / "dark.json"
        if not dark_path.exists():
            print(f"  ❌ Tema dark não encontrado: {dark_path}")
            return False
            
        with open(dark_path) as f:
            dark_theme = json.load(f)
        print(f"  ✅ Tema dark carregado ({len(dark_theme)} cores)")
        
        # Testa tema light
        light_path = THEMES_DIR / "light.json"
        if not light_path.exists():
            print(f"  ❌ Tema light não encontrado: {light_path}")
            return False
            
        with open(light_path) as f:
            light_theme = json.load(f)
        print(f"  ✅ Tema light carregado ({len(light_theme)} cores)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao carregar temas: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("\n" + "="*60)
    print("🎭 TESTE DA APRESENTAÇÃO INTELLICARE")
    print("="*60 + "\n")
    
    results = []
    
    # Testa imports
    results.append(("Imports", test_imports()))
    
    # Testa criação de slides
    results.append(("Criação de Slides", test_slide_creation()))
    results.append(("Criação de Slides V2", test_v2_slide_creation()))
    results.append(("Criação de Slides V3", test_v3_slide_creation()))

    # Testa carregamento de temas
    results.append(("Carregamento de Temas", test_theme_loading()))
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {name}: {status}")
        
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("\n✅ A apresentação está pronta para ser executada:")
        print("   python main.py --voz offline")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("\nVerifique os erros acima e corrija antes de executar.")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

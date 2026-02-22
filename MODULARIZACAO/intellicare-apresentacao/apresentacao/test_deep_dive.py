"""
Testes para o sistema de Deep Dive (TICKET-005).
"""

import sys
import os

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_overlay_creation():
    """Testa criação de overlay."""
    from core.overlay import TextOverlay
    
    overlay = TextOverlay(
        title="Teste",
        content="Conteúdo de teste"
    )
    
    assert overlay.title == "Teste"
    assert overlay.content == "Conteúdo de teste"
    assert overlay.alpha == 0  # Começa invisível
    assert overlay.is_closing == False
    print("✅ Overlay criado corretamente")

def test_overlay_animation():
    """Testa animação de fade-in."""
    from core.overlay import TextOverlay
    
    overlay = TextOverlay("Teste", "Conteúdo")
    
    # Simula 0.15s (metade da animação)
    is_complete = overlay.update(0.15)
    assert not is_complete
    assert overlay.alpha > 0
    assert overlay.alpha < 255
    print(f"✅ Fade-in funcionando (alpha={overlay.alpha})")
    
    # Completa animação
    overlay.update(0.15)
    assert overlay.alpha == 255
    print("✅ Fade-in completo")

def test_overlay_close():
    """Testa fechamento de overlay."""
    from core.overlay import TextOverlay
    
    overlay = TextOverlay("Teste", "Conteúdo")
    overlay.update(0.3)  # Completa fade-in
    
    overlay.close()
    assert overlay.is_closing == True
    assert overlay.animation_time == 0.0
    
    # Simula fade-out
    is_complete = overlay.update(0.3)
    assert is_complete
    assert overlay.alpha == 0
    print("✅ Fade-out funcionando")

def test_base_slide_deep_dive():
    """Testa suporte a deep dive no BaseSlide."""
    from slides.content_slide import ContentSlide
    
    slide = ContentSlide(
        title="Teste",
        content=["Item 1", "Item 2"]
    )
    
    # Sem deep dive
    assert not slide.has_deep_dive()
    assert slide.current_overlay is None
    
    # Adiciona deep dive
    slide.deep_dive_content = {
        "title": "Detalhes",
        "content": "Conteúdo detalhado"
    }
    
    assert slide.has_deep_dive()
    print("✅ BaseSlide detecta deep dive")
    
    # Abre deep dive
    slide.open_deep_dive()
    assert slide.current_overlay is not None
    assert slide.current_overlay.title == "Detalhes"
    print("✅ Deep dive aberto")
    
    # Fecha deep dive
    slide.close_deep_dive()
    assert slide.current_overlay.is_closing
    print("✅ Deep dive fechado")

def test_slide_update_with_overlay():
    """Testa atualização de slide com overlay."""
    from slides.content_slide import ContentSlide
    
    slide = ContentSlide("Teste", ["Item 1"])
    slide.deep_dive_content = {"title": "Detalhes", "content": "Teste"}
    
    # Abre overlay
    slide.open_deep_dive()
    assert slide.current_overlay is not None
    
    # Atualiza (fade-in)
    slide.update(0.15, 0.0)
    assert slide.current_overlay is not None
    assert slide.current_overlay.alpha > 0
    
    # Fecha overlay
    slide.close_deep_dive()
    
    # Atualiza até fade-out completo
    slide.update(0.3, 0.0)
    assert slide.current_overlay is None  # Removido após fade-out
    print("✅ Slide atualiza overlay corretamente")

def test_v1_slide2_has_deep_dive():
    """Testa se Slide 2 da V1 tem deep dive."""
    from versoes.v1_visao_geral.slides import create_v1_slides
    
    slides = create_v1_slides()
    slide2 = slides[1]  # Slide 2 (índice 1)
    
    assert slide2.has_deep_dive()
    assert slide2.deep_dive_content is not None
    assert "Arquitetura" in slide2.deep_dive_content["title"]
    print("✅ Slide 2 da V1 tem deep dive configurado")

def run_all_tests():
    """Executa todos os testes."""
    print("\n🧪 TESTANDO SISTEMA DE DEEP DIVE (TICKET-005)\n")
    print("=" * 60)
    
    tests = [
        ("Criação de Overlay", test_overlay_creation),
        ("Animação de Fade-in", test_overlay_animation),
        ("Fechamento de Overlay", test_overlay_close),
        ("BaseSlide com Deep Dive", test_base_slide_deep_dive),
        ("Atualização de Slide com Overlay", test_slide_update_with_overlay),
        ("Slide 2 V1 tem Deep Dive", test_v1_slide2_has_deep_dive),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n📋 {name}:")
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ FALHOU: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"\n📊 RESULTADO: {passed}/{len(tests)} testes passaram")
    
    if failed == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("\n✅ Critérios de Aceite:")
        print("   [✓] Overlay criado com fade-in/fade-out")
        print("   [✓] BaseSlide suporta deep dive")
        print("   [✓] Slide 2 tem deep dive configurado")
        print("   [✓] Animações funcionando corretamente")
        return True
    else:
        print(f"\n❌ {failed} teste(s) falharam")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)


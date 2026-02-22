#!/usr/bin/env python3
"""
IntelliCare - Apresentação Interativa com Wanda
Apresentação Python com IA narradora
"""

import argparse
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.presentation_engine import PresentationEngine
from versoes.v1_visao_geral.slides import create_v1_slides
from versoes.v2_agentes.slides import create_v2_slides
from versoes.v3_agentes_completo.slides import create_v3_slides
from versoes.v3_investidores.slides import create_v3_investidores_slides


def main():
    """Função principal da apresentação."""
    parser = argparse.ArgumentParser(
        description="IntelliCare - Apresentação Interativa com Wanda"
    )
    parser.add_argument(
        "--versao",
        default="v1_visao_geral",
        choices=["v1_visao_geral", "v2_agentes", "v3_agentes_completo", "v3_investidores"],
        help="Versão da apresentação"
    )
    parser.add_argument(
        "--tema",
        default="dark",
        choices=["dark", "light"],
        help="Tema visual"
    )
    parser.add_argument(
        "--voz",
        default="offline",
        choices=["online", "offline"],
        help="Modo de TTS (online=OpenAI, offline=pyttsx3)"
    )
    parser.add_argument(
        "--agente-imagem",
        default="cartoon",
        choices=["cartoon", "real", "dual"],
        help="Estilo visual das imagens dos agentes na V2"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1920,
        help="Largura da janela"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1080,
        help="Altura da janela"
    )
    
    args = parser.parse_args()
    
    try:
        # Cria engine de apresentação
        engine = PresentationEngine(
            width=args.width,
            height=args.height,
            theme=args.tema,
            tts_mode=args.voz
        )
        
        # Carrega slides da versão selecionada
        if args.versao == "v1_visao_geral":
            slides = create_v1_slides()
            for slide in slides:
                engine.add_slide(slide)
        elif args.versao == "v2_agentes":
            slides = create_v2_slides(image_style=args.agente_imagem)
            for slide in slides:
                engine.add_slide(slide)
        elif args.versao == "v3_agentes_completo":
            slides = create_v3_slides(image_style=args.agente_imagem)
            for slide in slides:
                engine.add_slide(slide)
        elif args.versao == "v3_investidores":
            slides = create_v3_investidores_slides(image_style=args.agente_imagem)
            for slide in slides:
                engine.add_slide(slide)
        
        # Executa apresentação
        engine.run()
        
    except KeyboardInterrupt:
        print("\n\nApresentacao encerrada pelo usuario.")
    except Exception as e:
        print(f"\nErro ao executar apresentacao: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

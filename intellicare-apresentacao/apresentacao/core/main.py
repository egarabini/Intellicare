import os
import sys

# Adiciona diretório atual ao path para imports funcionarem
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from core.presentation_engine import PresentationEngine
from content.v4_slides import create_v4_presentation

def main():
    # Inicializa engine
    # tts_mode="online" tenta usar OpenAI (se tiver chave), senao cai para offline
    # tts_mode="offline" usa pyttsx3 direto
    engine = PresentationEngine(
        width=1280, 
        height=720, 
        theme="dark",
        tts_mode="offline" 
    )
    
    # Carrega slides da V4 (Agentes)
    create_v4_presentation(engine)
    
    # Roda apresentação
    engine.run()

if __name__ == "__main__":
    main()
"""
Configurações da apresentação.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Diretório raiz da apresentação
ROOT_DIR = Path(__file__).parent.parent

# Diretórios
ASSETS_DIR = ROOT_DIR / "assets"
THEMES_DIR = ASSETS_DIR / "themes"
FONTS_DIR = ASSETS_DIR / "fonts"
IMAGES_DIR = ASSETS_DIR / "images"
AUDIO_DIR = ASSETS_DIR / "audio"


class Config:
    """Configurações globais da apresentação."""
    
    # Tela
    SCREEN_WIDTH = int(os.getenv("SCREEN_WIDTH", "1920"))
    SCREEN_HEIGHT = int(os.getenv("SCREEN_HEIGHT", "1080"))
    FPS = 60
    
    # Tema
    DEFAULT_THEME = os.getenv("DEFAULT_THEME", "dark")
    
    # TTS
    TTS_MODE = os.getenv("TTS_MODE", "offline")  # "online" ou "offline"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    TTS_VOICE = "nova"  # Voz feminina natural da OpenAI
    TTS_MODEL = "tts-1-hd"
    
    # Narração
    NARRATION_RATE = 150  # Velocidade da fala (palavras por minuto)
    NARRATION_VOLUME = 0.9
    
    # Animações
    ANIMATION_SPEED = 1.0  # Multiplicador de velocidade
    FADE_DURATION = 0.5  # Duração do fade in/out (segundos)
    TYPEWRITER_SPEED = 0.05  # Delay entre caracteres (segundos)
    
    # Avatar da Wanda
    WANDA_AVATAR_SIZE = 80
    WANDA_AVATAR_POSITION = (50, 50)  # Canto superior esquerdo
    
    @classmethod
    def get_theme_path(cls, theme_name: str) -> Path:
        """Retorna o caminho do arquivo de tema."""
        return THEMES_DIR / f"{theme_name}.json"


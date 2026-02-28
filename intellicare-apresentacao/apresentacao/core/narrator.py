"""
Gerenciador de narração (TTS).
"""

import pygame
import os
from pathlib import Path
from typing import Optional

# Importa TTS engines
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


class Narrator:
    """Gerencia narração com TTS (online ou offline)."""
    
    def __init__(self, mode: str = "offline", voice: str = "nova"):
        """
        Inicializa o narrador.
        
        Args:
            mode: "online" (OpenAI) ou "offline" (pyttsx3)
            voice: Nome da voz (para OpenAI)
        """
        self.mode = mode
        self.voice = voice
        self.is_muted = False
        self.current_audio = None
        
        # Inicializa pygame mixer
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        # Configura TTS baseado no modo
        if mode == "online":
            if not OPENAI_AVAILABLE:
                print("⚠️  OpenAI não disponível. Usando modo offline.")
                self.mode = "offline"
            else:
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    print("⚠️  OPENAI_API_KEY não configurada. Usando modo offline.")
                    self.mode = "offline"
                else:
                    self.client = OpenAI(api_key=api_key)
                    
        if self.mode == "offline":
            if not PYTTSX3_AVAILABLE:
                print("❌ pyttsx3 não disponível. Narração desabilitada.")
                self.mode = "none"
            else:
                self.engine = pyttsx3.init()
                self._configure_offline_voice()
                
    def _configure_offline_voice(self):
        """Configura voz offline (pyttsx3)."""
        if self.mode != "offline":
            return
            
        # Configura velocidade e volume
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 0.9)
        
        # Tenta encontrar voz em português
        voices = self.engine.getProperty('voices')
        for voice in voices:
            voice_name = voice.name.lower()
            if 'portuguese' in voice_name or 'brazil' in voice_name:
                self.engine.setProperty('voice', voice.id)
                break
                
    def speak(self, text: str, wait: bool = False) -> None:
        """
        Faz a narração do texto.
        
        Args:
            text: Texto a ser narrado
            wait: Se True, aguarda término da narração
        """
        if self.is_muted or self.mode == "none":
            return
            
        if self.mode == "online":
            self._speak_online(text, wait)
        else:
            self._speak_offline(text, wait)
            
    def _speak_online(self, text: str, wait: bool):
        """Narração online com OpenAI TTS."""
        try:
            # Gera áudio
            response = self.client.audio.speech.create(
                model="tts-1-hd",
                voice=self.voice,
                input=text
            )
            
            # Salva temporariamente
            temp_path = Path("temp_narration.mp3")
            response.stream_to_file(str(temp_path))
            
            # Reproduz
            pygame.mixer.music.load(str(temp_path))
            pygame.mixer.music.play()
            
            if wait:
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                    
        except Exception as e:
            print(f"❌ Erro na narração online: {e}")
            
    def _speak_offline(self, text: str, wait: bool):
        """Narração offline com pyttsx3."""
        try:
            self.engine.say(text)
            if wait:
                self.engine.runAndWait()
        except Exception as e:
            print(f"❌ Erro na narração offline: {e}")
            
    def stop(self) -> None:
        """Para a narração atual."""
        if self.mode == "online":
            pygame.mixer.music.stop()
        elif self.mode == "offline":
            self.engine.stop()
            
    def is_speaking(self) -> bool:
        """
        Verifica se está narrando.
        
        Returns:
            True se está narrando
        """
        if self.mode == "online":
            return pygame.mixer.music.get_busy()
        return False
        
    def toggle_mute(self) -> None:
        """Alterna mute/unmute."""
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.stop()
            
    def set_volume(self, volume: float) -> None:
        """
        Define o volume.
        
        Args:
            volume: Volume (0.0 a 1.0)
        """
        if self.mode == "online":
            pygame.mixer.music.set_volume(volume)
        elif self.mode == "offline":
            self.engine.setProperty('volume', volume)


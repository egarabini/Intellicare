"""
Wanda AI - Modulo de Voz e Inteligencia
========================================

Subsistema de narracao da apresentacao IntelliCare.
- WandaNarrator: TTS hibrido (OpenAI online / pyttsx3 offline)
"""

from .narrator import WandaNarrator

__all__ = ["WandaNarrator"]

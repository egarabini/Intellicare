"""
WandaNarrator - Modulo de Voz Hibrido
======================================

Gera e reproduz narracao para a apresentacao IntelliCare.

Modos de operacao:
  1. ONLINE  (prioritario) - OpenAI TTS (tts-1, voz "nova")
  2. OFFLINE (fallback)    - pyttsx3 (voz do sistema)

Recursos:
  - Cache inteligente: evita chamadas repetidas a API
  - Threading: reproducao nao bloqueia a thread principal
  - Fallback automatico: se OpenAI falha, usa pyttsx3 sem interrupcao

Uso:
    narrator = WandaNarrator()
    narrator.speak("Ola, eu sou a Wanda!")
    narrator.speak("Segundo texto...", wait=False)  # non-blocking
    narrator.wait()  # espera terminar
    narrator.shutdown()
"""

import hashlib
import logging
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("wanda.narrator")


class WandaNarrator:
    """
    Narradora hibrida da Wanda com cache, fallback e threading.

    Args:
        voice: Voz OpenAI TTS ("nova", "alloy", "echo", "fable", "onyx", "shimmer")
        model: Modelo TTS ("tts-1" para velocidade, "tts-1-hd" para qualidade)
        cache_dir: Diretorio para armazenar audios gerados
        force_offline: Se True, ignora OpenAI e usa pyttsx3 sempre
    """

    def __init__(
        self,
        voice: str = "nova",
        model: str = "tts-1",
        cache_dir: Optional[str] = None,
        force_offline: bool = False,
    ):
        self.voice = voice
        self.model = model
        self.force_offline = force_offline

        # Diretorio de cache (default: apresentacao/cache/)
        if cache_dir is None:
            self._cache_dir = Path(__file__).resolve().parent.parent / "cache"
        else:
            self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # Estado de reproducao
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Inicializacao lazy dos backends
        self._openai_client = None
        self._openai_available: Optional[bool] = None  # None = nao testado ainda
        self._pyttsx3_engine = None
        self._pyttsx3_available: Optional[bool] = None
        self._offline_warned = False

        logger.info(
            "WandaNarrator inicializado voice=%s model=%s cache=%s offline=%s",
            voice, model, self._cache_dir, force_offline,
        )

    # =========================================================================
    # API Publica
    # =========================================================================

    def speak(self, text: str, wait: bool = True, rate: int = 160, voice: Optional[str] = None) -> None:
        """
        Narra o texto fornecido.

        Args:
            text: Texto para narrar
            wait: Se True (default), bloqueia ate terminar. Se False, retorna imediatamente.
            rate: Velocidade da fala pyttsx3 (100-250). Ignorado no modo online.
            voice: Voz OpenAI a usar nesta chamada (ex: 'nova', 'shimmer'). Se None, usa self.voice.
        """
        if not text or not text.strip():
            return

        # Esperar reproducao anterior terminar (evita sobreposicao)
        self._wait_current()

        effective_voice = voice or self.voice

        self._stop_event.clear()
        self._playback_thread = threading.Thread(
            target=self._speak_worker,
            args=(text.strip(), rate, effective_voice),
            daemon=True,
        )
        self._playback_thread.start()

        if wait:
            self._playback_thread.join()

    def wait(self) -> None:
        """Bloqueia ate a reproducao atual terminar."""
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join()

    def stop(self) -> None:
        """Para a reproducao atual imediatamente."""
        self._stop_event.set()
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=2.0)

    def shutdown(self) -> None:
        """Encerra todos os recursos. Chamar ao final do programa."""
        self.stop()
        if self._pyttsx3_engine:
            try:
                self._pyttsx3_engine.stop()
            except Exception:
                pass
        logger.info("WandaNarrator encerrado")

    def clear_cache(self) -> int:
        """Remove todos os arquivos de cache. Retorna quantidade removida."""
        count = 0
        for f in self._cache_dir.glob("*.mp3"):
            f.unlink()
            count += 1
        logger.info("Cache limpo: %d arquivo(s) removido(s)", count)
        return count

    @property
    def is_online(self) -> bool:
        """Retorna True se OpenAI TTS esta disponivel."""
        if self.force_offline:
            return False
        if self._openai_available is None:
            self._init_openai()
        return bool(self._openai_available)

    @property
    def mode(self) -> str:
        """Retorna modo atual: 'online' ou 'offline'."""
        return "online" if self.is_online else "offline"

    # =========================================================================
    # Worker Thread (executa em background)
    # =========================================================================

    def _speak_worker(self, text: str, rate: int = 160, voice: Optional[str] = None) -> None:
        """Worker que executa a narracao na thread de background."""
        effective_voice = voice or self.voice
        try:
            # 1. Tentar cache (inclui voz na chave para diferenciar vozes)
            cache_path = self._get_cache_path(text, voice=effective_voice)
            if cache_path.exists():
                logger.debug("Cache hit: %s", cache_path.name)
                self._play_mp3(cache_path)
                return

            # 2. Tentar OpenAI TTS (online)
            if not self.force_offline:
                mp3_path = self._generate_openai(text, cache_path, voice=effective_voice)
                if mp3_path:
                    self._play_mp3(mp3_path)
                    return

            # 3. Fallback: pyttsx3 (offline)
            logger.info("Usando fallback offline (pyttsx3) rate=%d", rate)
            if self._speak_pyttsx3(text, rate=rate):
                return

            # 4. Fallback extra Windows: PowerShell SAPI
            if self._speak_powershell_sapi(text):
                return

        except Exception as e:
            logger.error("Erro na narracao: %s", e)
            # Ultimas tentativas de fallback
            try:
                if self._speak_pyttsx3(text):
                    return
                self._speak_powershell_sapi(text)
            except Exception as e2:
                logger.error("Fallback tambem falhou: %s", e2)

    # =========================================================================
    # Backend: OpenAI TTS
    # =========================================================================

    def _init_openai(self) -> None:
        """Inicializa o cliente OpenAI (lazy)."""
        if self._openai_available is not None:
            return

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY nao definida - modo offline")
            self._openai_available = False
            return

        try:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=api_key)
            self._openai_available = True
            logger.info("OpenAI TTS disponivel (modelo=%s, voz=%s)", self.model, self.voice)
        except ImportError:
            logger.warning("Pacote 'openai' nao instalado - modo offline")
            self._openai_available = False
        except Exception as e:
            logger.warning("Falha ao inicializar OpenAI: %s - modo offline", e)
            self._openai_available = False

    def _generate_openai(self, text: str, cache_path: Path, voice: Optional[str] = None) -> Optional[Path]:
        """Gera MP3 via OpenAI TTS e salva no cache."""
        self._init_openai()
        if not self._openai_available or not self._openai_client:
            return None

        effective_voice = voice or self.voice
        try:
            logger.debug("Gerando TTS OpenAI: '%s...' (%d chars) voice=%s", text[:40], len(text), effective_voice)

            response = self._openai_client.audio.speech.create(
                model=self.model,
                voice=effective_voice,
                input=text,
            )

            # Salvar no cache
            response.stream_to_file(str(cache_path))
            logger.info("Audio salvo no cache: %s", cache_path.name)
            return cache_path

        except Exception as e:
            logger.warning("OpenAI TTS falhou: %s - usando fallback", e)
            # Marcar como indisponivel para evitar tentativas repetidas na mesma sessao
            # (pode ser problema temporario, mas evita travamentos)
            self._openai_available = False
            return None

    # =========================================================================
    # Backend: pyttsx3 (Offline)
    # =========================================================================

    @staticmethod
    def _select_female_voice(voices) -> Optional[str]:
        """Seleciona voz feminina preferencial para Wanda (evita vozes masculinas).

        Prioridade: Maria (PT-BR) > Helena (PT-BR) > Zira (EN) > qualquer com 'female'
        Evita: David, Mark, James, etc.
        """
        if not voices:
            return None
        name_lower = lambda v: (getattr(v, "name", "") or str(v)).lower()
        male_keywords = ("david", "mark", "james", "paul", "george", "male", "daniel")
        female_keywords_pt = ("maria", "helena")  # Vozes PT-BR femininas
        female_keywords_en = ("zira",)  # Windows EN feminina
        female_keywords_any = ("female", "feminin", "mulher")

        # 1. Preferir Maria ou Helena (PT-BR)
        for v in voices:
            n = name_lower(v)
            if any(k in n for k in female_keywords_pt) and not any(k in n for k in male_keywords):
                return v.id

        # 2. Zira (EN) ou qualquer com 'female'
        for v in voices:
            n = name_lower(v)
            if any(k in n for k in female_keywords_en + female_keywords_any) and not any(k in n for k in male_keywords):
                return v.id

        # 3. Qualquer voz que nao seja claramente masculina
        for v in voices:
            n = name_lower(v)
            if not any(k in n for k in male_keywords):
                return v.id

        return None

    def _init_pyttsx3(self) -> None:
        """Inicializa engine pyttsx3 (lazy)."""
        if self._pyttsx3_available is False:
            raise RuntimeError("pyttsx3 indisponivel neste ambiente")

        if self._pyttsx3_engine is not None:
            return

        try:
            import pyttsx3
            self._pyttsx3_engine = pyttsx3.init()
            voices = self._pyttsx3_engine.getProperty("voices")
            voice_id = self._select_female_voice(voices)
            if voice_id:
                self._pyttsx3_engine.setProperty("voice", voice_id)
                logger.info("pyttsx3: voz feminina selecionada")
            else:
                logger.warning("pyttsx3: nenhuma voz feminina encontrada, usando padrao do sistema")
            self._pyttsx3_engine.setProperty("rate", 160)
            self._pyttsx3_available = True
            logger.info("pyttsx3 inicializado")
        except ImportError:
            self._pyttsx3_available = False
            logger.error("Pacote 'pyttsx3' nao instalado - narracao indisponivel")
            raise
        except Exception as e:
            self._pyttsx3_available = False
            if not self._offline_warned:
                logger.error("Falha ao inicializar pyttsx3: %s", e)
                self._offline_warned = True
            raise

    def _speak_pyttsx3(self, text: str, rate: int = 160) -> bool:
        """Gera WAV via pyttsx3 e reproduz via pygame.mixer.

        Estrategia: pyttsx3 salva audio em arquivo WAV (sem conflito de
        dispositivo) e pygame.mixer reproduz (mesmo dispositivo de audio
        da apresentacao).  WAV e mantido como cache para reproducoes
        futuras da mesma frase (rate incluido na chave de cache).
        """
        try:
            if self._stop_event.is_set():
                return True

            # Inclui "female" no cache para invalidar cache antigo com voz masculina
            cache_key = f"female:{rate}:{text}"
            wav_path = self._cache_dir / f"_offline_{hashlib.md5(cache_key.encode()).hexdigest()}.wav"

            # Gerar WAV apenas se nao estiver em cache
            if not wav_path.exists():
                import pyttsx3

                engine = pyttsx3.init()
                voices = engine.getProperty("voices")
                voice_id = self._select_female_voice(voices)
                if voice_id:
                    engine.setProperty("voice", voice_id)
                engine.setProperty("rate", rate)

                engine.save_to_file(text, str(wav_path))
                engine.runAndWait()
                engine.stop()

                if not wav_path.exists():
                    logger.warning("pyttsx3: WAV nao foi gerado")
                    return False

                logger.info("WAV offline gerado: %s", wav_path.name)

            if self._stop_event.is_set():
                return True

            # Reproduzir via pygame.mixer (mesmo dispositivo da apresentacao)
            played = self._play_with_pygame(wav_path)
            if not played:
                played = self._play_with_playsound(wav_path)
            return played
        except ImportError:
            logger.warning("pyttsx3 nao instalado")
            return False
        except Exception as e:
            logger.warning("pyttsx3 falhou: %s", e)
            return False

    def _speak_powershell_sapi(self, text: str) -> bool:
        """Fallback de voz para Windows via PowerShell/System.Speech."""
        import platform
        import subprocess

        if platform.system().lower() != "windows":
            return False
        if self._stop_event.is_set():
            return True

        escaped = text.replace("'", "''")
        cmd = (
            "Add-Type -AssemblyName System.Speech; "
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.Rate=0; "
            f"$s.Speak('{escaped}')"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                timeout=120,
            )
            return result.returncode == 0
        except Exception:
            return False

    # =========================================================================
    # Player MP3
    # =========================================================================

    def _play_mp3(self, path: Path) -> None:
        """Reproduz arquivo MP3. Tenta pygame.mixer, fallback para playsound."""
        if self._stop_event.is_set():
            return

        # Tentativa 1: pygame.mixer (ideal quando engine grafica ja esta rodando)
        if self._play_with_pygame(path):
            return

        # Tentativa 2: playsound (standalone, sem dependencia pesada)
        if self._play_with_playsound(path):
            return

        # Tentativa 3: player nativo do OS
        self._play_with_system(path)

    def _play_with_pygame(self, path: Path) -> bool:
        """Tenta reproduzir com pygame.mixer."""
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if self._stop_event.is_set():
                    pygame.mixer.music.stop()
                    return True
                time.sleep(0.05)
            return True
        except Exception:
            return False

    def _play_with_playsound(self, path: Path) -> bool:
        """Tenta reproduzir com playsound."""
        try:
            from playsound import playsound
            playsound(str(path))
            return True
        except Exception:
            return False

    def _play_with_system(self, path: Path) -> None:
        """Reproduz usando player nativo do OS (ultimo recurso)."""
        import subprocess
        import sys

        try:
            if sys.platform == "win32":
                # Windows Media Player silencioso
                subprocess.run(
                    ["powershell", "-c",
                     f'(New-Object Media.SoundPlayer "{path}").PlaySync()'],
                    capture_output=True, timeout=60,
                )
            elif sys.platform == "darwin":
                subprocess.run(["afplay", str(path)], capture_output=True, timeout=60)
            else:
                # Linux: aplay, mpg123, ou ffplay
                for player in ["mpg123", "ffplay -nodisp -autoexit", "aplay"]:
                    cmd = player.split() + [str(path)]
                    result = subprocess.run(cmd, capture_output=True, timeout=60)
                    if result.returncode == 0:
                        break
        except Exception as e:
            logger.warning("Reproducao via sistema falhou: %s", e)

    # =========================================================================
    # Cache
    # =========================================================================

    def _get_cache_path(self, text: str, voice: Optional[str] = None) -> Path:
        """Gera path de cache baseado em hash do texto + voz + modelo."""
        effective_voice = voice or self.voice
        key = f"{self.model}:{effective_voice}:{text}"
        digest = hashlib.md5(key.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.mp3"

    # =========================================================================
    # Helpers
    # =========================================================================

    def _wait_current(self) -> None:
        """Espera reproducao atual terminar antes de iniciar nova."""
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join()

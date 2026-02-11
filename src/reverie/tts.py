"""Text-to-speech narration for Reverie.

Uses edge-tts for high-quality async speech synthesis.
"""

import asyncio
import os
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable
import subprocess

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False


@dataclass
class TTSConfig:
    """TTS configuration."""
    enabled: bool = False
    voice: str = "en-US-JennyNeural"
    rate: str = "+0%"
    volume: str = "+0%"
    pitch: str = "+0Hz"


class TTSEngine:
    """Text-to-speech engine with async playback.
    
    Uses edge-tts for synthesis and system audio player for playback.
    Playback is non-blocking - new speech cancels previous.
    """

    def __init__(self, config: Optional[TTSConfig] = None):
        """Initialize TTS engine.
        
        Args:
            config: TTS configuration. Uses defaults if None.
        """
        self.config = config or TTSConfig()
        self._current_process: Optional[subprocess.Popen] = None
        self._playback_thread: Optional[threading.Thread] = None
        self._temp_dir = Path(tempfile.gettempdir()) / "reverie_tts"
        self._temp_dir.mkdir(exist_ok=True)

    @property
    def available(self) -> bool:
        """Check if TTS is available."""
        return EDGE_TTS_AVAILABLE and self.config.enabled

    def speak(self, text: str, callback: Optional[Callable[[], None]] = None) -> bool:
        """Speak text asynchronously.
        
        Args:
            text: Text to speak.
            callback: Optional callback when playback completes.
            
        Returns:
            True if speech started, False if TTS unavailable.
        """
        if not self.available:
            return False

        # Cancel any current playback
        self.stop()

        # Start playback in background thread
        self._playback_thread = threading.Thread(
            target=self._speak_async,
            args=(text, callback),
            daemon=True,
        )
        self._playback_thread.start()
        return True

    def _speak_async(self, text: str, callback: Optional[Callable[[], None]] = None):
        """Synthesize and play speech (runs in thread)."""
        try:
            # Run async synthesis
            asyncio.run(self._synthesize_and_play(text))
        except Exception:
            pass  # Silently ignore TTS errors
        finally:
            if callback:
                callback()

    async def _synthesize_and_play(self, text: str):
        """Synthesize text to audio and play it."""
        # Generate unique temp file
        audio_path = self._temp_dir / f"speech_{id(text)}.mp3"

        try:
            # Synthesize with edge-tts
            communicate = edge_tts.Communicate(
                text,
                self.config.voice,
                rate=self.config.rate,
                volume=self.config.volume,
                pitch=self.config.pitch,
            )
            await communicate.save(str(audio_path))

            # Play audio
            self._play_audio(audio_path)
        finally:
            # Cleanup temp file
            try:
                audio_path.unlink(missing_ok=True)
            except Exception:
                pass

    def _play_audio(self, path: Path):
        """Play audio file using system player."""
        import platform

        system = platform.system()

        if system == "Darwin":  # macOS
            cmd = ["afplay", str(path)]
        elif system == "Linux":
            # Try different players
            for player in ["aplay", "paplay", "mpv", "ffplay"]:
                if self._command_exists(player):
                    if player in ("mpv", "ffplay"):
                        cmd = [player, "-nodisp", "-autoexit", str(path)]
                    else:
                        cmd = [player, str(path)]
                    break
            else:
                return  # No player found
        elif system == "Windows":
            # Use PowerShell to play audio
            cmd = [
                "powershell",
                "-c",
                f'(New-Object Media.SoundPlayer "{path}").PlaySync()',
            ]
        else:
            return  # Unknown system

        try:
            self._current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._current_process.wait()
        except Exception:
            pass
        finally:
            self._current_process = None

    def _command_exists(self, cmd: str) -> bool:
        """Check if a command exists on the system."""
        try:
            subprocess.run(
                ["which", cmd],
                capture_output=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def stop(self):
        """Stop current playback."""
        if self._current_process:
            try:
                self._current_process.terminate()
                self._current_process.wait(timeout=1)
            except Exception:
                try:
                    self._current_process.kill()
                except Exception:
                    pass
            self._current_process = None

    def set_enabled(self, enabled: bool):
        """Enable or disable TTS."""
        self.config.enabled = enabled
        if not enabled:
            self.stop()

    def set_voice(self, voice: str):
        """Set the voice to use."""
        self.config.voice = voice


# Available voices (subset of edge-tts voices)
VOICES = {
    "jenny": "en-US-JennyNeural",
    "guy": "en-US-GuyNeural",
    "aria": "en-US-AriaNeural",
    "davis": "en-US-DavisNeural",
    "amber": "en-US-AmberNeural",
    "ana": "en-US-AnaNeural",
    "andrew": "en-US-AndrewNeural",
    "ashley": "en-US-AshleyNeural",
    "brian": "en-US-BrianNeural",
    "cora": "en-US-CoraNeural",
    "elizabeth": "en-US-ElizabethNeural",
    "emma": "en-US-EmmaNeural",
    "eric": "en-US-EricNeural",
    "jacob": "en-US-JacobNeural",
    "jane": "en-US-JaneNeural",
    "jason": "en-US-JasonNeural",
    "michelle": "en-US-MichelleNeural",
    "monica": "en-US-MonicaNeural",
    "nancy": "en-US-NancyNeural",
    "roger": "en-US-RogerNeural",
    "sara": "en-US-SaraNeural",
    "steffan": "en-US-SteffanNeural",
    "tony": "en-US-TonyNeural",
    # British voices
    "sonia": "en-GB-SoniaNeural",
    "ryan": "en-GB-RyanNeural",
    "libby": "en-GB-LibbyNeural",
    "maisie": "en-GB-MaisieNeural",
    "thomas": "en-GB-ThomasNeural",
}


def get_voice_name(short_name: str) -> str:
    """Get full voice name from short name."""
    return VOICES.get(short_name.lower(), short_name)


def list_voices() -> list[str]:
    """List available voice short names."""
    return sorted(VOICES.keys())

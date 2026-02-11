"""Tests for TTS module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import threading
import time

from reverie.tts import (
    TTSConfig,
    TTSEngine,
    VOICES,
    get_voice_name,
    list_voices,
    EDGE_TTS_AVAILABLE,
)


class TestTTSConfig:
    """Tests for TTSConfig."""

    def test_default_config(self):
        """Default config has TTS disabled."""
        config = TTSConfig()
        assert config.enabled is False
        assert config.voice == "en-US-JennyNeural"
        assert config.rate == "+0%"

    def test_custom_config(self):
        """Can create custom config."""
        config = TTSConfig(
            enabled=True,
            voice="en-US-GuyNeural",
            rate="+10%",
        )
        assert config.enabled is True
        assert config.voice == "en-US-GuyNeural"
        assert config.rate == "+10%"


class TestTTSEngine:
    """Tests for TTSEngine."""

    def test_engine_creation(self):
        """Can create TTS engine."""
        engine = TTSEngine()
        assert engine.config is not None
        assert engine.config.enabled is False

    def test_engine_with_config(self):
        """Can create engine with custom config."""
        config = TTSConfig(enabled=True, voice="en-US-GuyNeural")
        engine = TTSEngine(config)
        assert engine.config.enabled is True
        assert engine.config.voice == "en-US-GuyNeural"

    def test_available_when_disabled(self):
        """Engine not available when disabled."""
        config = TTSConfig(enabled=False)
        engine = TTSEngine(config)
        assert engine.available is False

    @pytest.mark.skipif(not EDGE_TTS_AVAILABLE, reason="edge-tts not installed")
    def test_available_when_enabled(self):
        """Engine available when enabled and edge-tts installed."""
        config = TTSConfig(enabled=True)
        engine = TTSEngine(config)
        assert engine.available is True

    def test_speak_returns_false_when_unavailable(self):
        """speak() returns False when TTS unavailable."""
        config = TTSConfig(enabled=False)
        engine = TTSEngine(config)
        result = engine.speak("Hello world")
        assert result is False

    def test_set_enabled(self):
        """Can enable/disable TTS."""
        engine = TTSEngine()
        assert engine.config.enabled is False

        engine.set_enabled(True)
        assert engine.config.enabled is True

        engine.set_enabled(False)
        assert engine.config.enabled is False

    def test_set_voice(self):
        """Can change voice."""
        engine = TTSEngine()
        engine.set_voice("en-US-GuyNeural")
        assert engine.config.voice == "en-US-GuyNeural"

    def test_stop_no_process(self):
        """stop() works even with no active process."""
        engine = TTSEngine()
        engine.stop()  # Should not raise

    @patch("reverie.tts.subprocess.Popen")
    def test_stop_terminates_process(self, mock_popen):
        """stop() terminates active process."""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        engine = TTSEngine()
        engine._current_process = mock_process

        engine.stop()

        mock_process.terminate.assert_called_once()


class TestVoices:
    """Tests for voice utilities."""

    def test_voices_dict_not_empty(self):
        """VOICES dict has entries."""
        assert len(VOICES) > 0

    def test_voices_have_neural_suffix(self):
        """All voices end with Neural."""
        for name, full_name in VOICES.items():
            assert full_name.endswith("Neural"), f"{name}: {full_name}"

    def test_get_voice_name_known(self):
        """get_voice_name returns full name for known voice."""
        assert get_voice_name("jenny") == "en-US-JennyNeural"
        assert get_voice_name("guy") == "en-US-GuyNeural"

    def test_get_voice_name_case_insensitive(self):
        """get_voice_name is case insensitive."""
        assert get_voice_name("JENNY") == "en-US-JennyNeural"
        assert get_voice_name("Jenny") == "en-US-JennyNeural"

    def test_get_voice_name_unknown(self):
        """get_voice_name returns input for unknown voice."""
        assert get_voice_name("custom-voice") == "custom-voice"

    def test_list_voices(self):
        """list_voices returns sorted list."""
        voices = list_voices()
        assert len(voices) > 0
        assert voices == sorted(voices)
        assert "jenny" in voices
        assert "guy" in voices


class TestTTSEngineAsync:
    """Tests for async TTS functionality."""

    @pytest.mark.skipif(not EDGE_TTS_AVAILABLE, reason="edge-tts not installed")
    @patch("reverie.tts.TTSEngine._play_audio")
    def test_speak_starts_thread(self, mock_play):
        """speak() starts background thread."""
        config = TTSConfig(enabled=True)
        engine = TTSEngine(config)

        result = engine.speak("Hello")
        assert result is True
        assert engine._playback_thread is not None

        # Wait for thread to start
        time.sleep(0.1)
        engine.stop()

    @pytest.mark.skipif(not EDGE_TTS_AVAILABLE, reason="edge-tts not installed")
    def test_speak_with_callback(self):
        """speak() calls callback when done."""
        config = TTSConfig(enabled=True)
        engine = TTSEngine(config)
        callback_called = threading.Event()

        def callback():
            callback_called.set()

        with patch.object(engine, "_synthesize_and_play"):
            result = engine.speak("Hello", callback=callback)
            assert result is True

            # Wait for callback
            callback_called.wait(timeout=2)
            assert callback_called.is_set()

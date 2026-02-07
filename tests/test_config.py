"""Tests for configuration module."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from reverie.config import (
    AudioConfig,
    DisplayConfig,
    GameplayConfig,
    LLMConfig,
    ReverieConfig,
    get_config_dir,
    get_config_path,
    get_data_dir,
    load_config,
)


class TestConfigPaths:
    def test_get_config_dir_default(self, monkeypatch):
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        config_dir = get_config_dir()
        assert config_dir == Path.home() / ".config" / "reverie"

    def test_get_config_dir_xdg(self, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")
        config_dir = get_config_dir()
        assert config_dir == Path("/custom/config/reverie")

    def test_get_data_dir_default(self, monkeypatch):
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        data_dir = get_data_dir()
        assert data_dir == Path.home() / ".local" / "share" / "reverie"

    def test_get_data_dir_xdg(self, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")
        data_dir = get_data_dir()
        assert data_dir == Path("/custom/data/reverie")


class TestLLMConfig:
    def test_defaults(self):
        config = LLMConfig()
        assert config.provider == "ollama"
        assert config.model == "llama3.1"
        assert config.endpoint == "http://localhost:11434"
        assert config.timeout == 30
        assert config.api_key is None


class TestReverieConfig:
    def test_default_config(self):
        config = ReverieConfig()
        assert config.llm.provider == "ollama"
        assert config.audio.enabled is False
        assert config.display.color_scheme == "dark"
        assert config.gameplay.auto_save is True

    def test_load_missing_file(self):
        config = ReverieConfig.load(Path("/nonexistent/config.toml"))
        # Should return defaults
        assert config.llm.provider == "ollama"

    def test_load_from_file(self):
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("""
[llm]
provider = "openai"
model = "gpt-4"

[gameplay]
difficulty = "hard"
""")
            config = ReverieConfig.load(config_path)
            assert config.llm.provider == "openai"
            assert config.llm.model == "gpt-4"
            assert config.gameplay.difficulty == "hard"
            # Defaults for unspecified
            assert config.audio.enabled is False

    def test_env_override_provider(self, monkeypatch):
        monkeypatch.setenv("REVERIE_LLM_PROVIDER", "openai")
        config = ReverieConfig.load(Path("/nonexistent"))
        assert config.llm.provider == "openai"

    def test_env_override_model(self, monkeypatch):
        monkeypatch.setenv("REVERIE_LLM_MODEL", "custom-model")
        config = ReverieConfig.load(Path("/nonexistent"))
        assert config.llm.model == "custom-model"

    def test_env_override_api_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")
        config = ReverieConfig.load(Path("/nonexistent"))
        assert config.llm.api_key == "sk-test123"

    def test_save_and_reload(self):
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            
            config = ReverieConfig()
            config.llm.provider = "openai"
            config.gameplay.difficulty = "hard"
            config.save(config_path)

            assert config_path.exists()

            loaded = ReverieConfig.load(config_path)
            assert loaded.llm.provider == "openai"
            assert loaded.gameplay.difficulty == "hard"

    def test_save_creates_directory(self):
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "subdir" / "config.toml"
            config = ReverieConfig()
            config.save(config_path)
            assert config_path.exists()


class TestLoadConfig:
    def test_convenience_function(self):
        config = load_config(Path("/nonexistent"))
        assert isinstance(config, ReverieConfig)

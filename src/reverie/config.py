"""Configuration management for Reverie."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import toml


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "reverie"
    return Path.home() / ".config" / "reverie"


def get_config_path() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.toml"


def get_data_dir() -> Path:
    """Get the data directory path."""
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        return Path(xdg_data) / "reverie"
    return Path.home() / ".local" / "share" / "reverie"


@dataclass
class LLMConfig:
    """LLM provider configuration."""

    provider: str = "ollama"
    model: str = "llama3.1"
    endpoint: str = "http://localhost:11434"
    timeout: int = 30
    api_key: Optional[str] = None


@dataclass
class AudioConfig:
    """Audio/TTS configuration."""

    enabled: bool = False
    voice: str = "en-US-JennyNeural"


@dataclass
class DisplayConfig:
    """Display/color configuration."""

    color_scheme: str = "dark"
    narrator_color: str = "cyan"
    npc_color: str = "yellow"
    system_color: str = "dim"


@dataclass
class GameplayConfig:
    """Gameplay settings."""

    auto_save: bool = True
    difficulty: str = "normal"
    verbose_rolls: bool = True


@dataclass
class ReverieConfig:
    """Complete configuration for Reverie."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    gameplay: GameplayConfig = field(default_factory=GameplayConfig)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "ReverieConfig":
        """Load configuration from file with env var overrides."""
        config = cls()
        config_path = path or get_config_path()

        # Load from file if exists
        if config_path.exists():
            try:
                data = toml.load(config_path)
                config = cls._from_dict(data)
            except Exception:
                # Use defaults on parse error
                pass

        # Apply environment variable overrides
        config = cls._apply_env_overrides(config)

        return config

    @classmethod
    def _from_dict(cls, data: dict) -> "ReverieConfig":
        """Create config from dictionary."""
        llm_data = data.get("llm", {})
        audio_data = data.get("audio", {})
        display_data = data.get("display", {})
        gameplay_data = data.get("gameplay", {})

        return cls(
            llm=LLMConfig(
                provider=llm_data.get("provider", "ollama"),
                model=llm_data.get("model", "llama3.1"),
                endpoint=llm_data.get("endpoint", "http://localhost:11434"),
                timeout=llm_data.get("timeout", 30),
                api_key=llm_data.get("api_key"),
            ),
            audio=AudioConfig(
                enabled=audio_data.get("enabled", False),
                voice=audio_data.get("voice", "en-US-JennyNeural"),
            ),
            display=DisplayConfig(
                color_scheme=display_data.get("color_scheme", "dark"),
                narrator_color=display_data.get("narrator_color", "cyan"),
                npc_color=display_data.get("npc_color", "yellow"),
                system_color=display_data.get("system_color", "dim"),
            ),
            gameplay=GameplayConfig(
                auto_save=gameplay_data.get("auto_save", True),
                difficulty=gameplay_data.get("difficulty", "normal"),
                verbose_rolls=gameplay_data.get("verbose_rolls", True),
            ),
        )

    @classmethod
    def _apply_env_overrides(cls, config: "ReverieConfig") -> "ReverieConfig":
        """Apply environment variable overrides."""
        # LLM overrides
        if provider := os.environ.get("REVERIE_LLM_PROVIDER"):
            config.llm.provider = provider
        if model := os.environ.get("REVERIE_LLM_MODEL"):
            config.llm.model = model
        if endpoint := os.environ.get("REVERIE_LLM_ENDPOINT"):
            config.llm.endpoint = endpoint
        if api_key := os.environ.get("REVERIE_LLM_API_KEY"):
            config.llm.api_key = api_key
        if api_key := os.environ.get("OPENAI_API_KEY"):
            config.llm.api_key = api_key

        # Gameplay overrides
        if difficulty := os.environ.get("REVERIE_DIFFICULTY"):
            config.gameplay.difficulty = difficulty

        return config

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        config_path = path or get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "endpoint": self.llm.endpoint,
                "timeout": self.llm.timeout,
            },
            "audio": {
                "enabled": self.audio.enabled,
                "voice": self.audio.voice,
            },
            "display": {
                "color_scheme": self.display.color_scheme,
                "narrator_color": self.display.narrator_color,
                "npc_color": self.display.npc_color,
                "system_color": self.display.system_color,
            },
            "gameplay": {
                "auto_save": self.gameplay.auto_save,
                "difficulty": self.gameplay.difficulty,
                "verbose_rolls": self.gameplay.verbose_rolls,
            },
        }

        # Don't save api_key to file
        if self.llm.api_key:
            data["llm"]["api_key"] = "***hidden***"

        with open(config_path, "w") as f:
            toml.dump(data, f)


def load_config(path: Optional[Path] = None) -> ReverieConfig:
    """Load configuration (convenience function)."""
    return ReverieConfig.load(path)

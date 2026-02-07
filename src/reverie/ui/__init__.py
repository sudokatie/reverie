"""Terminal user interface components for Reverie."""

from .app import ReverieApp, create_app
from .screens import (
    MainScreen,
    CharacterScreen,
    InventoryScreen,
    QuestScreen,
    HelpScreen,
)
from .widgets import (
    format_narration,
    format_npc_dialogue,
    format_system,
    format_player_action,
    format_combat,
    format_damage,
    format_success,
    format_failure,
    NarrationPanel,
    StatusBar,
)

__all__ = [
    # App
    "ReverieApp",
    "create_app",
    # Screens
    "MainScreen",
    "CharacterScreen",
    "InventoryScreen",
    "QuestScreen",
    "HelpScreen",
    # Formatting
    "format_narration",
    "format_npc_dialogue",
    "format_system",
    "format_player_action",
    "format_combat",
    "format_damage",
    "format_success",
    "format_failure",
    # Widgets
    "NarrationPanel",
    "StatusBar",
]

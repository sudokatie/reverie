"""Custom widgets and formatting for Reverie TUI."""

from textual.widgets import Static, RichLog
from textual.widget import Widget
from rich.text import Text
from rich.style import Style
from rich.console import RenderableType
from typing import Optional


# =============================================================================
# Text Formatting Functions
# =============================================================================

def format_narration(text: str) -> Text:
    """Format narration text for display.
    
    Narration is the main game text describing scenes,
    actions, and outcomes.
    
    Args:
        text: Raw narration text
        
    Returns:
        Rich Text object with styling
    """
    styled = Text()
    
    # Handle bold markdown
    parts = text.split("**")
    for i, part in enumerate(parts):
        if i % 2 == 1:
            # Bold text
            styled.append(part, style="bold")
        else:
            styled.append(part, style="")
    
    return styled


def format_npc_dialogue(npc_name: str, text: str) -> Text:
    """Format NPC dialogue for display.
    
    NPC speech is shown with the NPC's name in color
    and the dialogue in quotes.
    
    Args:
        npc_name: Name of the NPC speaking
        text: The dialogue text
        
    Returns:
        Rich Text object with styling
    """
    styled = Text()
    styled.append(npc_name, style="bold cyan")
    styled.append(': "', style="dim")
    styled.append(text, style="italic")
    styled.append('"', style="dim")
    return styled


def format_system(text: str) -> Text:
    """Format system messages for display.
    
    System messages are meta-information like
    "Game saved" or "Level up!"
    
    Args:
        text: The system message
        
    Returns:
        Rich Text object with styling
    """
    styled = Text()
    styled.append(">>> ", style="bold yellow")
    styled.append(text, style="yellow")
    return styled


def format_player_action(text: str) -> Text:
    """Format player action echo for display.
    
    Shows what the player typed/did.
    
    Args:
        text: The player's action
        
    Returns:
        Rich Text object with styling
    """
    styled = Text()
    styled.append("> ", style="bold green")
    styled.append(text, style="green")
    return styled


def format_combat(text: str, is_player: bool = True) -> Text:
    """Format combat text for display.
    
    Args:
        text: The combat message
        is_player: True if this is the player's action
        
    Returns:
        Rich Text object with styling
    """
    styled = Text()
    if is_player:
        styled.append("⚔ ", style="bold")
        styled.append(text, style="bold white")
    else:
        styled.append("⚔ ", style="bold red")
        styled.append(text, style="red")
    return styled


def format_damage(text: str, is_critical: bool = False) -> Text:
    """Format damage messages.
    
    Args:
        text: The damage message
        is_critical: True if critical damage
        
    Returns:
        Rich Text object with styling
    """
    styled = Text()
    if is_critical:
        styled.append("!! ", style="bold red")
        styled.append(text, style="bold red")
    else:
        styled.append(text, style="red")
    return styled


def format_success(text: str) -> Text:
    """Format success messages.
    
    Args:
        text: The success message
        
    Returns:
        Rich Text object with styling
    """
    styled = Text()
    styled.append("✓ ", style="bold green")
    styled.append(text, style="green")
    return styled


def format_failure(text: str) -> Text:
    """Format failure messages.
    
    Args:
        text: The failure message
        
    Returns:
        Rich Text object with styling
    """
    styled = Text()
    styled.append("✗ ", style="bold red")
    styled.append(text, style="red")
    return styled


# =============================================================================
# Custom Widgets
# =============================================================================

class NarrationPanel(Static):
    """A scrollable panel for game narration."""
    
    DEFAULT_CSS = """
    NarrationPanel {
        height: 100%;
        overflow-y: auto;
        padding: 1;
    }
    """
    
    def __init__(self, **kwargs):
        """Initialize the narration panel."""
        super().__init__(**kwargs)
        self._entries: list[Text] = []
        self._max_entries: int = 100
    
    def add_narration(self, text: str) -> None:
        """Add narration text."""
        self._entries.append(format_narration(text))
        self._trim_and_update()
    
    def add_dialogue(self, npc_name: str, text: str) -> None:
        """Add NPC dialogue."""
        self._entries.append(format_npc_dialogue(npc_name, text))
        self._trim_and_update()
    
    def add_system(self, text: str) -> None:
        """Add a system message."""
        self._entries.append(format_system(text))
        self._trim_and_update()
    
    def add_player_action(self, text: str) -> None:
        """Add player action echo."""
        self._entries.append(format_player_action(text))
        self._trim_and_update()
    
    def clear(self) -> None:
        """Clear all entries."""
        self._entries.clear()
        self.update("")
    
    def _trim_and_update(self) -> None:
        """Trim old entries and update display."""
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        
        # Combine entries with newlines
        combined = Text()
        for i, entry in enumerate(self._entries):
            if i > 0:
                combined.append("\n\n")
            combined.append(entry)
        
        self.update(combined)


class StatusBar(Static):
    """A status bar showing game state."""
    
    DEFAULT_CSS = """
    StatusBar {
        height: 3;
        background: $surface;
        padding: 0 1;
    }
    """
    
    def __init__(self, **kwargs):
        """Initialize the status bar."""
        super().__init__(**kwargs)
        self._hp: int = 3
        self._max_hp: int = 3
        self._gold: int = 0
        self._level: int = 1
        self._location: str = "Unknown"
        self._in_combat: bool = False
    
    def update_status(
        self,
        hp: Optional[int] = None,
        gold: Optional[int] = None,
        level: Optional[int] = None,
        location: Optional[str] = None,
        in_combat: Optional[bool] = None,
    ) -> None:
        """Update status values.
        
        Args:
            hp: Current HP (danger level 0-3)
            gold: Current gold
            level: Character level
            location: Current location name
            in_combat: Whether in combat
        """
        if hp is not None:
            self._hp = hp
        if gold is not None:
            self._gold = gold
        if level is not None:
            self._level = level
        if location is not None:
            self._location = location
        if in_combat is not None:
            self._in_combat = in_combat
        
        self._render_status()
    
    def _render_status(self) -> None:
        """Render the status bar."""
        styled = Text()
        
        # HP as hearts
        hp_display = "❤" * self._hp + "♡" * (self._max_hp - self._hp)
        styled.append(f"HP: {hp_display}", style="red")
        styled.append(" | ")
        
        # Gold
        styled.append(f"Gold: {self._gold}", style="yellow")
        styled.append(" | ")
        
        # Level
        styled.append(f"Lvl: {self._level}", style="cyan")
        styled.append(" | ")
        
        # Location
        styled.append(f"@ {self._location}", style="green")
        
        # Combat indicator
        if self._in_combat:
            styled.append(" | ")
            styled.append("[COMBAT]", style="bold red")
        
        self.update(styled)

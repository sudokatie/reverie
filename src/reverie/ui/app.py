"""Main Textual application for Reverie."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, Static
from textual.containers import Container, Vertical, Horizontal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..game import Game


class ReverieApp(App):
    """The main Reverie TUI application."""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #main-container {
        height: 100%;
    }
    
    #narration-panel {
        height: 1fr;
        border: solid green;
        padding: 1;
        overflow-y: auto;
    }
    
    #status-bar {
        height: 3;
        background: $surface;
        padding: 0 1;
    }
    
    #input-container {
        height: 3;
        padding: 0 1;
    }
    
    .side-panel {
        width: 40;
        border: solid blue;
        padding: 1;
        display: none;
    }
    
    .side-panel.visible {
        display: block;
    }
    
    #help-panel {
        border: solid yellow;
    }
    
    #character-panel {
        border: solid cyan;
    }
    
    #inventory-panel {
        border: solid magenta;
    }
    
    #quest-panel {
        border: solid green;
    }
    """
    
    BINDINGS = [
        Binding("c", "toggle_character", "Character", show=True),
        Binding("i", "toggle_inventory", "Inventory", show=True),
        Binding("q", "toggle_quests", "Quests", show=True),
        Binding("?", "toggle_help", "Help", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]
    
    def __init__(self, game: Optional["Game"] = None, **kwargs):
        """Initialize the app.
        
        Args:
            game: The game instance to use
        """
        super().__init__(**kwargs)
        self.game = game
        self._narration_history: list[str] = []
    
    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header(show_clock=True)
        
        with Horizontal(id="main-container"):
            with Vertical(id="game-area"):
                yield Static("", id="narration-panel")
                yield Static("", id="status-bar")
                with Container(id="input-container"):
                    yield Input(placeholder="> What do you do?", id="player-input")
            
            # Side panels (hidden by default)
            yield Static("", id="character-panel", classes="side-panel")
            yield Static("", id="inventory-panel", classes="side-panel")
            yield Static("", id="quest-panel", classes="side-panel")
            yield Static("", id="help-panel", classes="side-panel")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.title = "REVERIE"
        self.sub_title = "An AI Dungeon Master"
        
        # Show initial narration
        if self.game:
            self._show_initial_state()
        else:
            self._add_narration("Welcome to Reverie. No game loaded.")
        
        # Update help panel
        help_panel = self.query_one("#help-panel", Static)
        help_panel.update(self._get_help_text())
        
        # Focus input
        self.query_one("#player-input", Input).focus()
    
    def _show_initial_state(self) -> None:
        """Show the initial game state."""
        if not self.game:
            return
        
        # Show location if available
        if self.game.state.location:
            from ..game import handle_command
            look_result = handle_command(self.game, "look")
            self._add_narration(look_result)
        else:
            self._add_narration("You find yourself... somewhere.")
        
        self._update_status_bar()
    
    def _add_narration(self, text: str) -> None:
        """Add text to the narration panel."""
        self._narration_history.append(text)
        
        # Keep last 50 entries
        if len(self._narration_history) > 50:
            self._narration_history = self._narration_history[-50:]
        
        # Update display
        panel = self.query_one("#narration-panel", Static)
        panel.update("\n\n".join(self._narration_history))
    
    def _update_status_bar(self) -> None:
        """Update the status bar with current state."""
        if not self.game:
            return
        
        char = self.game.state.character
        loc = self.game.state.location
        
        status_parts = [
            f"HP: {'*' * char.danger_level.value}{'.' * (3 - char.danger_level.value)}",
            f"Gold: {char.gold}",
            f"Level: {char.level}",
        ]
        
        if loc:
            status_parts.append(f"Location: {loc.name}")
        
        if self.game.state.in_combat:
            status_parts.append("[COMBAT]")
        
        status = " | ".join(status_parts)
        self.query_one("#status-bar", Static).update(status)
    
    def _update_character_panel(self) -> None:
        """Update the character panel."""
        if not self.game:
            return
        
        from ..game import handle_command
        stats_text = handle_command(self.game, "stats")
        self.query_one("#character-panel", Static).update(stats_text)
    
    def _update_inventory_panel(self) -> None:
        """Update the inventory panel."""
        if not self.game:
            return
        
        from ..game import handle_command
        inv_text = handle_command(self.game, "inventory")
        self.query_one("#inventory-panel", Static).update(inv_text)
    
    def _update_quest_panel(self) -> None:
        """Update the quest panel."""
        if not self.game:
            return
        
        from ..game import handle_command
        quest_text = handle_command(self.game, "quests")
        self.query_one("#quest-panel", Static).update(quest_text)
    
    def _get_help_text(self) -> str:
        """Get the help text."""
        return """HELP

COMMANDS:
  look      - Examine surroundings
  go <dir>  - Move (north, south, etc.)
  talk <n>  - Speak with NPC
  inventory - Check items
  stats     - View character
  quests    - View quests
  save      - Save game
  help      - Show this help
  quit      - Exit game

KEYS:
  C - Character sheet
  I - Inventory
  Q - Quest log
  ? - Help
  Ctrl+Q - Quit

Type actions naturally:
  "search the room"
  "pick up the sword"
  "attack the goblin"
"""
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle player input submission."""
        user_input = event.value.strip()
        event.input.value = ""
        
        if not user_input:
            return
        
        if not self.game:
            self._add_narration("No game loaded.")
            return
        
        # Handle quit command
        if user_input.lower() in ("quit", "/quit", "exit"):
            self.exit()
            return
        
        # Process input through game
        from ..game import process_input, check_triggers
        
        response = process_input(self.game, user_input)
        self._add_narration(response)
        
        # Check for triggers
        triggers = check_triggers(self.game)
        for trigger in triggers:
            self._add_narration(f">>> {trigger}")
        
        # Update UI
        self._update_status_bar()
        self._update_character_panel()
        self._update_inventory_panel()
        self._update_quest_panel()
    
    def action_toggle_character(self) -> None:
        """Toggle character panel visibility."""
        panel = self.query_one("#character-panel", Static)
        self._update_character_panel()
        panel.toggle_class("visible")
    
    def action_toggle_inventory(self) -> None:
        """Toggle inventory panel visibility."""
        panel = self.query_one("#inventory-panel", Static)
        self._update_inventory_panel()
        panel.toggle_class("visible")
    
    def action_toggle_quests(self) -> None:
        """Toggle quest panel visibility."""
        panel = self.query_one("#quest-panel", Static)
        self._update_quest_panel()
        panel.toggle_class("visible")
    
    def action_toggle_help(self) -> None:
        """Toggle help panel visibility."""
        panel = self.query_one("#help-panel", Static)
        panel.toggle_class("visible")


def create_app(game: Optional["Game"] = None) -> ReverieApp:
    """Create and return a configured ReverieApp instance.
    
    Args:
        game: The game instance to use
        
    Returns:
        Configured ReverieApp
    """
    return ReverieApp(game=game)

"""Screen definitions for Reverie TUI."""

from textual.screen import Screen
from textual.widgets import Static, Button, Input, Label
from textual.containers import Container, Vertical, Horizontal, Grid
from textual.app import ComposeResult
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..game import Game, GameState
    from ..character import Character


class MainScreen(Screen):
    """The main game screen with narration and input."""
    
    def __init__(self, game: Optional["Game"] = None, **kwargs):
        """Initialize the main screen.
        
        Args:
            game: The game instance
        """
        super().__init__(**kwargs)
        self.game = game
    
    def compose(self) -> ComposeResult:
        """Create the screen layout."""
        yield Static("Welcome to Reverie", id="narration")
        yield Static("", id="status")
        yield Input(placeholder="> What do you do?", id="input")


class CharacterScreen(Screen):
    """Character sheet screen."""
    
    CSS = """
    CharacterScreen {
        align: center middle;
    }
    
    #character-container {
        width: 60;
        height: auto;
        max-height: 80%;
        border: thick $primary;
        padding: 1 2;
    }
    
    .stat-row {
        height: 1;
    }
    
    .stat-label {
        width: 12;
    }
    
    .stat-value {
        width: 8;
    }
    """
    
    BINDINGS = [
        ("escape", "dismiss", "Back"),
        ("c", "dismiss", "Close"),
    ]
    
    def __init__(self, character: Optional["Character"] = None, **kwargs):
        """Initialize the character screen.
        
        Args:
            character: The character to display
        """
        super().__init__(**kwargs)
        self.character = character
    
    def compose(self) -> ComposeResult:
        """Create the screen layout."""
        with Vertical(id="character-container"):
            yield Label("CHARACTER SHEET", id="title")
            yield Static("")  # Spacer
            
            if self.character:
                yield Static(f"Name: {self.character.name}")
                yield Static(f"Race: {self.character.race}")
                yield Static(f"Class: {self.character.player_class.value}")
                yield Static(f"Level: {self.character.level}")
                yield Static("")
                yield Static("STATS")
                yield Static(f"  Might:  {self.character.stats.might}")
                yield Static(f"  Wit:    {self.character.stats.wit}")
                yield Static(f"  Spirit: {self.character.stats.spirit}")
                yield Static("")
                yield Static(f"Health: {self.character.danger_level.name}")
                yield Static(f"XP: {self.character.xp}/{self.character.level * 100}")
                yield Static(f"Gold: {self.character.gold}")
            else:
                yield Static("No character loaded")
            
            yield Static("")
            yield Button("Close", id="close-btn", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "close-btn":
            self.dismiss()


class InventoryScreen(Screen):
    """Inventory management screen."""
    
    CSS = """
    InventoryScreen {
        align: center middle;
    }
    
    #inventory-container {
        width: 60;
        height: auto;
        max-height: 80%;
        border: thick $primary;
        padding: 1 2;
    }
    
    .item-row {
        height: 1;
    }
    """
    
    BINDINGS = [
        ("escape", "dismiss", "Back"),
        ("i", "dismiss", "Close"),
    ]
    
    def __init__(self, character: Optional["Character"] = None, **kwargs):
        """Initialize the inventory screen.
        
        Args:
            character: The character whose inventory to display
        """
        super().__init__(**kwargs)
        self.character = character
    
    def compose(self) -> ComposeResult:
        """Create the screen layout."""
        with Vertical(id="inventory-container"):
            yield Label("INVENTORY", id="title")
            yield Static("")
            
            if self.character:
                # Equipment
                yield Static("EQUIPPED")
                eq = self.character.equipment
                yield Static(f"  Weapon:    {eq.weapon or '(none)'}")
                yield Static(f"  Armor:     {eq.armor or '(none)'}")
                yield Static(f"  Accessory: {eq.accessory or '(none)'}")
                yield Static("")
                
                # Items
                yield Static("ITEMS")
                if self.character.inventory:
                    for item in self.character.inventory:
                        yield Static(f"  - {item}")
                else:
                    yield Static("  (empty)")
                
                yield Static("")
                yield Static(f"Gold: {self.character.gold}")
            else:
                yield Static("No character loaded")
            
            yield Static("")
            yield Button("Close", id="close-btn", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "close-btn":
            self.dismiss()


class QuestScreen(Screen):
    """Quest log screen."""
    
    CSS = """
    QuestScreen {
        align: center middle;
    }
    
    #quest-container {
        width: 70;
        height: auto;
        max-height: 80%;
        border: thick $primary;
        padding: 1 2;
    }
    
    .quest-title {
        text-style: bold;
    }
    """
    
    BINDINGS = [
        ("escape", "dismiss", "Back"),
        ("q", "dismiss", "Close"),
    ]
    
    def __init__(self, state: Optional["GameState"] = None, **kwargs):
        """Initialize the quest screen.
        
        Args:
            state: The game state with quest info
        """
        super().__init__(**kwargs)
        self.state = state
    
    def compose(self) -> ComposeResult:
        """Create the screen layout."""
        with Vertical(id="quest-container"):
            yield Label("QUEST LOG", id="title")
            yield Static("")
            
            if self.state and self.state.active_quest:
                quest = self.state.active_quest
                yield Static(f"Active Quest: {quest.title}", classes="quest-title")
                yield Static("")
                yield Static(f"Objective: {quest.objective}")
                yield Static("")
                
                # Stages
                completed, total = quest.get_progress()
                yield Static(f"Progress: {completed}/{total} stages")
                
                for i, stage in enumerate(quest.stages):
                    marker = "[x]" if stage.completed else "[ ]"
                    yield Static(f"  {marker} {stage.description}")
                
                if quest.complications:
                    yield Static("")
                    yield Static("Complications:")
                    for comp in quest.complications:
                        yield Static(f"  - {comp}")
            else:
                yield Static("No active quests")
            
            yield Static("")
            yield Button("Close", id="close-btn", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "close-btn":
            self.dismiss()


class HelpScreen(Screen):
    """Help screen with commands and controls."""
    
    CSS = """
    HelpScreen {
        align: center middle;
    }
    
    #help-container {
        width: 60;
        height: auto;
        max-height: 80%;
        border: thick $primary;
        padding: 1 2;
    }
    """
    
    BINDINGS = [
        ("escape", "dismiss", "Back"),
        ("?", "dismiss", "Close"),
    ]
    
    def compose(self) -> ComposeResult:
        """Create the screen layout."""
        with Vertical(id="help-container"):
            yield Label("HELP", id="title")
            yield Static("")
            yield Static("COMMANDS")
            yield Static("  look      - Examine surroundings")
            yield Static("  go <dir>  - Move in direction")
            yield Static("  talk <n>  - Talk to NPC")
            yield Static("  inventory - Check items")
            yield Static("  stats     - View character")
            yield Static("  quests    - View quests")
            yield Static("  save      - Save game")
            yield Static("  help      - Show help")
            yield Static("  quit      - Exit game")
            yield Static("")
            yield Static("KEYBOARD SHORTCUTS")
            yield Static("  C      - Character sheet")
            yield Static("  I      - Inventory")
            yield Static("  Q      - Quest log")
            yield Static("  ?      - Help")
            yield Static("  Ctrl+Q - Quit")
            yield Static("")
            yield Static("ACTIONS")
            yield Static("  Type natural actions:")
            yield Static('  "search the room"')
            yield Static('  "pick up the sword"')
            yield Static('  "attack the goblin"')
            yield Static("")
            yield Button("Close", id="close-btn", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "close-btn":
            self.dismiss()

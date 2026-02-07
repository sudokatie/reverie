"""Tests for the Reverie UI components."""

import pytest
from rich.text import Text

from reverie.ui import (
    ReverieApp,
    create_app,
    MainScreen,
    CharacterScreen,
    InventoryScreen,
    QuestScreen,
    HelpScreen,
    format_narration,
    format_npc_dialogue,
    format_system,
    format_player_action,
    NarrationPanel,
    StatusBar,
)
from reverie.character import Character, Stats, Equipment, PlayerClass, DangerLevel
from reverie.game import GameState, Game, create_game_state
from reverie.storage.database import Database
from reverie.storage.models import Campaign


@pytest.fixture
def sample_campaign() -> Campaign:
    """Create a sample campaign."""
    return Campaign.create("Test Adventure")


@pytest.fixture
def sample_character() -> Character:
    """Create a sample character."""
    return Character(
        name="Thorn",
        race="Human",
        player_class=PlayerClass.CODE_WARRIOR,
        stats=Stats(might=5, wit=4, spirit=3),
        background="A warrior",
        equipment=Equipment(weapon="Sword", armor="Chainmail"),
        gold=100,
        level=2,
    )


@pytest.fixture
def test_db() -> Database:
    """Create in-memory test database."""
    return Database.open_memory()


@pytest.fixture
def sample_game(sample_campaign, sample_character, test_db) -> Game:
    """Create a sample game instance."""
    state = create_game_state(sample_campaign, sample_character)
    return Game(state=state, db=test_db, llm=None)


class TestCreateApp:
    """Tests for create_app function."""
    
    def test_create_app_without_game(self):
        """Test creating app without a game."""
        app = create_app()
        assert isinstance(app, ReverieApp)
        assert app.game is None
    
    def test_create_app_with_game(self, sample_game):
        """Test creating app with a game."""
        app = create_app(sample_game)
        assert isinstance(app, ReverieApp)
        assert app.game == sample_game


class TestReverieApp:
    """Tests for ReverieApp class."""
    
    def test_app_has_bindings(self):
        """Test that app has expected key bindings."""
        app = create_app()
        binding_keys = [b.key for b in app.BINDINGS]
        
        assert "c" in binding_keys  # Character
        assert "i" in binding_keys  # Inventory
        assert "q" in binding_keys  # Quests
        assert "?" in binding_keys  # Help


class TestScreens:
    """Tests for screen classes."""
    
    def test_character_screen_with_character(self, sample_character):
        """Test character screen with a character."""
        screen = CharacterScreen(character=sample_character)
        assert screen.character == sample_character
    
    def test_inventory_screen_with_character(self, sample_character):
        """Test inventory screen with a character."""
        screen = InventoryScreen(character=sample_character)
        assert screen.character == sample_character
    
    def test_quest_screen_without_state(self):
        """Test quest screen without state."""
        screen = QuestScreen(state=None)
        assert screen.state is None
    
    def test_help_screen_creation(self):
        """Test help screen can be created."""
        screen = HelpScreen()
        assert screen is not None


class TestFormatNarration:
    """Tests for format_narration function."""
    
    def test_plain_text(self):
        """Test formatting plain text."""
        result = format_narration("You enter the room.")
        assert isinstance(result, Text)
        assert "You enter the room." in result.plain
    
    def test_bold_text(self):
        """Test formatting text with bold markers."""
        result = format_narration("The **dragon** roars.")
        assert "dragon" in result.plain
        # Bold markers should be removed
        assert "**" not in result.plain


class TestFormatNpcDialogue:
    """Tests for format_npc_dialogue function."""
    
    def test_dialogue_format(self):
        """Test NPC dialogue formatting."""
        result = format_npc_dialogue("Mayor Syntax", "Hello there!")
        assert isinstance(result, Text)
        assert "Mayor Syntax" in result.plain
        assert "Hello there!" in result.plain


class TestFormatSystem:
    """Tests for format_system function."""
    
    def test_system_message(self):
        """Test system message formatting."""
        result = format_system("Game saved.")
        assert isinstance(result, Text)
        assert "Game saved." in result.plain
        assert ">>>" in result.plain


class TestFormatPlayerAction:
    """Tests for format_player_action function."""
    
    def test_player_action(self):
        """Test player action formatting."""
        result = format_player_action("search the room")
        assert isinstance(result, Text)
        assert "search the room" in result.plain
        assert ">" in result.plain


class TestNarrationPanel:
    """Tests for NarrationPanel widget."""
    
    def test_panel_creation(self):
        """Test narration panel can be created."""
        panel = NarrationPanel()
        assert panel is not None
        assert panel._entries == []
    
    def test_add_entry_directly(self):
        """Test adding entries directly to internal list."""
        panel = NarrationPanel()
        # Add directly to test list behavior without triggering update()
        panel._entries.append(format_narration("You see a door."))
        assert len(panel._entries) == 1
    
    def test_max_entries_limit(self):
        """Test that max entries is set."""
        panel = NarrationPanel()
        assert panel._max_entries == 100


class TestStatusBar:
    """Tests for StatusBar widget."""
    
    def test_status_bar_creation(self):
        """Test status bar can be created."""
        bar = StatusBar()
        assert bar is not None
    
    def test_status_bar_defaults(self):
        """Test status bar default values."""
        bar = StatusBar()
        assert bar._hp == 3
        assert bar._gold == 0
        assert bar._level == 1
        assert bar._location == "Unknown"
        assert bar._in_combat is False
    
    def test_status_bar_internal_state(self):
        """Test updating internal state without render."""
        bar = StatusBar()
        # Update internal state directly to test without app context
        bar._hp = 2
        bar._gold = 50
        bar._level = 3
        bar._location = "Tavern"
        bar._in_combat = True
        
        assert bar._hp == 2
        assert bar._gold == 50
        assert bar._level == 3
        assert bar._location == "Tavern"
        assert bar._in_combat is True

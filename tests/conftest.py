"""Shared fixtures for Reverie tests."""

import pytest
from pathlib import Path
from uuid import uuid4

from reverie.character import Character, Stats, Equipment, PlayerClass, DangerLevel
from reverie.world import Location, Region, ElementType
from reverie.npc import NPC, NPCMemory, Disposition
from reverie.quest import Quest, QuestStage, QuestReward, QuestStatus
from reverie.combat import Enemy, CombatState
from reverie.combat import DangerLevel as CombatDangerLevel
from reverie.storage.database import Database
from reverie.storage.models import Campaign
from reverie.game import Game, GameState, create_game_state
from reverie.llm.client import LLMClient


# =============================================================================
# Mock LLM Client
# =============================================================================

class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""
    
    def __init__(self, responses: dict[str, str] | None = None):
        """Initialize with optional canned responses."""
        self.responses = responses or {}
        self.calls: list[str] = []
    
    def generate(self, prompt: str, context: dict | None = None):
        """Return a canned or default response."""
        from reverie.llm.client import LLMResponse
        
        self.calls.append(prompt)
        
        # Check for matching response
        for key, response in self.responses.items():
            if key.lower() in prompt.lower():
                return LLMResponse(text=response)
        
        # Default responses based on prompt type
        if "scene" in prompt.lower() or "describe" in prompt.lower():
            return LLMResponse(text="You find yourself in a mysterious place. The air is thick with anticipation.")
        elif "dialogue" in prompt.lower() or "npc" in prompt.lower():
            return LLMResponse(text="Greetings, traveler. What brings you to these parts?")
        elif "combat" in prompt.lower() or "attack" in prompt.lower():
            return LLMResponse(text="Your strike lands true, dealing a solid blow.")
        elif "quest" in prompt.lower():
            return LLMResponse(text="A new adventure awaits. Will you accept the challenge?")
        else:
            return LLMResponse(text="The winds of fate are ever-changing...")
    
    def is_available(self) -> bool:
        """Always available for testing."""
        return True
    
    @property
    def model_name(self) -> str:
        """Return mock model name."""
        return "mock-model"


@pytest.fixture
def mock_llm() -> MockLLMClient:
    """Create a mock LLM client."""
    return MockLLMClient()


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture
def test_database() -> Database:
    """Create an in-memory test database."""
    return Database.open_memory()


@pytest.fixture
def test_db_path(tmp_path) -> Path:
    """Create a temporary database path."""
    return tmp_path / "test_reverie.db"


@pytest.fixture
def persistent_database(test_db_path) -> Database:
    """Create a file-based test database."""
    return Database.open(test_db_path)


# =============================================================================
# Character Fixtures
# =============================================================================

@pytest.fixture
def sample_character() -> Character:
    """Create a sample player character."""
    return Character(
        name="Thorn",
        race="Human",
        player_class=PlayerClass.CODE_WARRIOR,
        stats=Stats(might=5, wit=4, spirit=3),
        background="A warrior who debugged the ancient mainframe.",
        equipment=Equipment(
            weapon="Keyboard Blade",
            armor="Hoodie of Protection",
            accessory="USB Amulet",
        ),
        inventory=["Health Potion", "Magic Scroll"],
        gold=100,
        level=2,
        xp=150,
    )


@pytest.fixture
def wounded_character() -> Character:
    """Create a wounded character."""
    char = Character(
        name="Injured",
        race="Elf",
        player_class=PlayerClass.MEETING_SURVIVOR,
        stats=Stats(might=3, wit=5, spirit=4),
        danger_level=DangerLevel.CRITICAL,
    )
    return char


# =============================================================================
# World Fixtures
# =============================================================================

@pytest.fixture
def sample_location() -> Location:
    """Create a sample location."""
    return Location(
        id=str(uuid4()),
        element_type=ElementType.SETTLEMENT,
        name="Village of Debugton",
        description="A quiet village where bugs come to be fixed.",
        tags=["settlement", "peaceful", "tech"],
        secrets=["Hidden basement with server room"],
        exits={"north": "forest-001", "east": "mountains-001"},
    )


@pytest.fixture
def sample_region() -> Region:
    """Create a sample region."""
    return Region(
        id=str(uuid4()),
        element_type=ElementType.REGION,
        name="The Silicon Wastes",
        description="A vast expanse of abandoned technology.",
        tags=["wasteland", "tech", "dangerous"],
        climate="arid",
        terrain="desert",
        culture="nomadic scavengers",
    )


@pytest.fixture
def connected_locations() -> tuple[Location, Location, Location]:
    """Create connected locations for exploration tests."""
    village = Location(
        id="village-001",
        element_type=ElementType.SETTLEMENT,
        name="Starting Village",
        description="A peaceful village.",
        exits={"north": "forest-001"},
    )
    
    forest = Location(
        id="forest-001",
        element_type=ElementType.WILDERNESS,
        name="Dark Forest",
        description="A mysterious forest.",
        exits={"south": "village-001", "east": "dungeon-001"},
    )
    
    dungeon = Location(
        id="dungeon-001",
        element_type=ElementType.DUNGEON,
        name="Ancient Ruins",
        description="Crumbling ruins filled with danger.",
        exits={"west": "forest-001"},
    )
    
    return village, forest, dungeon


# =============================================================================
# NPC Fixtures
# =============================================================================

@pytest.fixture
def sample_npc() -> NPC:
    """Create a sample NPC."""
    return NPC(
        id=str(uuid4()),
        name="Mayor Syntax",
        race="Elf",
        occupation="Mayor",
        traits=["wise", "patient"],
        motivation="Keep the village safe from runtime errors",
        secret="Once caused a stack overflow that destroyed a city",
        disposition=Disposition.FRIENDLY,
        memory=NPCMemory(),
    )


@pytest.fixture
def hostile_npc() -> NPC:
    """Create a hostile NPC."""
    return NPC(
        id=str(uuid4()),
        name="Bugmaster",
        race="Goblin",
        occupation="Bug Breeder",
        traits=["cunning", "aggressive"],
        motivation="Spread bugs throughout the land",
        disposition=Disposition.HOSTILE,
    )


# =============================================================================
# Quest Fixtures
# =============================================================================

@pytest.fixture
def sample_quest() -> Quest:
    """Create a sample quest."""
    return Quest(
        id=str(uuid4()),
        title="The Bug Hunt",
        hook="Mayor Syntax reports bugs infesting the forest.",
        objective="Find and eliminate 5 bugs in the northern forest.",
        complications=["The forest is dark", "Bugs multiply at night"],
        resolutions=["Return to the Mayor with proof"],
        rewards=QuestReward(gold=100, reputation=10, items=["Bug Spray"]),
        stages=[
            QuestStage("Enter the forest"),
            QuestStage("Find the bug nest"),
            QuestStage("Defeat the bugs"),
            QuestStage("Return to Mayor Syntax"),
        ],
    )


# =============================================================================
# Combat Fixtures
# =============================================================================

@pytest.fixture
def sample_enemy() -> Enemy:
    """Create a sample enemy."""
    return Enemy(
        id=str(uuid4()),
        name="Goblin Scout",
        danger_level=CombatDangerLevel.FRESH,
        damage=1,
        special="Can call for reinforcements",
    )


@pytest.fixture
def sample_combat_state(sample_enemy) -> CombatState:
    """Create a sample combat state."""
    return CombatState(
        enemies=[sample_enemy],
        player_danger=CombatDangerLevel.FRESH,
    )


# =============================================================================
# Campaign Fixtures
# =============================================================================

@pytest.fixture
def sample_campaign() -> Campaign:
    """Create a sample campaign."""
    return Campaign.create("Test Adventure")


# =============================================================================
# Game Fixtures
# =============================================================================

@pytest.fixture
def sample_game_state(sample_campaign, sample_character, sample_location) -> GameState:
    """Create a sample game state."""
    return create_game_state(sample_campaign, sample_character, sample_location)


@pytest.fixture
def sample_game(sample_game_state, test_database, mock_llm) -> Game:
    """Create a fully configured game instance."""
    return Game(
        state=sample_game_state,
        db=test_database,
        llm=mock_llm,
    )


@pytest.fixture
def game_with_npcs(sample_game, sample_npc) -> Game:
    """Create a game with NPCs present."""
    sample_game.state.npcs_present = [sample_npc]
    return sample_game


@pytest.fixture
def game_with_quest(sample_game, sample_quest) -> Game:
    """Create a game with an active quest."""
    sample_game.state.active_quest = sample_quest
    return sample_game


@pytest.fixture
def game_in_combat(sample_game, sample_combat_state) -> Game:
    """Create a game in combat state."""
    sample_game.state.combat_state = sample_combat_state
    return sample_game

"""Tests for game state management."""

import pytest
from datetime import datetime
from uuid import uuid4

from reverie.game import (
    GameState,
    HistoryEntry,
    EventType,
    Game,
    CommandType,
    create_game_state,
    add_to_history,
    get_context,
    save_state,
    load_state,
    process_input,
    handle_command,
    handle_action,
    handle_dialogue,
    handle_combat_action,
    check_triggers,
    _serialize_character,
    _deserialize_character,
)
from reverie.character import Character, Stats, Equipment, PlayerClass, DangerLevel
from reverie.world import Location, ElementType
from reverie.npc import NPC, NPCMemory, Disposition
from reverie.quest import Quest, QuestStage, QuestReward, QuestStatus
from reverie.combat import CombatState, Enemy, CombatStatus
from reverie.combat import DangerLevel as CombatDangerLevel
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
        background="A warrior who once debugged the ancient mainframe.",
        equipment=Equipment(weapon="Keyboard Blade", armor="Hoodie of Protection"),
        gold=100,
        level=2,
        xp=150,
    )


@pytest.fixture
def sample_location() -> Location:
    """Create a sample location."""
    return Location(
        id=str(uuid4()),
        element_type=ElementType.SETTLEMENT,
        name="Village of Debugton",
        description="A quiet village where bugs come to be fixed.",
        tags=["settlement", "peaceful", "tech"],
        exits={"north": "forest", "east": "mountains"},
    )


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
        disposition=Disposition.FRIENDLY,
    )


@pytest.fixture
def sample_quest() -> Quest:
    """Create a sample quest."""
    return Quest(
        id=str(uuid4()),
        title="The Bug Hunt",
        hook="Mayor Syntax says bugs are infesting the forest.",
        objective="Find and eliminate 5 bugs in the northern forest.",
        complications=["The forest is dark", "Bugs multiply at night"],
        resolutions=["Return to the Mayor"],
        rewards=QuestReward(gold=100, reputation=10),
        stages=[
            QuestStage("Enter the forest"),
            QuestStage("Find the bug nest"),
            QuestStage("Defeat the bugs"),
        ],
    )


@pytest.fixture
def test_db() -> Database:
    """Create in-memory test database."""
    return Database.open_memory()


class TestHistoryEntry:
    """Tests for HistoryEntry."""
    
    def test_create_entry(self):
        """Test creating a history entry."""
        entry = HistoryEntry.create(
            EventType.NARRATION,
            "You enter the village.",
            {"location_id": "abc123"},
        )
        
        assert entry.event_type == EventType.NARRATION
        assert entry.description == "You enter the village."
        assert entry.data == {"location_id": "abc123"}
        assert entry.id is not None
        assert entry.timestamp is not None
    
    def test_entry_serialization(self):
        """Test history entry serialization roundtrip."""
        entry = HistoryEntry.create(
            EventType.COMBAT_START,
            "A wild bug appears!",
            {"enemy_count": 3},
        )
        
        data = entry.to_dict()
        restored = HistoryEntry.from_dict(data)
        
        assert restored.id == entry.id
        assert restored.event_type == entry.event_type
        assert restored.description == entry.description
        assert restored.data == entry.data


class TestGameState:
    """Tests for GameState class."""
    
    def test_in_combat_property(self, sample_campaign, sample_character):
        """Test in_combat property."""
        state = GameState(
            campaign=sample_campaign,
            character=sample_character,
        )
        
        assert not state.in_combat
        
        # Add active combat
        state.combat_state = CombatState(
            enemies=[Enemy(id="1", name="Bug")],
        )
        
        assert state.in_combat
    
    def test_has_active_quest_property(self, sample_campaign, sample_character, sample_quest):
        """Test has_active_quest property."""
        state = GameState(
            campaign=sample_campaign,
            character=sample_character,
        )
        
        assert not state.has_active_quest
        
        state.active_quest = sample_quest
        assert state.has_active_quest
        
        # Complete the quest
        sample_quest.status = QuestStatus.COMPLETED
        assert not state.has_active_quest
    
    def test_get_recent_history(self, sample_campaign, sample_character):
        """Test getting recent history."""
        state = GameState(
            campaign=sample_campaign,
            character=sample_character,
        )
        
        # Add some history
        for i in range(15):
            add_to_history(state, EventType.NARRATION, f"Event {i}")
        
        recent = state.get_recent_history(5)
        assert len(recent) == 5
        assert recent[0].description == "Event 10"
        assert recent[-1].description == "Event 14"
    
    def test_get_history_by_type(self, sample_campaign, sample_character):
        """Test filtering history by type."""
        state = GameState(
            campaign=sample_campaign,
            character=sample_character,
        )
        
        add_to_history(state, EventType.NARRATION, "Narration 1")
        add_to_history(state, EventType.COMBAT_START, "Combat begins")
        add_to_history(state, EventType.NARRATION, "Narration 2")
        add_to_history(state, EventType.COMBAT_END, "Combat ends")
        
        narrations = state.get_history_by_type(EventType.NARRATION)
        assert len(narrations) == 2


class TestCreateGameState:
    """Tests for create_game_state function."""
    
    def test_create_basic_state(self, sample_campaign, sample_character):
        """Test creating a basic game state."""
        state = create_game_state(sample_campaign, sample_character)
        
        assert state.campaign == sample_campaign
        assert state.character == sample_character
        assert state.location is None
        assert state.npcs_present == []
        assert state.active_quest is None
        assert state.combat_state is None
        assert len(state.history) == 1  # Initial entry
    
    def test_create_state_with_location(self, sample_campaign, sample_character, sample_location):
        """Test creating state with starting location."""
        state = create_game_state(sample_campaign, sample_character, sample_location)
        
        assert state.location == sample_location
        assert sample_location.id in state.discovered_locations


class TestAddToHistory:
    """Tests for add_to_history function."""
    
    def test_add_simple_event(self, sample_campaign, sample_character):
        """Test adding a simple event."""
        state = create_game_state(sample_campaign, sample_character)
        initial_count = len(state.history)
        
        entry = add_to_history(
            state,
            EventType.PLAYER_ACTION,
            "You pick up the sword.",
        )
        
        assert len(state.history) == initial_count + 1
        assert entry.event_type == EventType.PLAYER_ACTION
        assert entry.description == "You pick up the sword."
    
    def test_add_event_with_data(self, sample_campaign, sample_character):
        """Test adding event with additional data."""
        state = create_game_state(sample_campaign, sample_character)
        
        entry = add_to_history(
            state,
            EventType.ITEM_ACQUIRED,
            "You found a golden key!",
            {"item_name": "Golden Key", "item_value": 50},
        )
        
        assert entry.data["item_name"] == "Golden Key"
        assert entry.data["item_value"] == 50


class TestGetContext:
    """Tests for get_context function."""
    
    def test_basic_context(self, sample_campaign, sample_character):
        """Test getting basic context."""
        state = create_game_state(sample_campaign, sample_character)
        context = get_context(state)
        
        assert context["campaign_name"] == sample_campaign.name
        assert context["character"]["name"] == "Thorn"
        assert context["character"]["class"] == "Code Warrior"
        assert context["in_combat"] is False
    
    def test_context_with_location(self, sample_campaign, sample_character, sample_location):
        """Test context includes location."""
        state = create_game_state(sample_campaign, sample_character, sample_location)
        context = get_context(state)
        
        assert context["location"] is not None
        assert context["location"]["name"] == "Village of Debugton"
        assert "north" in context["location"]["exits"]
    
    def test_context_with_npcs(self, sample_campaign, sample_character, sample_location, sample_npc):
        """Test context includes NPCs."""
        state = create_game_state(sample_campaign, sample_character, sample_location)
        state.npcs_present = [sample_npc]
        
        context = get_context(state)
        
        assert len(context["npcs_present"]) == 1
        assert context["npcs_present"][0]["name"] == "Mayor Syntax"
    
    def test_context_with_quest(self, sample_campaign, sample_character, sample_quest):
        """Test context includes active quest."""
        state = create_game_state(sample_campaign, sample_character)
        state.active_quest = sample_quest
        
        context = get_context(state)
        
        assert context["active_quest"] is not None
        assert context["active_quest"]["title"] == "The Bug Hunt"
        assert context["active_quest"]["current_stage"]["description"] == "Enter the forest"
    
    def test_context_history_limit(self, sample_campaign, sample_character):
        """Test history limit in context."""
        state = create_game_state(sample_campaign, sample_character)
        
        for i in range(10):
            add_to_history(state, EventType.NARRATION, f"Event {i}")
        
        context = get_context(state, history_limit=3)
        
        assert len(context["recent_history"]) == 3


class TestSaveAndLoadState:
    """Tests for save_state and load_state functions."""
    
    def test_save_and_load_basic_state(self, sample_campaign, sample_character, test_db):
        """Test saving and loading basic state."""
        state = create_game_state(sample_campaign, sample_character)
        add_to_history(state, EventType.NARRATION, "Test event")
        
        save_state(state, test_db)
        loaded = load_state(test_db, sample_campaign.id)
        
        assert loaded is not None
        assert loaded.campaign.name == sample_campaign.name
        assert loaded.character.name == sample_character.name
    
    def test_save_and_load_with_location(
        self, sample_campaign, sample_character, sample_location, test_db
    ):
        """Test saving and loading state with location."""
        state = create_game_state(sample_campaign, sample_character, sample_location)
        
        save_state(state, test_db)
        loaded = load_state(test_db, sample_campaign.id)
        
        assert loaded.location is not None
        assert loaded.location.name == sample_location.name
    
    def test_save_and_load_history(self, sample_campaign, sample_character, test_db):
        """Test history persistence."""
        state = create_game_state(sample_campaign, sample_character)
        
        add_to_history(state, EventType.PLAYER_ACTION, "Action 1")
        add_to_history(state, EventType.NPC_DIALOGUE, "NPC says hello")
        add_to_history(state, EventType.COMBAT_START, "Combat begins")
        
        save_state(state, test_db)
        loaded = load_state(test_db, sample_campaign.id)
        
        # Should have 4 entries (1 initial + 3 added)
        assert len(loaded.history) == 4
    
    def test_load_nonexistent_campaign(self, test_db):
        """Test loading a campaign that doesn't exist."""
        result = load_state(test_db, "nonexistent-id")
        assert result is None


class TestCharacterSerialization:
    """Tests for character serialization helpers."""
    
    def test_character_roundtrip(self, sample_character):
        """Test character serialize/deserialize roundtrip."""
        data = _serialize_character(sample_character)
        restored = _deserialize_character(data)
        
        assert restored.name == sample_character.name
        assert restored.race == sample_character.race
        assert restored.player_class == sample_character.player_class
        assert restored.stats.might == sample_character.stats.might
        assert restored.stats.wit == sample_character.stats.wit
        assert restored.stats.spirit == sample_character.stats.spirit
        assert restored.level == sample_character.level
        assert restored.gold == sample_character.gold
        assert restored.equipment.weapon == sample_character.equipment.weapon


# =============================================================================
# Game Loop Tests (Task 12)
# =============================================================================

@pytest.fixture
def sample_game(sample_campaign, sample_character, sample_location, test_db) -> Game:
    """Create a sample game instance."""
    state = create_game_state(sample_campaign, sample_character, sample_location)
    return Game(state=state, db=test_db, llm=None)


class TestProcessInput:
    """Tests for process_input function."""
    
    def test_empty_input(self, sample_game):
        """Test handling empty input."""
        result = process_input(sample_game, "")
        assert "what would you like to do" in result.lower()
    
    def test_command_with_slash(self, sample_game):
        """Test command with slash prefix."""
        result = process_input(sample_game, "/look")
        assert sample_game.state.location.name in result
    
    def test_command_keyword(self, sample_game):
        """Test command as keyword."""
        result = process_input(sample_game, "inventory")
        assert "inventory" in result.lower()
    
    def test_movement_direction(self, sample_game):
        """Test movement by direction name."""
        result = process_input(sample_game, "north")
        # Either moves or says can't go
        assert "north" in result.lower() or "can't go" in result.lower()


class TestHandleCommand:
    """Tests for handle_command function."""
    
    def test_look_command(self, sample_game):
        """Test look command."""
        result = handle_command(sample_game, "look")
        assert sample_game.state.location.name in result
    
    def test_inventory_command(self, sample_game):
        """Test inventory command."""
        result = handle_command(sample_game, "inventory")
        assert "inventory" in result.lower()
        assert "gold" in result.lower()
    
    def test_stats_command(self, sample_game):
        """Test stats command."""
        result = handle_command(sample_game, "stats")
        assert sample_game.state.character.name in result
        assert "might" in result.lower()
    
    def test_help_command(self, sample_game):
        """Test help command."""
        result = handle_command(sample_game, "help")
        assert "commands" in result.lower()
    
    def test_unknown_command(self, sample_game):
        """Test unknown command."""
        result = handle_command(sample_game, "xyzzy")
        assert "unknown command" in result.lower()


class TestHandleAction:
    """Tests for handle_action function."""
    
    def test_action_adds_to_history(self, sample_game):
        """Test that actions are logged to history."""
        initial_count = len(sample_game.state.history)
        handle_action(sample_game, "search the room")
        
        assert len(sample_game.state.history) > initial_count
    
    def test_action_without_llm(self, sample_game):
        """Test action handling without LLM."""
        result = handle_action(sample_game, "pick up the sword")
        assert "pick up the sword" in result.lower()


class TestHandleDialogue:
    """Tests for handle_dialogue function."""
    
    def test_dialogue_logs_to_history(self, sample_game, sample_npc):
        """Test that dialogue is logged."""
        initial_count = len(sample_game.state.history)
        handle_dialogue(sample_game, sample_npc, "Hello there!")
        
        assert len(sample_game.state.history) > initial_count
    
    def test_dialogue_returns_response(self, sample_game, sample_npc):
        """Test that dialogue returns NPC response."""
        result = handle_dialogue(sample_game, sample_npc, "What's your name?")
        assert sample_npc.name in result


class TestHandleCombatAction:
    """Tests for handle_combat_action function."""
    
    def test_combat_action_not_in_combat(self, sample_game):
        """Test combat action when not in combat."""
        result = handle_combat_action(sample_game, "attack")
        assert "not in combat" in result.lower()
    
    def test_combat_attack(self, sample_game):
        """Test attack action in combat."""
        # Set up combat
        enemy = Enemy(id="1", name="Goblin")
        sample_game.state.combat_state = CombatState(enemies=[enemy])
        
        result = handle_combat_action(sample_game, "attack")
        assert "goblin" in result.lower()


class TestCheckTriggers:
    """Tests for check_triggers function."""
    
    def test_no_triggers(self, sample_game):
        """Test when no triggers fire."""
        triggers = check_triggers(sample_game)
        # May or may not have triggers
        assert isinstance(triggers, list)
    
    def test_level_up_trigger(self, sample_game):
        """Test level up trigger."""
        # Give enough XP to level up
        sample_game.state.character.xp = 200  # Level 1 needs 100
        sample_game.state.character.level = 1
        
        triggers = check_triggers(sample_game)
        
        assert any("level up" in t.lower() for t in triggers)
        assert sample_game.state.character.level == 2


class TestRollCommand:
    """Tests for roll command."""
    
    def test_roll_no_stat(self, sample_game):
        """Test rolling without a stat."""
        result = handle_command(sample_game, "roll")
        assert "roll" in result.lower() or "**" in result
    
    def test_roll_with_might(self, sample_game):
        """Test rolling with might stat."""
        result = handle_command(sample_game, "roll might")
        assert "might" in result.lower()
    
    def test_roll_with_wit(self, sample_game):
        """Test rolling with wit stat."""
        result = handle_command(sample_game, "roll wit")
        assert "wit" in result.lower()
    
    def test_roll_with_spirit(self, sample_game):
        """Test rolling with spirit stat."""
        result = handle_command(sample_game, "roll spirit")
        assert "spirit" in result.lower()
    
    def test_roll_invalid_stat(self, sample_game):
        """Test rolling with invalid stat."""
        result = handle_command(sample_game, "roll charisma")
        assert "unknown stat" in result.lower()


class TestMapCommand:
    """Tests for map command."""
    
    def test_map_no_locations(self, sample_game):
        """Test map when no locations discovered."""
        sample_game.state.discovered_locations = []
        result = handle_command(sample_game, "map")
        assert "haven't discovered" in result.lower()
    
    def test_map_with_locations(self, sample_game, sample_location):
        """Test map with discovered locations."""
        sample_game.state.location = sample_location
        sample_game.state.discovered_locations = [sample_location.id]
        result = handle_command(sample_game, "map")
        assert "discovered" in result.lower() or "locations" in result.lower()


class TestNpcsCommand:
    """Tests for npcs command."""
    
    def test_npcs_none_known(self, sample_game):
        """Test npcs when none are known."""
        sample_game.state.known_npcs = []
        result = handle_command(sample_game, "npcs")
        assert "haven't met" in result.lower()
    
    def test_npcs_with_known(self, sample_game, sample_npc):
        """Test npcs with known NPCs."""
        sample_game.state.known_npcs = [sample_npc.id]
        sample_game.state.npcs_present = [sample_npc]
        result = handle_command(sample_game, "npcs")
        # Either shows NPCs or says how many
        assert "npc" in result.lower() or "known" in result.lower()

"""Tests for world state integration with game loop."""

import pytest
from datetime import datetime
from uuid import uuid4

from reverie.game import (
    Game,
    GameState,
    add_world_history_context,
    handle_combat_action,
)
from reverie.storage.models import Campaign
from reverie.storage.database import Database
from reverie.storage.world_state import WorldStateDB, FactionStanding, NPCDeath, WorldEvent
from reverie.character import Character, Stats, Equipment, PlayerClass
from reverie.world import Location, ElementType
from reverie.combat import CombatState, Enemy, CombatStatus, DangerLevel as CombatDangerLevel


@pytest.fixture
def world_db():
    """Create in-memory world state database."""
    db = WorldStateDB.open_memory()
    yield db
    db.close()


@pytest.fixture
def campaign_db():
    """Create in-memory campaign database."""
    db = Database.open_memory()
    yield db
    db.close()


@pytest.fixture
def character():
    """Create test character."""
    return Character(
        name="Test Hero",
        race="human",
        player_class=PlayerClass.CODE_WARRIOR,
        stats=Stats(might=4, wit=4, spirit=4),
        equipment=Equipment(weapon="Sword", armor="Leather"),
    )


@pytest.fixture
def game_state(character):
    """Create test game state."""
    campaign = Campaign.create("Test Campaign")
    return GameState(
        campaign=campaign,
        character=character,
        location=Location(
            id=str(uuid4()),
            element_type=ElementType.SETTLEMENT,
            name="Test Town",
            description="A quiet town",
        ),
    )


class TestAddWorldHistoryContext:
    """Tests for world history context enrichment."""
    
    def test_no_world_state(self):
        """Returns None for world_history when no world state."""
        context = {}
        result = add_world_history_context(context, None)
        assert result["world_history"] is None
    
    def test_empty_world_state(self, world_db):
        """Returns empty summary for new world."""
        context = {}
        result = add_world_history_context(context, world_db)
        assert result["world_history"]["summary"] == "No recorded world history."
        assert result["world_history"]["dead_npcs"] == []
        assert result["world_history"]["factions"] == {}
    
    def test_includes_dead_npcs(self, world_db):
        """Dead NPCs appear in context."""
        world_db.record_npc_death(NPCDeath.create(
            "Evil Baron", "Castle", "Defeated by hero", "c1"
        ))
        
        context = {}
        result = add_world_history_context(context, world_db)
        assert "Evil Baron" in result["world_history"]["dead_npcs"]
        assert "Evil Baron" in result["world_history"]["summary"]
    
    def test_includes_factions(self, world_db):
        """Faction standings appear in context."""
        world_db.set_faction_standing(FactionStanding(
            "guild", "Merchants Guild", 50
        ))
        
        context = {}
        result = add_world_history_context(context, world_db)
        assert "guild" in result["world_history"]["factions"]
        assert result["world_history"]["factions"]["guild"]["standing"] == 50
    
    def test_includes_events(self, world_db):
        """World events appear in summary."""
        world_db.record_world_event(WorldEvent.create(
            "war", "The Great War", "Kingdoms went to war", "c1"
        ))
        
        context = {}
        result = add_world_history_context(context, world_db)
        assert "The Great War" in result["world_history"]["summary"]


class TestCombatNPCDeathRecording:
    """Tests for recording NPC deaths after combat."""
    
    def test_records_deaths_on_victory(self, game_state, campaign_db, world_db):
        """Defeated enemies are recorded to world state."""
        # Set up game with combat state
        game = Game(state=game_state, db=campaign_db, world_state=world_db)
        
        # Create combat with a defeated enemy
        enemy = Enemy(
            id=str(uuid4()),
            name="Goblin Chief",
            danger_level=CombatDangerLevel.DEFEATED,  # Already defeated
        )
        game.state.combat_state = CombatState(
            enemies=[enemy],
            turn=1,
        )
        
        # Process a combat action - enemy already dead, should record and end combat
        handle_combat_action(game, "attack")
        
        # Verify death was recorded
        assert world_db.is_npc_dead("Goblin Chief")
        death = world_db.get_npc_death("Goblin Chief")
        assert death.location == "Test Town"
        assert "combat" in death.cause.lower()
    
    def test_no_recording_without_world_state(self, game_state, campaign_db):
        """No error when world_state is None."""
        game = Game(state=game_state, db=campaign_db, world_state=None)
        
        enemy = Enemy(
            id=str(uuid4()),
            name="Goblin",
            danger_level=CombatDangerLevel.DEFEATED,
        )
        game.state.combat_state = CombatState(
            enemies=[enemy],
            turn=1,
        )
        
        # Should not crash
        handle_combat_action(game, "attack")


class TestNPCDeathChecks:
    """Tests for NPC death checking functions."""
    
    def test_is_npc_dead_checks_world_state(self, world_db):
        """Can check if NPC is dead."""
        from reverie.npc import is_npc_dead_in_world
        
        assert not is_npc_dead_in_world("Aldric", world_db)
        
        world_db.record_npc_death(NPCDeath.create(
            "Aldric", "Town Square", "Accident", "c1"
        ))
        
        assert is_npc_dead_in_world("Aldric", world_db)
    
    def test_get_npc_death_info(self, world_db):
        """Can get death info for NPC."""
        from reverie.npc import get_npc_death_info
        
        assert get_npc_death_info("Nobody", world_db) is None
        
        world_db.record_npc_death(NPCDeath.create(
            "Baron Evil", "Dark Castle", "Slain by hero", "c1"
        ))
        
        info = get_npc_death_info("Baron Evil", world_db)
        assert "Baron Evil" in info
        assert "Dark Castle" in info
        assert "Slain by hero" in info

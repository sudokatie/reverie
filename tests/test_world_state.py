"""Tests for world state persistence."""

import pytest
from datetime import datetime

from reverie.storage.world_state import (
    WorldStateDB,
    FactionStanding,
    NPCDeath,
    WorldEvent,
)


@pytest.fixture
def db():
    """Create in-memory world state database."""
    db = WorldStateDB.open_memory()
    yield db
    db.close()


class TestFactionStanding:
    """Tests for faction standing persistence."""
    
    def test_set_and_get_faction(self, db):
        """Can set and retrieve faction standing."""
        standing = FactionStanding(
            faction_id="guild_merchants",
            faction_name="Merchants Guild",
            standing=25,
        )
        db.set_faction_standing(standing)
        
        result = db.get_faction_standing("guild_merchants")
        assert result is not None
        assert result.faction_name == "Merchants Guild"
        assert result.standing == 25
    
    def test_get_nonexistent_faction(self, db):
        """Getting nonexistent faction returns None."""
        result = db.get_faction_standing("nonexistent")
        assert result is None
    
    def test_adjust_faction_creates_new(self, db):
        """Adjusting nonexistent faction creates it."""
        result = db.adjust_faction_standing("thieves_guild", "Thieves Guild", 15)
        assert result.faction_id == "thieves_guild"
        assert result.standing == 15
    
    def test_adjust_faction_updates_existing(self, db):
        """Adjusting existing faction updates standing."""
        standing = FactionStanding(
            faction_id="mages_guild",
            faction_name="Mages Guild",
            standing=50,
        )
        db.set_faction_standing(standing)
        
        result = db.adjust_faction_standing("mages_guild", "Mages Guild", -30)
        assert result.standing == 20
    
    def test_standing_clamps_to_bounds(self, db):
        """Standing is clamped to -100 to +100."""
        db.adjust_faction_standing("test", "Test Faction", 150)
        result = db.get_faction_standing("test")
        assert result.standing == 100
        
        db.adjust_faction_standing("test", "Test Faction", -300)
        result = db.get_faction_standing("test")
        assert result.standing == -100
    
    def test_list_faction_standings_sorted(self, db):
        """List factions sorted by standing descending."""
        db.set_faction_standing(FactionStanding("a", "Faction A", -50))
        db.set_faction_standing(FactionStanding("b", "Faction B", 75))
        db.set_faction_standing(FactionStanding("c", "Faction C", 25))
        
        factions = db.list_faction_standings()
        assert len(factions) == 3
        assert factions[0].standing == 75
        assert factions[1].standing == 25
        assert factions[2].standing == -50


class TestNPCDeath:
    """Tests for NPC death tracking."""
    
    def test_record_npc_death(self, db):
        """Can record an NPC death."""
        death = NPCDeath.create(
            npc_name="Aldric the Merchant",
            location="Crossroads Tavern",
            cause="Player attacked him for his gold",
            campaign_id="campaign_123",
        )
        db.record_npc_death(death)
        
        assert db.is_npc_dead("Aldric the Merchant")
    
    def test_npc_not_dead_by_default(self, db):
        """NPCs are not dead by default."""
        assert not db.is_npc_dead("Some Random NPC")
    
    def test_get_npc_death_details(self, db):
        """Can retrieve NPC death details."""
        death = NPCDeath.create(
            npc_name="Evil Wizard",
            location="Dark Tower",
            cause="Defeated in combat",
            campaign_id="campaign_456",
        )
        db.record_npc_death(death)
        
        result = db.get_npc_death("Evil Wizard")
        assert result is not None
        assert result.location == "Dark Tower"
        assert result.cause == "Defeated in combat"
        assert result.campaign_id == "campaign_456"
    
    def test_get_death_nonexistent(self, db):
        """Getting death of living NPC returns None."""
        result = db.get_npc_death("Still Alive NPC")
        assert result is None
    
    def test_list_npc_deaths(self, db):
        """Can list recent NPC deaths."""
        db.record_npc_death(NPCDeath.create("NPC 1", "Location 1", "Cause 1", "c1"))
        db.record_npc_death(NPCDeath.create("NPC 2", "Location 2", "Cause 2", "c2"))
        db.record_npc_death(NPCDeath.create("NPC 3", "Location 3", "Cause 3", "c3"))
        
        deaths = db.list_npc_deaths()
        assert len(deaths) == 3


class TestWorldEvent:
    """Tests for world event tracking."""
    
    def test_record_world_event(self, db):
        """Can record a world event."""
        event = WorldEvent.create(
            event_type="war",
            title="The Great War Begins",
            description="The kingdoms of the North declared war on the Southern Empire.",
            campaign_id="campaign_789",
            location="Northern Border",
        )
        db.record_world_event(event)
        
        events = db.list_world_events()
        assert len(events) == 1
        assert events[0].title == "The Great War Begins"
    
    def test_list_events_by_type(self, db):
        """Can filter events by type."""
        db.record_world_event(WorldEvent.create("war", "War 1", "Desc", "c1"))
        db.record_world_event(WorldEvent.create("plague", "Plague", "Desc", "c2"))
        db.record_world_event(WorldEvent.create("war", "War 2", "Desc", "c3"))
        
        war_events = db.list_world_events(event_type="war")
        assert len(war_events) == 2
        
        plague_events = db.list_world_events(event_type="plague")
        assert len(plague_events) == 1
    
    def test_event_with_data(self, db):
        """Events can store additional data."""
        event = WorldEvent.create(
            event_type="discovery",
            title="Ancient Ruins Found",
            description="Explorers discovered ancient ruins.",
            campaign_id="c1",
            data={"artifacts_found": 3, "danger_level": "high"},
        )
        db.record_world_event(event)
        
        result = db.list_world_events()[0]
        assert result.data["artifacts_found"] == 3
        assert result.data["danger_level"] == "high"


class TestWorldHistory:
    """Tests for world history summary."""
    
    def test_empty_history(self, db):
        """Empty world returns appropriate message."""
        summary = db.get_world_history_summary()
        assert summary == "No recorded world history."
    
    def test_history_summary_includes_events(self, db):
        """Summary includes recent events."""
        db.record_world_event(WorldEvent.create(
            "coronation", "New King Crowned", "King Harold III takes the throne.", "c1"
        ))
        
        summary = db.get_world_history_summary()
        assert "New King Crowned" in summary
        assert "King Harold III" in summary
    
    def test_history_summary_includes_deaths(self, db):
        """Summary includes NPC deaths."""
        db.record_npc_death(NPCDeath.create(
            "Lord Blackwood", "Castle Blackwood", "Assassinated", "c1"
        ))
        
        summary = db.get_world_history_summary()
        assert "Lord Blackwood" in summary
        assert "Castle Blackwood" in summary
    
    def test_history_summary_includes_factions(self, db):
        """Summary includes faction standings."""
        db.set_faction_standing(FactionStanding("guild", "Merchants Guild", 75))
        
        summary = db.get_world_history_summary()
        assert "Merchants Guild" in summary
        assert "allied" in summary


class TestExportImport:
    """Tests for export/import functionality."""
    
    def test_export_world_state(self, db):
        """Can export entire world state."""
        db.set_faction_standing(FactionStanding("guild", "Guild", 50))
        db.record_npc_death(NPCDeath.create("NPC", "Location", "Cause", "c1"))
        db.record_world_event(WorldEvent.create("war", "War", "Desc", "c1"))
        
        data = db.export_all()
        assert len(data["factions"]) == 1
        assert len(data["npc_deaths"]) == 1
        assert len(data["world_events"]) == 1
    
    def test_import_world_state(self, db):
        """Can import world state."""
        data = {
            "factions": [{"faction_id": "test", "faction_name": "Test", 
                         "standing": 30, "updated_at": datetime.now().isoformat()}],
            "npc_deaths": [],
            "world_events": [],
        }
        
        db.import_all(data)
        
        faction = db.get_faction_standing("test")
        assert faction is not None
        assert faction.standing == 30

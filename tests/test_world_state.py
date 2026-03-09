"""Tests for world state persistence."""

import pytest
from datetime import datetime

from reverie.storage.world_state import (
    WorldStateDB,
    FactionStanding,
    NPCDeath,
    WorldEvent,
    NPCMemoryRecord,
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


class TestNPCMemory:
    """Tests for persistent NPC memory system."""
    
    def test_create_npc_memory(self, db):
        """Can create an NPC memory record."""
        memory = NPCMemoryRecord.create(
            npc_name="Elara the Blacksmith",
            campaign_id="campaign_1",
            relationship_score=15,
            interaction_summary="Bought a sword, helped fix her wagon",
            last_interaction_type="trade",
        )
        db.save_npc_memory(memory)
        
        result = db.get_npc_memory("Elara the Blacksmith")
        assert result is not None
        assert result.relationship_score == 15
        assert result.interaction_summary == "Bought a sword, helped fix her wagon"
    
    def test_get_nonexistent_memory(self, db):
        """Getting memory for unknown NPC returns None."""
        result = db.get_npc_memory("Unknown NPC")
        assert result is None
    
    def test_update_npc_memory_new(self, db):
        """Updating memory for new NPC creates record."""
        memory = db.update_npc_memory(
            npc_name="New Friend",
            campaign_id="c1",
            relationship_delta=10,
            interaction_type="friendly",
            summary_addition="Had a pleasant conversation",
        )
        assert memory.relationship_score == 10
        assert memory.last_interaction_type == "friendly"
    
    def test_update_npc_memory_existing(self, db):
        """Updating existing memory modifies it."""
        db.update_npc_memory(
            npc_name="Recurring NPC",
            campaign_id="c1",
            relationship_delta=20,
            summary_addition="First meeting was good",
        )
        
        db.update_npc_memory(
            npc_name="Recurring NPC",
            campaign_id="c2",
            relationship_delta=-10,
            summary_addition="Had a disagreement",
            promise_broken=True,
        )
        
        memory = db.get_npc_memory("Recurring NPC")
        assert memory.relationship_score == 10  # 20 - 10
        assert memory.promises_broken == 1
        assert "First meeting" in memory.interaction_summary
        assert "disagreement" in memory.interaction_summary
    
    def test_relationship_score_clamped(self, db):
        """Relationship score stays within -100 to 100."""
        db.update_npc_memory("Test NPC", "c1", relationship_delta=150)
        memory = db.get_npc_memory("Test NPC")
        assert memory.relationship_score == 100
        
        db.update_npc_memory("Test NPC", "c1", relationship_delta=-300)
        memory = db.get_npc_memory("Test NPC")
        assert memory.relationship_score == -100
    
    def test_memorable_events_limited(self, db):
        """Only last 10 memorable events are kept."""
        for i in range(15):
            db.update_npc_memory(
                npc_name="Event NPC",
                campaign_id=f"c{i}",
                memorable_event=f"Event {i}",
            )
        
        memory = db.get_npc_memory("Event NPC")
        assert len(memory.memorable_events) == 10
        assert "Event 5" in memory.memorable_events
        assert "Event 14" in memory.memorable_events
        assert "Event 0" not in memory.memorable_events
    
    def test_gift_promise_tracking(self, db):
        """Gifts and promises are tracked."""
        db.update_npc_memory("Gift NPC", "c1", gift_given=True)
        db.update_npc_memory("Gift NPC", "c1", gift_given=True, promise_kept=True)
        db.update_npc_memory("Gift NPC", "c1", promise_broken=True)
        
        memory = db.get_npc_memory("Gift NPC")
        assert memory.gifts_received == 2
        assert memory.promises_kept == 1
        assert memory.promises_broken == 1
    
    def test_memory_context_for_llm(self, db):
        """Memory context is formatted for LLM."""
        db.update_npc_memory(
            npc_name="Old Friend",
            campaign_id="c1",
            relationship_delta=60,
            summary_addition="Saved from bandits",
            gift_given=True,
            promise_kept=True,
        )
        
        context = db.get_npc_memory_context("Old Friend")
        assert "old friends" in context.lower()
        assert "Saved from bandits" in context
        assert "1 gift" in context
        assert "1 promise" in context
    
    def test_memory_context_no_history(self, db):
        """Memory context for unknown NPC."""
        context = db.get_npc_memory_context("Stranger")
        assert "No prior history" in context
    
    def test_list_npc_memories(self, db):
        """Can list all NPC memories."""
        db.update_npc_memory("NPC A", "c1", relationship_delta=-50)
        db.update_npc_memory("NPC B", "c1", relationship_delta=75)
        db.update_npc_memory("NPC C", "c1", relationship_delta=25)
        
        memories = db.list_npc_memories()
        assert len(memories) == 3
        # Should be sorted by score descending
        assert memories[0].npc_name == "NPC B"
        assert memories[1].npc_name == "NPC C"
        assert memories[2].npc_name == "NPC A"
    
    def test_list_npc_memories_min_score(self, db):
        """Can filter memories by minimum score."""
        db.update_npc_memory("Enemy", "c1", relationship_delta=-30)
        db.update_npc_memory("Friend", "c1", relationship_delta=50)
        db.update_npc_memory("Acquaintance", "c1", relationship_delta=10)
        
        memories = db.list_npc_memories(min_score=20)
        assert len(memories) == 1
        assert memories[0].npc_name == "Friend"
    
    def test_allies_and_enemies(self, db):
        """Can get lists of allies and enemies."""
        db.update_npc_memory("Best Friend", "c1", relationship_delta=80)
        db.update_npc_memory("Friend", "c1", relationship_delta=30)
        db.update_npc_memory("Neutral", "c1", relationship_delta=0)
        db.update_npc_memory("Enemy", "c1", relationship_delta=-50)
        
        allies, enemies = db.get_allies_and_enemies()
        assert "Best Friend" in allies
        assert "Friend" in allies
        assert "Enemy" in enemies
        assert "Neutral" not in allies
        assert "Neutral" not in enemies
    
    def test_world_history_includes_relationships(self, db):
        """World history summary includes ally/enemy info."""
        db.update_npc_memory("Ally NPC", "c1", relationship_delta=50)
        db.update_npc_memory("Enemy NPC", "c1", relationship_delta=-50)
        
        summary = db.get_world_history_summary()
        assert "Ally NPC" in summary or "Allied NPCs" in summary
        assert "Enemy NPC" in summary or "Hostile NPCs" in summary
    
    def test_export_includes_memories(self, db):
        """Export includes NPC memories."""
        db.update_npc_memory("Exported NPC", "c1", relationship_delta=25)
        
        data = db.export_all()
        assert "npc_memories" in data
        assert len(data["npc_memories"]) == 1
        assert data["npc_memories"][0]["npc_name"] == "Exported NPC"
    
    def test_import_includes_memories(self, db):
        """Import handles NPC memories."""
        data = {
            "factions": [],
            "npc_deaths": [],
            "world_events": [],
            "npc_memories": [{
                "id": "test-id",
                "npc_name": "Imported NPC",
                "relationship_score": 40,
                "interaction_summary": "Imported history",
                "last_interaction_type": "friendly",
                "gifts_received": 2,
                "promises_kept": 1,
                "promises_broken": 0,
                "campaign_id": "imported",
                "timestamp": datetime.now().isoformat(),
                "memorable_events": ["Event 1"],
            }],
        }
        
        db.import_all(data)
        
        memory = db.get_npc_memory("Imported NPC")
        assert memory is not None
        assert memory.relationship_score == 40
        assert memory.gifts_received == 2

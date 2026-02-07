"""Tests for storage layer."""

import pytest
from datetime import datetime
from uuid import uuid4

from reverie.storage import (
    Campaign,
    CharacterRecord,
    WorldElementRecord,
    NPCRecord,
    QuestRecord,
    EventRecord,
    Database,
    create_database,
    save_campaign,
    load_campaign,
    list_campaigns,
    delete_campaign,
    export_campaign,
    import_campaign,
)


@pytest.fixture
def db():
    """Create an in-memory database for testing."""
    database = Database.open_memory()
    yield database
    database.close()


class TestCampaign:
    """Tests for Campaign model."""

    def test_create_campaign(self):
        """Create a new campaign."""
        campaign = Campaign.create("My Adventure")
        assert campaign.name == "My Adventure"
        assert campaign.id is not None
        assert campaign.playtime_seconds == 0

    def test_campaign_serialization(self):
        """Campaign serializes and deserializes."""
        original = Campaign.create("Test")
        data = original.to_dict()
        restored = Campaign.from_dict(data)
        
        assert restored.id == original.id
        assert restored.name == original.name


class TestCharacterRecord:
    """Tests for CharacterRecord model."""

    def test_character_serialization(self):
        """CharacterRecord serializes and deserializes."""
        original = CharacterRecord(
            id=str(uuid4()),
            campaign_id=str(uuid4()),
            name="Hero",
            data={"class": "warrior", "level": 5},
        )
        data = original.to_dict()
        restored = CharacterRecord.from_dict(data)
        
        assert restored.name == "Hero"
        assert restored.data["level"] == 5


class TestWorldElementRecord:
    """Tests for WorldElementRecord model."""

    def test_world_element_serialization(self):
        """WorldElementRecord serializes and deserializes."""
        original = WorldElementRecord(
            id=str(uuid4()),
            campaign_id=str(uuid4()),
            element_type="dungeon",
            name="Dark Cave",
            data={"difficulty": "hard"},
        )
        data = original.to_dict()
        restored = WorldElementRecord.from_dict(data)
        
        assert restored.element_type == "dungeon"
        assert restored.name == "Dark Cave"


class TestEventRecord:
    """Tests for EventRecord model."""

    def test_create_event(self):
        """Create an event."""
        event = EventRecord.create(
            campaign_id="camp-1",
            event_type="combat",
            description="Fought a goblin",
            data={"enemy": "goblin", "result": "victory"},
        )
        assert event.event_type == "combat"
        assert event.timestamp is not None


class TestDatabaseCampaign:
    """Tests for campaign database operations."""

    def test_save_and_load_campaign(self, db):
        """Save and load a campaign."""
        campaign = Campaign.create("Test Campaign")
        db.save_campaign(campaign)
        
        loaded = db.load_campaign(campaign.id)
        assert loaded is not None
        assert loaded.name == "Test Campaign"

    def test_list_campaigns(self, db):
        """List all campaigns."""
        db.save_campaign(Campaign.create("Campaign 1"))
        db.save_campaign(Campaign.create("Campaign 2"))
        
        campaigns = db.list_campaigns()
        assert len(campaigns) == 2

    def test_delete_campaign(self, db):
        """Delete a campaign."""
        campaign = Campaign.create("To Delete")
        db.save_campaign(campaign)
        
        assert db.delete_campaign(campaign.id)
        assert db.load_campaign(campaign.id) is None

    def test_delete_nonexistent_campaign(self, db):
        """Deleting nonexistent campaign returns False."""
        assert not db.delete_campaign("fake-id")


class TestDatabaseCharacter:
    """Tests for character database operations."""

    def test_save_and_load_character(self, db):
        """Save and load a character."""
        campaign = Campaign.create("Test")
        db.save_campaign(campaign)
        
        char = CharacterRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            name="Hero",
            data={"class": "mage"},
        )
        db.save_character(char)
        
        loaded = db.load_character(char.id)
        assert loaded is not None
        assert loaded.name == "Hero"
        assert loaded.data["class"] == "mage"

    def test_get_campaign_character(self, db):
        """Get character for a campaign."""
        campaign = Campaign.create("Test")
        db.save_campaign(campaign)
        
        char = CharacterRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            name="Hero",
            data={},
        )
        db.save_character(char)
        
        loaded = db.get_campaign_character(campaign.id)
        assert loaded is not None
        assert loaded.name == "Hero"


class TestDatabaseWorldElement:
    """Tests for world element database operations."""

    def test_save_and_load_world_element(self, db):
        """Save and load a world element."""
        campaign = Campaign.create("Test")
        db.save_campaign(campaign)
        
        elem = WorldElementRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            element_type="region",
            name="The North",
            data={"climate": "cold"},
        )
        db.save_world_element(elem)
        
        loaded = db.load_world_element(elem.id)
        assert loaded is not None
        assert loaded.name == "The North"

    def test_list_world_elements_by_type(self, db):
        """List world elements filtered by type."""
        campaign = Campaign.create("Test")
        db.save_campaign(campaign)
        
        db.save_world_element(WorldElementRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            element_type="region",
            name="Region 1",
            data={},
        ))
        db.save_world_element(WorldElementRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            element_type="dungeon",
            name="Dungeon 1",
            data={},
        ))
        
        regions = db.list_world_elements(campaign.id, element_type="region")
        assert len(regions) == 1
        assert regions[0].name == "Region 1"


class TestDatabaseNPC:
    """Tests for NPC database operations."""

    def test_save_and_load_npc(self, db):
        """Save and load an NPC."""
        campaign = Campaign.create("Test")
        db.save_campaign(campaign)
        
        npc = NPCRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            name="Bartender",
            location_id="tavern-1",
            data={"disposition": "friendly"},
        )
        db.save_npc(npc)
        
        loaded = db.load_npc(npc.id)
        assert loaded is not None
        assert loaded.name == "Bartender"

    def test_list_npcs_by_location(self, db):
        """List NPCs filtered by location."""
        campaign = Campaign.create("Test")
        db.save_campaign(campaign)
        
        db.save_npc(NPCRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            name="Guard",
            location_id="gate",
            data={},
        ))
        db.save_npc(NPCRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            name="Merchant",
            location_id="market",
            data={},
        ))
        
        gate_npcs = db.list_npcs(campaign.id, location_id="gate")
        assert len(gate_npcs) == 1
        assert gate_npcs[0].name == "Guard"


class TestDatabaseQuest:
    """Tests for quest database operations."""

    def test_save_and_load_quest(self, db):
        """Save and load a quest."""
        campaign = Campaign.create("Test")
        db.save_campaign(campaign)
        
        quest = QuestRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            title="Find the Artifact",
            status="active",
            data={"reward": 100},
        )
        db.save_quest(quest)
        
        loaded = db.load_quest(quest.id)
        assert loaded is not None
        assert loaded.title == "Find the Artifact"

    def test_list_quests_by_status(self, db):
        """List quests filtered by status."""
        campaign = Campaign.create("Test")
        db.save_campaign(campaign)
        
        db.save_quest(QuestRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            title="Active Quest",
            status="active",
            data={},
        ))
        db.save_quest(QuestRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            title="Completed Quest",
            status="completed",
            data={},
        ))
        
        active = db.list_quests(campaign.id, status="active")
        assert len(active) == 1
        assert active[0].title == "Active Quest"


class TestDatabaseEvent:
    """Tests for event database operations."""

    def test_save_and_list_events(self, db):
        """Save and list events."""
        campaign = Campaign.create("Test")
        db.save_campaign(campaign)
        
        event1 = EventRecord.create(
            campaign_id=campaign.id,
            event_type="action",
            description="Entered the dungeon",
        )
        event2 = EventRecord.create(
            campaign_id=campaign.id,
            event_type="combat",
            description="Fought a goblin",
        )
        
        db.save_event(event1)
        db.save_event(event2)
        
        events = db.list_events(campaign.id)
        assert len(events) == 2


class TestExportImport:
    """Tests for export/import functionality."""

    def test_export_campaign(self, db):
        """Export a campaign with all data."""
        campaign = Campaign.create("Export Test")
        db.save_campaign(campaign)
        
        char = CharacterRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            name="Hero",
            data={"level": 3},
        )
        db.save_character(char)
        
        npc = NPCRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            name="Guide",
            data={},
        )
        db.save_npc(npc)
        
        exported = db.export_campaign(campaign.id)
        
        assert exported["campaign"]["name"] == "Export Test"
        assert exported["character"]["name"] == "Hero"
        assert len(exported["npcs"]) == 1

    def test_export_nonexistent_campaign(self, db):
        """Export nonexistent campaign returns empty dict."""
        exported = db.export_campaign("fake-id")
        assert exported == {}

    def test_import_campaign(self, db):
        """Import a campaign from exported data."""
        data = {
            "campaign": {
                "id": str(uuid4()),
                "name": "Imported Campaign",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "character_id": None,
                "current_location_id": None,
                "playtime_seconds": 0,
            },
            "character": {
                "id": str(uuid4()),
                "campaign_id": "",  # Will be set from campaign
                "name": "Imported Hero",
                "data": {"level": 5},
            },
            "world_elements": [],
            "npcs": [],
            "quests": [],
            "events": [],
        }
        data["character"]["campaign_id"] = data["campaign"]["id"]
        
        campaign_id = db.import_campaign(data)
        assert campaign_id is not None
        
        loaded = db.load_campaign(campaign_id)
        assert loaded.name == "Imported Campaign"

    def test_import_invalid_data(self, db):
        """Import invalid data returns None."""
        campaign_id = db.import_campaign({})
        assert campaign_id is None


class TestHelperFunctions:
    """Tests for module-level helper functions."""

    def test_save_campaign_function(self, db):
        """save_campaign helper works."""
        campaign = Campaign.create("Test")
        save_campaign(db, campaign)
        
        loaded = load_campaign(db, campaign.id)
        assert loaded is not None

    def test_list_campaigns_function(self, db):
        """list_campaigns helper works."""
        save_campaign(db, Campaign.create("Test"))
        campaigns = list_campaigns(db)
        assert len(campaigns) == 1

    def test_delete_campaign_function(self, db):
        """delete_campaign helper works."""
        campaign = Campaign.create("Test")
        save_campaign(db, campaign)
        assert delete_campaign(db, campaign.id)

    def test_export_import_functions(self, db):
        """export_campaign and import_campaign helpers work."""
        campaign = Campaign.create("Original")
        save_campaign(db, campaign)
        
        exported = export_campaign(db, campaign.id)
        
        # Modify the campaign ID to simulate importing to a new database
        exported["campaign"]["id"] = str(uuid4())
        exported["campaign"]["name"] = "Imported Copy"
        
        new_id = import_campaign(db, exported)
        assert new_id is not None
        
        loaded = load_campaign(db, new_id)
        assert loaded.name == "Imported Copy"

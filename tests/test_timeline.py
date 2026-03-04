"""Tests for campaign timeline functionality."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from reverie.storage.database import Database
from reverie.storage.models import Campaign, EventRecord
from reverie.timeline import (
    CampaignTimeline,
    TimelineEntry,
    TimelineEventIcon,
    Chapter,
    format_timeline,
    format_chapters,
    add_chapter,
    add_campaign_start,
)
from reverie.game import EventType


@pytest.fixture
def db():
    """Create in-memory database."""
    return Database.open_memory()


@pytest.fixture
def campaign(db):
    """Create a test campaign."""
    campaign = Campaign.create("Test Campaign")
    db.save_campaign(campaign)
    return campaign


class TestTimelineEventIcon:
    """Tests for TimelineEventIcon."""
    
    def test_get_known_event_type(self):
        """Get icon for known event type."""
        assert TimelineEventIcon.get(EventType.COMBAT_START) == TimelineEventIcon.COMBAT_START
        assert TimelineEventIcon.get(EventType.QUEST_COMPLETE) == TimelineEventIcon.QUEST_COMPLETE
        
    def test_get_unknown_event_type(self):
        """Get default icon for unknown event type."""
        assert TimelineEventIcon.get("unknown_type") == TimelineEventIcon.DEFAULT


class TestTimelineEntry:
    """Tests for TimelineEntry."""
    
    def test_from_event_record(self):
        """Create entry from event record."""
        record = EventRecord(
            id=str(uuid4()),
            campaign_id="test",
            timestamp=datetime.now(),
            event_type=EventType.QUEST_COMPLETE,
            description="Completed the quest",
            data={"quest_name": "Test Quest"},
        )
        
        entry = TimelineEntry.from_event_record(record)
        
        assert entry.event_type == EventType.QUEST_COMPLETE
        assert entry.description == "Completed the quest"
        assert entry.is_milestone is True
        
    def test_non_milestone_entry(self):
        """Non-milestone events are marked correctly."""
        record = EventRecord(
            id=str(uuid4()),
            campaign_id="test",
            timestamp=datetime.now(),
            event_type=EventType.NARRATION,
            description="Some narration",
            data={},
        )
        
        entry = TimelineEntry.from_event_record(record)
        assert entry.is_milestone is False


class TestChapter:
    """Tests for Chapter dataclass."""
    
    def test_to_dict(self):
        """Serialize chapter to dict."""
        chapter = Chapter(
            name="Chapter 1",
            started_at=datetime(2026, 1, 1, 12, 0),
            event_count=10,
            quests_completed=2,
        )
        
        data = chapter.to_dict()
        
        assert data["name"] == "Chapter 1"
        assert data["event_count"] == 10
        assert data["quests_completed"] == 2
        
    def test_from_dict(self):
        """Deserialize chapter from dict."""
        data = {
            "name": "Chapter 2",
            "started_at": "2026-01-15T14:30:00",
            "event_count": 20,
            "quests_completed": 5,
            "combats_won": 3,
            "locations_visited": 4,
        }
        
        chapter = Chapter.from_dict(data)
        
        assert chapter.name == "Chapter 2"
        assert chapter.event_count == 20


class TestCampaignTimeline:
    """Tests for CampaignTimeline."""
    
    def test_empty_timeline(self, db, campaign):
        """Empty campaign has no chapters or entries."""
        tl = CampaignTimeline(db, campaign.id)
        
        assert tl.chapters == []
        assert tl.get_entries() == []
        
    def test_load_chapters_from_events(self, db, campaign):
        """Chapters are loaded from chapter start events."""
        # Add chapter events
        add_campaign_start(db, campaign.id, campaign.name)
        add_chapter(db, campaign.id, "The Beginning")
        
        tl = CampaignTimeline(db, campaign.id)
        
        assert len(tl.chapters) >= 1
        
    def test_get_entries(self, db, campaign):
        """Get timeline entries."""
        # Add some events
        add_campaign_start(db, campaign.id, campaign.name)
        
        event = EventRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            timestamp=datetime.now(),
            event_type=EventType.LOCATION_CHANGE,
            description="Entered the tavern",
            data={"location_name": "Tavern"},
        )
        db.save_event(event)
        
        tl = CampaignTimeline(db, campaign.id)
        entries = tl.get_entries()
        
        assert len(entries) >= 1
        
    def test_get_entries_milestones_only(self, db, campaign):
        """Filter to milestones only."""
        # Add milestone event
        milestone = EventRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            timestamp=datetime.now(),
            event_type=EventType.QUEST_COMPLETE,
            description="Quest completed",
            data={},
        )
        db.save_event(milestone)
        
        # Add non-milestone event
        narration = EventRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            timestamp=datetime.now(),
            event_type=EventType.NARRATION,
            description="Some narration",
            data={},
        )
        db.save_event(narration)
        
        tl = CampaignTimeline(db, campaign.id)
        entries = tl.get_entries(milestones_only=True)
        
        # Should only include milestone
        for entry in entries:
            assert entry.is_milestone is True
            
    def test_get_entries_filtered_by_type(self, db, campaign):
        """Filter entries by event type."""
        # Add combat event
        combat = EventRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            timestamp=datetime.now(),
            event_type=EventType.COMBAT_END,
            description="Combat ended",
            data={},
        )
        db.save_event(combat)
        
        # Add dialogue event
        dialogue = EventRecord(
            id=str(uuid4()),
            campaign_id=campaign.id,
            timestamp=datetime.now(),
            event_type=EventType.NPC_DIALOGUE,
            description="Talked to NPC",
            data={},
        )
        db.save_event(dialogue)
        
        tl = CampaignTimeline(db, campaign.id)
        entries = tl.get_entries(event_types=[EventType.COMBAT_END])
        
        for entry in entries:
            assert entry.event_type == EventType.COMBAT_END
            
    def test_get_summary(self, db, campaign):
        """Get campaign summary statistics."""
        # Add various events
        events = [
            (EventType.QUEST_COMPLETE, "Quest done"),
            (EventType.COMBAT_END, "Combat won"),
            (EventType.LOCATION_CHANGE, "Moved"),
            (EventType.LEVEL_UP, "Leveled up"),
        ]
        
        for event_type, desc in events:
            event = EventRecord(
                id=str(uuid4()),
                campaign_id=campaign.id,
                timestamp=datetime.now(),
                event_type=event_type,
                description=desc,
                data={},
            )
            db.save_event(event)
        
        tl = CampaignTimeline(db, campaign.id)
        summary = tl.get_summary()
        
        assert summary["total_events"] == 4
        assert summary["quests_completed"] == 1
        assert summary["combats_won"] == 1
        assert summary["level_ups"] == 1


class TestFormatFunctions:
    """Tests for timeline formatting functions."""
    
    def test_format_timeline_empty(self, db, campaign):
        """Format empty timeline."""
        tl = CampaignTimeline(db, campaign.id)
        output = format_timeline(tl, campaign)
        
        assert campaign.name in output
        assert "No events yet" in output
        
    def test_format_timeline_with_events(self, db, campaign):
        """Format timeline with events."""
        add_campaign_start(db, campaign.id, campaign.name)
        
        tl = CampaignTimeline(db, campaign.id)
        output = format_timeline(tl, campaign)
        
        assert campaign.name in output
        assert "Recent Events" in output
        
    def test_format_chapters_empty(self, db, campaign):
        """Format empty chapters list."""
        tl = CampaignTimeline(db, campaign.id)
        output = format_chapters(tl, campaign)
        
        assert campaign.name in output
        assert "No chapters yet" in output
        
    def test_format_chapters_with_chapters(self, db, campaign):
        """Format chapters list with chapters."""
        add_campaign_start(db, campaign.id, campaign.name)
        add_chapter(db, campaign.id, "The Journey Begins")
        
        tl = CampaignTimeline(db, campaign.id)
        output = format_chapters(tl, campaign)
        
        assert campaign.name in output


class TestAddChapter:
    """Tests for add_chapter function."""
    
    def test_add_chapter(self, db, campaign):
        """Add a chapter to campaign."""
        add_chapter(db, campaign.id, "The Dark Forest")
        
        events = db.list_events(campaign.id)
        chapter_events = [e for e in events if e.event_type == EventType.CHAPTER_START]
        
        assert len(chapter_events) == 1
        assert chapter_events[0].data.get("chapter_name") == "The Dark Forest"
        
    def test_add_multiple_chapters(self, db, campaign):
        """Add multiple chapters."""
        add_chapter(db, campaign.id, "Chapter 1")
        add_chapter(db, campaign.id, "Chapter 2")
        add_chapter(db, campaign.id, "Chapter 3")
        
        events = db.list_events(campaign.id)
        chapter_events = [e for e in events if e.event_type == EventType.CHAPTER_START]
        
        assert len(chapter_events) == 3


class TestAddCampaignStart:
    """Tests for add_campaign_start function."""
    
    def test_add_campaign_start(self, db, campaign):
        """Add campaign start event."""
        add_campaign_start(db, campaign.id, "Epic Adventure")
        
        events = db.list_events(campaign.id)
        start_events = [e for e in events if e.event_type == EventType.CAMPAIGN_START]
        
        assert len(start_events) == 1
        assert start_events[0].data.get("campaign_name") == "Epic Adventure"

"""Campaign timeline utilities for Reverie.

Provides timeline view and chapter management for campaigns.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .storage.database import Database
from .storage.models import Campaign, EventRecord
from .game import EventType


class TimelineEventIcon:
    """Icons for different event types in timeline display."""
    NARRATION = "📜"
    PLAYER_ACTION = "🎭"
    NPC_DIALOGUE = "💬"
    COMBAT_START = "⚔️"
    COMBAT_END = "🏆"
    QUEST_START = "📋"
    QUEST_COMPLETE = "✅"
    QUEST_FAIL = "❌"
    LOCATION_CHANGE = "🗺️"
    ITEM_ACQUIRED = "🎁"
    ITEM_USED = "🧪"
    LEVEL_UP = "⬆️"
    DISCOVERY = "💡"
    CHAPTER_START = "📖"
    CAMPAIGN_START = "🎬"
    DEFAULT = "•"

    @classmethod
    def get(cls, event_type: str) -> str:
        """Get icon for event type."""
        return getattr(cls, event_type.upper(), cls.DEFAULT)


@dataclass
class TimelineEntry:
    """A processed entry for timeline display."""
    timestamp: datetime
    event_type: str
    description: str
    icon: str
    is_milestone: bool = False
    chapter: Optional[str] = None
    
    @classmethod
    def from_event_record(cls, record: EventRecord, chapter: Optional[str] = None) -> "TimelineEntry":
        """Create timeline entry from event record."""
        is_milestone = record.event_type in (
            EventType.CHAPTER_START,
            EventType.CAMPAIGN_START,
            EventType.QUEST_COMPLETE,
            EventType.LEVEL_UP,
            EventType.COMBAT_END,
        )
        return cls(
            timestamp=record.timestamp,
            event_type=record.event_type,
            description=record.description,
            icon=TimelineEventIcon.get(record.event_type),
            is_milestone=is_milestone,
            chapter=chapter,
        )


@dataclass
class Chapter:
    """A chapter/adventure marker in the campaign."""
    name: str
    started_at: datetime
    event_count: int = 0
    quests_completed: int = 0
    combats_won: int = 0
    locations_visited: int = 0
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "started_at": self.started_at.isoformat(),
            "event_count": self.event_count,
            "quests_completed": self.quests_completed,
            "combats_won": self.combats_won,
            "locations_visited": self.locations_visited,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Chapter":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            started_at=datetime.fromisoformat(data["started_at"]),
            event_count=data.get("event_count", 0),
            quests_completed=data.get("quests_completed", 0),
            combats_won=data.get("combats_won", 0),
            locations_visited=data.get("locations_visited", 0),
        )


class CampaignTimeline:
    """Manages campaign timeline and chapters."""
    
    def __init__(self, db: Database, campaign_id: str):
        self.db = db
        self.campaign_id = campaign_id
        self._chapters: list[Chapter] = []
        self._load_chapters()
    
    def _load_chapters(self) -> None:
        """Load chapters from events."""
        events = self.db.list_events(self.campaign_id, limit=10000)
        
        current_chapter: Optional[Chapter] = None
        chapters: list[Chapter] = []
        
        for event in reversed(events):  # Chronological order
            if event.event_type == EventType.CHAPTER_START:
                if current_chapter:
                    chapters.append(current_chapter)
                chapter_name = event.data.get("chapter_name", event.description)
                current_chapter = Chapter(
                    name=chapter_name,
                    started_at=event.timestamp,
                )
            elif event.event_type == EventType.CAMPAIGN_START:
                if current_chapter:
                    chapters.append(current_chapter)
                current_chapter = Chapter(
                    name="Prologue",
                    started_at=event.timestamp,
                )
            
            if current_chapter:
                current_chapter.event_count += 1
                if event.event_type == EventType.QUEST_COMPLETE:
                    current_chapter.quests_completed += 1
                elif event.event_type == EventType.COMBAT_END:
                    current_chapter.combats_won += 1
                elif event.event_type == EventType.LOCATION_CHANGE:
                    current_chapter.locations_visited += 1
        
        if current_chapter:
            chapters.append(current_chapter)
        
        self._chapters = chapters
    
    @property
    def chapters(self) -> list[Chapter]:
        """Get list of chapters."""
        return self._chapters
    
    def get_entries(
        self,
        limit: int = 100,
        event_types: Optional[list[str]] = None,
        milestones_only: bool = False,
    ) -> list[TimelineEntry]:
        """Get timeline entries with optional filtering."""
        events = self.db.list_events(self.campaign_id, limit=limit)
        
        # Build chapter mapping
        chapter_map: dict[str, str] = {}
        current_chapter = None
        for event in reversed(events):
            if event.event_type in (EventType.CHAPTER_START, EventType.CAMPAIGN_START):
                current_chapter = event.data.get("chapter_name", event.description)
            chapter_map[event.id] = current_chapter
        
        entries = []
        for event in events:  # Most recent first
            chapter = chapter_map.get(event.id)
            entry = TimelineEntry.from_event_record(event, chapter)
            
            # Apply filters
            if event_types and entry.event_type not in event_types:
                continue
            if milestones_only and not entry.is_milestone:
                continue
            
            entries.append(entry)
        
        return entries
    
    def get_summary(self) -> dict:
        """Get campaign summary statistics."""
        events = self.db.list_events(self.campaign_id, limit=10000)
        
        stats = {
            "total_events": len(events),
            "chapters": len(self._chapters),
            "quests_completed": 0,
            "quests_failed": 0,
            "combats_won": 0,
            "locations_visited": set(),
            "items_acquired": 0,
            "level_ups": 0,
            "npcs_talked_to": set(),
        }
        
        for event in events:
            if event.event_type == EventType.QUEST_COMPLETE:
                stats["quests_completed"] += 1
            elif event.event_type == EventType.QUEST_FAIL:
                stats["quests_failed"] += 1
            elif event.event_type == EventType.COMBAT_END:
                stats["combats_won"] += 1
            elif event.event_type == EventType.LOCATION_CHANGE:
                location = event.data.get("location_name")
                if location:
                    stats["locations_visited"].add(location)
            elif event.event_type == EventType.ITEM_ACQUIRED:
                stats["items_acquired"] += 1
            elif event.event_type == EventType.LEVEL_UP:
                stats["level_ups"] += 1
            elif event.event_type == EventType.NPC_DIALOGUE:
                npc = event.data.get("npc_name")
                if npc:
                    stats["npcs_talked_to"].add(npc)
        
        # Convert sets to counts
        stats["locations_visited"] = len(stats["locations_visited"])
        stats["npcs_talked_to"] = len(stats["npcs_talked_to"])
        
        return stats


def format_timeline(
    timeline: CampaignTimeline,
    campaign: Campaign,
    limit: int = 50,
    milestones_only: bool = False,
    show_chapters: bool = True,
) -> str:
    """Format campaign timeline for display."""
    console = Console(record=True, width=80)
    
    # Header
    playtime_min = campaign.playtime_seconds // 60
    console.print(Panel(
        f"[bold]{campaign.name}[/bold]\n"
        f"Started: {campaign.created_at.strftime('%Y-%m-%d')}\n"
        f"Last played: {campaign.updated_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"Playtime: {playtime_min} minutes",
        title="Campaign Timeline",
    ))
    
    # Summary stats
    summary = timeline.get_summary()
    console.print()
    console.print(f"[dim]Events:[/dim] {summary['total_events']} | "
                  f"[dim]Chapters:[/dim] {summary['chapters']} | "
                  f"[dim]Quests:[/dim] {summary['quests_completed']} | "
                  f"[dim]Combats:[/dim] {summary['combats_won']} | "
                  f"[dim]Locations:[/dim] {summary['locations_visited']}")
    console.print()
    
    # Chapters overview
    if show_chapters and timeline.chapters:
        console.print("[bold]Chapters:[/bold]")
        for i, chapter in enumerate(timeline.chapters, 1):
            duration = ""
            if i < len(timeline.chapters):
                next_chapter = timeline.chapters[i]
                delta = next_chapter.started_at - chapter.started_at
                duration = f" ({_format_duration(delta)})"
            console.print(f"  {i}. {chapter.name}{duration}")
        console.print()
    
    # Timeline entries
    entries = timeline.get_entries(limit=limit, milestones_only=milestones_only)
    
    if not entries:
        console.print("[dim]No events yet.[/dim]")
        return console.export_text()
    
    console.print("[bold]Recent Events:[/bold]")
    
    current_date = None
    for entry in entries:
        date_str = entry.timestamp.strftime("%Y-%m-%d")
        if date_str != current_date:
            current_date = date_str
            console.print(f"\n[bold cyan]{date_str}[/bold cyan]")
        
        time_str = entry.timestamp.strftime("%H:%M")
        
        # Highlight milestones
        if entry.is_milestone:
            console.print(f"  [bold]{entry.icon} {time_str}[/bold] - [bold]{entry.description}[/bold]")
        else:
            console.print(f"  {entry.icon} [dim]{time_str}[/dim] - {entry.description[:60]}")
    
    return console.export_text()


def format_chapters(timeline: CampaignTimeline, campaign: Campaign) -> str:
    """Format chapter summary for display."""
    console = Console(record=True, width=80)
    
    console.print(Panel(f"[bold]{campaign.name}[/bold]", title="Chapters"))
    
    if not timeline.chapters:
        console.print("[dim]No chapters yet. Start a new chapter with 'reverie chapter'.[/dim]")
        return console.export_text()
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=3)
    table.add_column("Chapter")
    table.add_column("Started", style="cyan")
    table.add_column("Events", justify="right")
    table.add_column("Quests", justify="right")
    table.add_column("Combats", justify="right")
    
    for i, chapter in enumerate(timeline.chapters, 1):
        table.add_row(
            str(i),
            chapter.name,
            chapter.started_at.strftime("%Y-%m-%d"),
            str(chapter.event_count),
            str(chapter.quests_completed),
            str(chapter.combats_won),
        )
    
    console.print(table)
    return console.export_text()


def _format_duration(delta: timedelta) -> str:
    """Format a timedelta for display."""
    days = delta.days
    hours = delta.seconds // 3600
    
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h"
    else:
        minutes = delta.seconds // 60
        return f"{minutes}m"


def add_chapter(db: Database, campaign_id: str, chapter_name: str) -> None:
    """Add a new chapter to a campaign."""
    from .storage.models import EventRecord
    
    event = EventRecord(
        id=str(__import__("uuid").uuid4()),
        campaign_id=campaign_id,
        timestamp=datetime.now(),
        event_type=EventType.CHAPTER_START,
        description=f"Chapter started: {chapter_name}",
        data={"chapter_name": chapter_name},
    )
    db.save_event(event)


def add_campaign_start(db: Database, campaign_id: str, campaign_name: str) -> None:
    """Add campaign start event."""
    from .storage.models import EventRecord
    
    event = EventRecord(
        id=str(__import__("uuid").uuid4()),
        campaign_id=campaign_id,
        timestamp=datetime.now(),
        event_type=EventType.CAMPAIGN_START,
        description=f"Campaign started: {campaign_name}",
        data={"campaign_name": campaign_name},
    )
    db.save_event(event)

"""Database operations for Reverie."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from .models import (
    Campaign,
    CharacterRecord,
    WorldElementRecord,
    NPCRecord,
    QuestRecord,
    EventRecord,
)
from .migrations import run_migrations, reset_schema


class Database:
    """SQLite database wrapper for Reverie."""
    
    def __init__(self, conn: sqlite3.Connection):
        """Initialize with existing connection."""
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
    
    @classmethod
    def open(cls, path: Path) -> "Database":
        """Open or create database at path."""
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        conn.execute("PRAGMA foreign_keys = ON")
        run_migrations(conn)
        return cls(conn)
    
    @classmethod
    def open_memory(cls) -> "Database":
        """Open in-memory database for testing."""
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA foreign_keys = ON")
        run_migrations(conn)
        return cls(conn)
    
    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
    
    # === Campaign Operations ===
    
    def save_campaign(self, campaign: Campaign) -> None:
        """Save or update a campaign."""
        campaign.updated_at = datetime.now()
        self.conn.execute(
            """INSERT OR REPLACE INTO campaigns 
               (id, name, created_at, updated_at, character_id, current_location_id, playtime_seconds)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                campaign.id,
                campaign.name,
                campaign.created_at.isoformat(),
                campaign.updated_at.isoformat(),
                campaign.character_id,
                campaign.current_location_id,
                campaign.playtime_seconds,
            ),
        )
        self.conn.commit()
    
    def load_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Load a campaign by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM campaigns WHERE id = ?", (campaign_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Campaign(
            id=row["id"],
            name=row["name"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            character_id=row["character_id"],
            current_location_id=row["current_location_id"],
            playtime_seconds=row["playtime_seconds"],
        )
    
    def list_campaigns(self) -> list[Campaign]:
        """List all campaigns."""
        cursor = self.conn.execute(
            "SELECT * FROM campaigns ORDER BY updated_at DESC"
        )
        campaigns = []
        for row in cursor:
            campaigns.append(Campaign(
                id=row["id"],
                name=row["name"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                character_id=row["character_id"],
                current_location_id=row["current_location_id"],
                playtime_seconds=row["playtime_seconds"],
            ))
        return campaigns
    
    def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign and all related data."""
        cursor = self.conn.execute(
            "DELETE FROM campaigns WHERE id = ?", (campaign_id,)
        )
        self.conn.commit()
        return cursor.rowcount > 0
    
    # === Character Operations ===
    
    def save_character(self, record: CharacterRecord) -> None:
        """Save or update a character."""
        self.conn.execute(
            """INSERT OR REPLACE INTO characters (id, campaign_id, name, data)
               VALUES (?, ?, ?, ?)""",
            (record.id, record.campaign_id, record.name, json.dumps(record.data)),
        )
        self.conn.commit()
    
    def load_character(self, character_id: str) -> Optional[CharacterRecord]:
        """Load a character by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM characters WHERE id = ?", (character_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return CharacterRecord(
            id=row["id"],
            campaign_id=row["campaign_id"],
            name=row["name"],
            data=json.loads(row["data"]),
        )
    
    def get_campaign_character(self, campaign_id: str) -> Optional[CharacterRecord]:
        """Get the character for a campaign."""
        cursor = self.conn.execute(
            "SELECT * FROM characters WHERE campaign_id = ?", (campaign_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return CharacterRecord(
            id=row["id"],
            campaign_id=row["campaign_id"],
            name=row["name"],
            data=json.loads(row["data"]),
        )
    
    # === World Element Operations ===
    
    def save_world_element(self, record: WorldElementRecord) -> None:
        """Save or update a world element."""
        self.conn.execute(
            """INSERT OR REPLACE INTO world_elements (id, campaign_id, element_type, name, data)
               VALUES (?, ?, ?, ?, ?)""",
            (record.id, record.campaign_id, record.element_type, record.name, json.dumps(record.data)),
        )
        self.conn.commit()
    
    def load_world_element(self, element_id: str) -> Optional[WorldElementRecord]:
        """Load a world element by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM world_elements WHERE id = ?", (element_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return WorldElementRecord(
            id=row["id"],
            campaign_id=row["campaign_id"],
            element_type=row["element_type"],
            name=row["name"],
            data=json.loads(row["data"]),
        )
    
    def list_world_elements(self, campaign_id: str, element_type: Optional[str] = None) -> list[WorldElementRecord]:
        """List world elements for a campaign."""
        if element_type:
            cursor = self.conn.execute(
                "SELECT * FROM world_elements WHERE campaign_id = ? AND element_type = ?",
                (campaign_id, element_type),
            )
        else:
            cursor = self.conn.execute(
                "SELECT * FROM world_elements WHERE campaign_id = ?", (campaign_id,)
            )
        
        elements = []
        for row in cursor:
            elements.append(WorldElementRecord(
                id=row["id"],
                campaign_id=row["campaign_id"],
                element_type=row["element_type"],
                name=row["name"],
                data=json.loads(row["data"]),
            ))
        return elements
    
    # === NPC Operations ===
    
    def save_npc(self, record: NPCRecord) -> None:
        """Save or update an NPC."""
        self.conn.execute(
            """INSERT OR REPLACE INTO npcs (id, campaign_id, name, location_id, data)
               VALUES (?, ?, ?, ?, ?)""",
            (record.id, record.campaign_id, record.name, record.location_id, json.dumps(record.data)),
        )
        self.conn.commit()
    
    def load_npc(self, npc_id: str) -> Optional[NPCRecord]:
        """Load an NPC by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM npcs WHERE id = ?", (npc_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return NPCRecord(
            id=row["id"],
            campaign_id=row["campaign_id"],
            name=row["name"],
            location_id=row["location_id"],
            data=json.loads(row["data"]),
        )
    
    def list_npcs(self, campaign_id: str, location_id: Optional[str] = None) -> list[NPCRecord]:
        """List NPCs for a campaign, optionally filtered by location."""
        if location_id:
            cursor = self.conn.execute(
                "SELECT * FROM npcs WHERE campaign_id = ? AND location_id = ?",
                (campaign_id, location_id),
            )
        else:
            cursor = self.conn.execute(
                "SELECT * FROM npcs WHERE campaign_id = ?", (campaign_id,)
            )
        
        npcs = []
        for row in cursor:
            npcs.append(NPCRecord(
                id=row["id"],
                campaign_id=row["campaign_id"],
                name=row["name"],
                location_id=row["location_id"],
                data=json.loads(row["data"]),
            ))
        return npcs
    
    # === Quest Operations ===
    
    def save_quest(self, record: QuestRecord) -> None:
        """Save or update a quest."""
        self.conn.execute(
            """INSERT OR REPLACE INTO quests (id, campaign_id, title, status, data)
               VALUES (?, ?, ?, ?, ?)""",
            (record.id, record.campaign_id, record.title, record.status, json.dumps(record.data)),
        )
        self.conn.commit()
    
    def load_quest(self, quest_id: str) -> Optional[QuestRecord]:
        """Load a quest by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM quests WHERE id = ?", (quest_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return QuestRecord(
            id=row["id"],
            campaign_id=row["campaign_id"],
            title=row["title"],
            status=row["status"],
            data=json.loads(row["data"]),
        )
    
    def list_quests(self, campaign_id: str, status: Optional[str] = None) -> list[QuestRecord]:
        """List quests for a campaign, optionally filtered by status."""
        if status:
            cursor = self.conn.execute(
                "SELECT * FROM quests WHERE campaign_id = ? AND status = ?",
                (campaign_id, status),
            )
        else:
            cursor = self.conn.execute(
                "SELECT * FROM quests WHERE campaign_id = ?", (campaign_id,)
            )
        
        quests = []
        for row in cursor:
            quests.append(QuestRecord(
                id=row["id"],
                campaign_id=row["campaign_id"],
                title=row["title"],
                status=row["status"],
                data=json.loads(row["data"]),
            ))
        return quests
    
    # === Event Operations ===
    
    def save_event(self, record: EventRecord) -> None:
        """Save an event."""
        self.conn.execute(
            """INSERT INTO events (id, campaign_id, timestamp, event_type, description, data)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                record.id,
                record.campaign_id,
                record.timestamp.isoformat(),
                record.event_type,
                record.description,
                json.dumps(record.data),
            ),
        )
        self.conn.commit()
    
    def list_events(self, campaign_id: str, limit: int = 100) -> list[EventRecord]:
        """List events for a campaign, most recent first."""
        cursor = self.conn.execute(
            "SELECT * FROM events WHERE campaign_id = ? ORDER BY timestamp DESC LIMIT ?",
            (campaign_id, limit),
        )
        
        events = []
        for row in cursor:
            events.append(EventRecord(
                id=row["id"],
                campaign_id=row["campaign_id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                event_type=row["event_type"],
                description=row["description"],
                data=json.loads(row["data"]),
            ))
        return events
    
    # === Export/Import ===
    
    def export_campaign(self, campaign_id: str) -> dict:
        """Export a campaign and all related data."""
        campaign = self.load_campaign(campaign_id)
        if campaign is None:
            return {}
        
        character = self.get_campaign_character(campaign_id)
        
        return {
            "campaign": campaign.to_dict(),
            "character": character.to_dict() if character else None,
            "world_elements": [e.to_dict() for e in self.list_world_elements(campaign_id)],
            "npcs": [n.to_dict() for n in self.list_npcs(campaign_id)],
            "quests": [q.to_dict() for q in self.list_quests(campaign_id)],
            "events": [e.to_dict() for e in self.list_events(campaign_id, limit=1000)],
        }
    
    def import_campaign(self, data: dict) -> Optional[str]:
        """Import a campaign from exported data.
        
        Returns the campaign ID or None on failure.
        """
        if "campaign" not in data:
            return None
        
        campaign = Campaign.from_dict(data["campaign"])
        self.save_campaign(campaign)
        
        if data.get("character"):
            character = CharacterRecord.from_dict(data["character"])
            self.save_character(character)
        
        for elem_data in data.get("world_elements", []):
            elem = WorldElementRecord.from_dict(elem_data)
            self.save_world_element(elem)
        
        for npc_data in data.get("npcs", []):
            npc = NPCRecord.from_dict(npc_data)
            self.save_npc(npc)
        
        for quest_data in data.get("quests", []):
            quest = QuestRecord.from_dict(quest_data)
            self.save_quest(quest)
        
        for event_data in data.get("events", []):
            event = EventRecord.from_dict(event_data)
            self.save_event(event)
        
        return campaign.id


# Helper functions

def create_database(path: Path) -> Database:
    """Create or open a database at the given path."""
    return Database.open(path)


def save_campaign(db: Database, campaign: Campaign) -> None:
    """Save a campaign to the database."""
    db.save_campaign(campaign)


def load_campaign(db: Database, campaign_id: str) -> Optional[Campaign]:
    """Load a campaign from the database."""
    return db.load_campaign(campaign_id)


def list_campaigns(db: Database) -> list[Campaign]:
    """List all campaigns in the database."""
    return db.list_campaigns()


def delete_campaign(db: Database, campaign_id: str) -> bool:
    """Delete a campaign from the database."""
    return db.delete_campaign(campaign_id)


def export_campaign(db: Database, campaign_id: str) -> dict:
    """Export a campaign to a dictionary."""
    return db.export_campaign(campaign_id)


def import_campaign(db: Database, data: dict) -> Optional[str]:
    """Import a campaign from a dictionary."""
    return db.import_campaign(data)

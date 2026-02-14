"""Persistent world state storage.

Tracks world-level state that persists across campaigns:
- NPC deaths (an NPC killed in one campaign is dead in future campaigns)
- Faction standings (reputation with factions persists)
- World events (major events that affected the world)

This creates a separate database from campaign saves, allowing
new campaigns to reference previous world history.
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4


@dataclass
class FactionStanding:
    """Standing with a faction (-100 to +100)."""
    faction_id: str
    faction_name: str
    standing: int  # -100 (hated) to +100 (revered)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "faction_id": self.faction_id,
            "faction_name": self.faction_name,
            "standing": self.standing,
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FactionStanding":
        return cls(
            faction_id=data["faction_id"],
            faction_name=data["faction_name"],
            standing=data["standing"],
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class NPCDeath:
    """Record of an NPC's death."""
    id: str
    npc_name: str
    npc_id: Optional[str]  # Original NPC ID if available
    location: str
    cause: str  # How they died
    campaign_id: str  # Which campaign this happened in
    timestamp: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def create(
        cls,
        npc_name: str,
        location: str,
        cause: str,
        campaign_id: str,
        npc_id: Optional[str] = None,
    ) -> "NPCDeath":
        return cls(
            id=str(uuid4()),
            npc_name=npc_name,
            npc_id=npc_id,
            location=location,
            cause=cause,
            campaign_id=campaign_id,
        )
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "npc_name": self.npc_name,
            "npc_id": self.npc_id,
            "location": self.location,
            "cause": self.cause,
            "campaign_id": self.campaign_id,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "NPCDeath":
        return cls(
            id=data["id"],
            npc_name=data["npc_name"],
            npc_id=data.get("npc_id"),
            location=data["location"],
            cause=data["cause"],
            campaign_id=data["campaign_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class WorldEvent:
    """A major world event that persists across campaigns."""
    id: str
    event_type: str  # war, plague, coronation, disaster, discovery, etc.
    title: str
    description: str
    location: Optional[str]  # Where it happened
    campaign_id: str  # Which campaign triggered it
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict = field(default_factory=dict)  # Additional event-specific data
    
    @classmethod
    def create(
        cls,
        event_type: str,
        title: str,
        description: str,
        campaign_id: str,
        location: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> "WorldEvent":
        return cls(
            id=str(uuid4()),
            event_type=event_type,
            title=title,
            description=description,
            location=location,
            campaign_id=campaign_id,
            data=data or {},
        )
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "campaign_id": self.campaign_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "WorldEvent":
        return cls(
            id=data["id"],
            event_type=data["event_type"],
            title=data["title"],
            description=data["description"],
            location=data.get("location"),
            campaign_id=data["campaign_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data.get("data", {}),
        )


WORLD_STATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS faction_standings (
    faction_id TEXT PRIMARY KEY,
    faction_name TEXT NOT NULL,
    standing INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS npc_deaths (
    id TEXT PRIMARY KEY,
    npc_name TEXT NOT NULL,
    npc_id TEXT,
    location TEXT NOT NULL,
    cause TEXT NOT NULL,
    campaign_id TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS world_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT,
    campaign_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    data TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_npc_deaths_name ON npc_deaths(npc_name);
CREATE INDEX IF NOT EXISTS idx_world_events_type ON world_events(event_type);
CREATE INDEX IF NOT EXISTS idx_world_events_timestamp ON world_events(timestamp);
"""


class WorldStateDB:
    """Database for persistent world state."""
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
    
    @classmethod
    def open(cls, path: Path) -> "WorldStateDB":
        """Open or create world state database."""
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        conn.executescript(WORLD_STATE_SCHEMA)
        conn.commit()
        return cls(conn)
    
    @classmethod
    def open_memory(cls) -> "WorldStateDB":
        """Open in-memory database for testing."""
        conn = sqlite3.connect(":memory:")
        conn.executescript(WORLD_STATE_SCHEMA)
        conn.commit()
        return cls(conn)
    
    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
    
    # === Faction Operations ===
    
    def get_faction_standing(self, faction_id: str) -> Optional[FactionStanding]:
        """Get standing with a faction."""
        cursor = self.conn.execute(
            "SELECT * FROM faction_standings WHERE faction_id = ?",
            (faction_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return FactionStanding(
            faction_id=row["faction_id"],
            faction_name=row["faction_name"],
            standing=row["standing"],
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
    
    def set_faction_standing(self, standing: FactionStanding) -> None:
        """Set or update faction standing."""
        standing.updated_at = datetime.now()
        self.conn.execute(
            """INSERT OR REPLACE INTO faction_standings 
               (faction_id, faction_name, standing, updated_at)
               VALUES (?, ?, ?, ?)""",
            (standing.faction_id, standing.faction_name, standing.standing, standing.updated_at.isoformat()),
        )
        self.conn.commit()
    
    def adjust_faction_standing(self, faction_id: str, faction_name: str, delta: int) -> FactionStanding:
        """Adjust faction standing by delta. Creates if doesn't exist."""
        existing = self.get_faction_standing(faction_id)
        if existing:
            new_standing = max(-100, min(100, existing.standing + delta))
            existing.standing = new_standing
            self.set_faction_standing(existing)
            return existing
        else:
            standing = FactionStanding(
                faction_id=faction_id,
                faction_name=faction_name,
                standing=max(-100, min(100, delta)),
            )
            self.set_faction_standing(standing)
            return standing
    
    def list_faction_standings(self) -> list[FactionStanding]:
        """List all faction standings."""
        cursor = self.conn.execute(
            "SELECT * FROM faction_standings ORDER BY standing DESC"
        )
        return [
            FactionStanding(
                faction_id=row["faction_id"],
                faction_name=row["faction_name"],
                standing=row["standing"],
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in cursor
        ]
    
    # === NPC Death Operations ===
    
    def record_npc_death(self, death: NPCDeath) -> None:
        """Record an NPC death."""
        self.conn.execute(
            """INSERT INTO npc_deaths 
               (id, npc_name, npc_id, location, cause, campaign_id, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (death.id, death.npc_name, death.npc_id, death.location, 
             death.cause, death.campaign_id, death.timestamp.isoformat()),
        )
        self.conn.commit()
    
    def is_npc_dead(self, npc_name: str) -> bool:
        """Check if an NPC (by name) has died in any campaign."""
        cursor = self.conn.execute(
            "SELECT 1 FROM npc_deaths WHERE npc_name = ? LIMIT 1",
            (npc_name,)
        )
        return cursor.fetchone() is not None
    
    def get_npc_death(self, npc_name: str) -> Optional[NPCDeath]:
        """Get death record for an NPC."""
        cursor = self.conn.execute(
            "SELECT * FROM npc_deaths WHERE npc_name = ? ORDER BY timestamp DESC LIMIT 1",
            (npc_name,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return NPCDeath(
            id=row["id"],
            npc_name=row["npc_name"],
            npc_id=row["npc_id"],
            location=row["location"],
            cause=row["cause"],
            campaign_id=row["campaign_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )
    
    def list_npc_deaths(self, limit: int = 100) -> list[NPCDeath]:
        """List recent NPC deaths."""
        cursor = self.conn.execute(
            "SELECT * FROM npc_deaths ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return [
            NPCDeath(
                id=row["id"],
                npc_name=row["npc_name"],
                npc_id=row["npc_id"],
                location=row["location"],
                cause=row["cause"],
                campaign_id=row["campaign_id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
            )
            for row in cursor
        ]
    
    # === World Event Operations ===
    
    def record_world_event(self, event: WorldEvent) -> None:
        """Record a world event."""
        self.conn.execute(
            """INSERT INTO world_events 
               (id, event_type, title, description, location, campaign_id, timestamp, data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (event.id, event.event_type, event.title, event.description,
             event.location, event.campaign_id, event.timestamp.isoformat(),
             json.dumps(event.data)),
        )
        self.conn.commit()
    
    def list_world_events(self, event_type: Optional[str] = None, limit: int = 100) -> list[WorldEvent]:
        """List world events, optionally filtered by type."""
        if event_type:
            cursor = self.conn.execute(
                "SELECT * FROM world_events WHERE event_type = ? ORDER BY timestamp DESC LIMIT ?",
                (event_type, limit)
            )
        else:
            cursor = self.conn.execute(
                "SELECT * FROM world_events ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
        return [
            WorldEvent(
                id=row["id"],
                event_type=row["event_type"],
                title=row["title"],
                description=row["description"],
                location=row["location"],
                campaign_id=row["campaign_id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                data=json.loads(row["data"]),
            )
            for row in cursor
        ]
    
    def get_world_history_summary(self, limit: int = 10) -> str:
        """Get a summary of recent world history for LLM context."""
        events = self.list_world_events(limit=limit)
        deaths = self.list_npc_deaths(limit=5)
        factions = self.list_faction_standings()
        
        summary_parts = []
        
        if events:
            summary_parts.append("Recent world events:")
            for event in events[:5]:
                summary_parts.append(f"- {event.title}: {event.description}")
        
        if deaths:
            summary_parts.append("\nFallen NPCs:")
            for death in deaths:
                summary_parts.append(f"- {death.npc_name} died at {death.location} ({death.cause})")
        
        if factions:
            summary_parts.append("\nFaction standings:")
            for f in factions:
                if f.standing >= 50:
                    status = "allied"
                elif f.standing >= 0:
                    status = "neutral"
                elif f.standing >= -50:
                    status = "unfriendly"
                else:
                    status = "hostile"
                summary_parts.append(f"- {f.faction_name}: {status} ({f.standing:+d})")
        
        return "\n".join(summary_parts) if summary_parts else "No recorded world history."
    
    # === Export/Import ===
    
    def export_all(self) -> dict:
        """Export entire world state."""
        return {
            "factions": [f.to_dict() for f in self.list_faction_standings()],
            "npc_deaths": [d.to_dict() for d in self.list_npc_deaths(limit=1000)],
            "world_events": [e.to_dict() for e in self.list_world_events(limit=1000)],
        }
    
    def import_all(self, data: dict) -> None:
        """Import world state from exported data."""
        for f_data in data.get("factions", []):
            self.set_faction_standing(FactionStanding.from_dict(f_data))
        
        for d_data in data.get("npc_deaths", []):
            death = NPCDeath.from_dict(d_data)
            # Skip if already exists
            if not self.is_npc_dead(death.npc_name):
                self.record_npc_death(death)
        
        for e_data in data.get("world_events", []):
            event = WorldEvent.from_dict(e_data)
            self.record_world_event(event)


def get_world_state_path() -> Path:
    """Get default path for world state database."""
    return Path.home() / ".config" / "reverie" / "world_state.db"


def open_world_state() -> WorldStateDB:
    """Open the world state database at the default location."""
    return WorldStateDB.open(get_world_state_path())

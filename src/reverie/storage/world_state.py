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
class NPCMemoryRecord:
    """Persistent memory of interactions with a specific NPC across campaigns."""
    id: str
    npc_name: str  # Canonical NPC name for matching across campaigns
    relationship_score: int  # -100 to +100
    interaction_summary: str  # Brief summary of past interactions
    last_interaction_type: str  # friendly, hostile, trade, quest, etc.
    gifts_received: int  # Count of gifts
    promises_kept: int
    promises_broken: int
    campaign_id: str  # Last campaign this interaction happened
    timestamp: datetime = field(default_factory=datetime.now)
    memorable_events: list[str] = field(default_factory=list)  # Key moments
    
    @classmethod
    def create(
        cls,
        npc_name: str,
        campaign_id: str,
        relationship_score: int = 0,
        interaction_summary: str = "",
        last_interaction_type: str = "neutral",
    ) -> "NPCMemoryRecord":
        return cls(
            id=str(uuid4()),
            npc_name=npc_name,
            relationship_score=relationship_score,
            interaction_summary=interaction_summary,
            last_interaction_type=last_interaction_type,
            gifts_received=0,
            promises_kept=0,
            promises_broken=0,
            campaign_id=campaign_id,
        )
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "npc_name": self.npc_name,
            "relationship_score": self.relationship_score,
            "interaction_summary": self.interaction_summary,
            "last_interaction_type": self.last_interaction_type,
            "gifts_received": self.gifts_received,
            "promises_kept": self.promises_kept,
            "promises_broken": self.promises_broken,
            "campaign_id": self.campaign_id,
            "timestamp": self.timestamp.isoformat(),
            "memorable_events": self.memorable_events,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "NPCMemoryRecord":
        return cls(
            id=data["id"],
            npc_name=data["npc_name"],
            relationship_score=data.get("relationship_score", 0),
            interaction_summary=data.get("interaction_summary", ""),
            last_interaction_type=data.get("last_interaction_type", "neutral"),
            gifts_received=data.get("gifts_received", 0),
            promises_kept=data.get("promises_kept", 0),
            promises_broken=data.get("promises_broken", 0),
            campaign_id=data["campaign_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            memorable_events=data.get("memorable_events", []),
        )
    
    def get_memory_context(self) -> str:
        """Get context string for LLM dialogue generation."""
        parts = []
        
        if self.relationship_score >= 50:
            parts.append(f"You are old friends with the player (score: {self.relationship_score})")
        elif self.relationship_score >= 10:
            parts.append(f"You have a positive history with the player (score: {self.relationship_score})")
        elif self.relationship_score <= -50:
            parts.append(f"You are enemies with the player (score: {self.relationship_score})")
        elif self.relationship_score <= -10:
            parts.append(f"You have a negative history with the player (score: {self.relationship_score})")
        
        if self.interaction_summary:
            parts.append(f"Past interactions: {self.interaction_summary}")
        
        if self.memorable_events:
            parts.append(f"Key moments: {'; '.join(self.memorable_events[-3:])}")
        
        if self.promises_broken > 0:
            parts.append(f"The player broke {self.promises_broken} promise(s) to you")
        if self.promises_kept > 0:
            parts.append(f"The player kept {self.promises_kept} promise(s) to you")
        if self.gifts_received > 0:
            parts.append(f"The player gave you {self.gifts_received} gift(s)")
        
        return "\n".join(parts) if parts else "No prior history with this player."


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

CREATE TABLE IF NOT EXISTS npc_memories (
    id TEXT PRIMARY KEY,
    npc_name TEXT NOT NULL UNIQUE,
    relationship_score INTEGER NOT NULL DEFAULT 0,
    interaction_summary TEXT NOT NULL DEFAULT '',
    last_interaction_type TEXT NOT NULL DEFAULT 'neutral',
    gifts_received INTEGER NOT NULL DEFAULT 0,
    promises_kept INTEGER NOT NULL DEFAULT 0,
    promises_broken INTEGER NOT NULL DEFAULT 0,
    campaign_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    memorable_events TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_npc_deaths_name ON npc_deaths(npc_name);
CREATE INDEX IF NOT EXISTS idx_world_events_type ON world_events(event_type);
CREATE INDEX IF NOT EXISTS idx_world_events_timestamp ON world_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_npc_memories_name ON npc_memories(npc_name);
CREATE INDEX IF NOT EXISTS idx_npc_memories_score ON npc_memories(relationship_score);
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
    
    # === NPC Memory Operations ===
    
    def get_npc_memory(self, npc_name: str) -> Optional[NPCMemoryRecord]:
        """Get persistent memory for an NPC by name."""
        cursor = self.conn.execute(
            "SELECT * FROM npc_memories WHERE npc_name = ?",
            (npc_name,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return NPCMemoryRecord(
            id=row["id"],
            npc_name=row["npc_name"],
            relationship_score=row["relationship_score"],
            interaction_summary=row["interaction_summary"],
            last_interaction_type=row["last_interaction_type"],
            gifts_received=row["gifts_received"],
            promises_kept=row["promises_kept"],
            promises_broken=row["promises_broken"],
            campaign_id=row["campaign_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            memorable_events=json.loads(row["memorable_events"]),
        )
    
    def save_npc_memory(self, memory: NPCMemoryRecord) -> None:
        """Save or update NPC memory."""
        memory.timestamp = datetime.now()
        self.conn.execute(
            """INSERT OR REPLACE INTO npc_memories 
               (id, npc_name, relationship_score, interaction_summary, 
                last_interaction_type, gifts_received, promises_kept, 
                promises_broken, campaign_id, timestamp, memorable_events)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (memory.id, memory.npc_name, memory.relationship_score,
             memory.interaction_summary, memory.last_interaction_type,
             memory.gifts_received, memory.promises_kept, memory.promises_broken,
             memory.campaign_id, memory.timestamp.isoformat(),
             json.dumps(memory.memorable_events)),
        )
        self.conn.commit()
    
    def update_npc_memory(
        self,
        npc_name: str,
        campaign_id: str,
        relationship_delta: int = 0,
        interaction_type: Optional[str] = None,
        summary_addition: Optional[str] = None,
        memorable_event: Optional[str] = None,
        gift_given: bool = False,
        promise_kept: bool = False,
        promise_broken: bool = False,
    ) -> NPCMemoryRecord:
        """Update NPC memory with new interaction. Creates if doesn't exist."""
        existing = self.get_npc_memory(npc_name)
        
        if existing:
            # Update existing record
            existing.relationship_score = max(-100, min(100, 
                existing.relationship_score + relationship_delta))
            existing.campaign_id = campaign_id
            
            if interaction_type:
                existing.last_interaction_type = interaction_type
            
            if summary_addition:
                if existing.interaction_summary:
                    existing.interaction_summary = f"{existing.interaction_summary}; {summary_addition}"
                else:
                    existing.interaction_summary = summary_addition
            
            if memorable_event:
                existing.memorable_events.append(memorable_event)
                # Keep only last 10 memorable events
                existing.memorable_events = existing.memorable_events[-10:]
            
            if gift_given:
                existing.gifts_received += 1
            if promise_kept:
                existing.promises_kept += 1
            if promise_broken:
                existing.promises_broken += 1
            
            self.save_npc_memory(existing)
            return existing
        else:
            # Create new record
            memory = NPCMemoryRecord.create(
                npc_name=npc_name,
                campaign_id=campaign_id,
                relationship_score=max(-100, min(100, relationship_delta)),
                interaction_summary=summary_addition or "",
                last_interaction_type=interaction_type or "neutral",
            )
            if memorable_event:
                memory.memorable_events.append(memorable_event)
            if gift_given:
                memory.gifts_received = 1
            if promise_kept:
                memory.promises_kept = 1
            if promise_broken:
                memory.promises_broken = 1
            
            self.save_npc_memory(memory)
            return memory
    
    def list_npc_memories(self, min_score: Optional[int] = None, limit: int = 100) -> list[NPCMemoryRecord]:
        """List NPC memories, optionally filtered by minimum relationship score."""
        if min_score is not None:
            cursor = self.conn.execute(
                "SELECT * FROM npc_memories WHERE relationship_score >= ? ORDER BY relationship_score DESC LIMIT ?",
                (min_score, limit)
            )
        else:
            cursor = self.conn.execute(
                "SELECT * FROM npc_memories ORDER BY relationship_score DESC LIMIT ?",
                (limit,)
            )
        return [
            NPCMemoryRecord(
                id=row["id"],
                npc_name=row["npc_name"],
                relationship_score=row["relationship_score"],
                interaction_summary=row["interaction_summary"],
                last_interaction_type=row["last_interaction_type"],
                gifts_received=row["gifts_received"],
                promises_kept=row["promises_kept"],
                promises_broken=row["promises_broken"],
                campaign_id=row["campaign_id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                memorable_events=json.loads(row["memorable_events"]),
            )
            for row in cursor
        ]
    
    def get_npc_memory_context(self, npc_name: str) -> str:
        """Get memory context for LLM dialogue generation."""
        memory = self.get_npc_memory(npc_name)
        if memory is None:
            return "No prior history with this player."
        return memory.get_memory_context()
    
    def get_allies_and_enemies(self) -> tuple[list[str], list[str]]:
        """Get lists of ally and enemy NPC names based on relationship scores."""
        allies_cursor = self.conn.execute(
            "SELECT npc_name FROM npc_memories WHERE relationship_score >= 25 ORDER BY relationship_score DESC"
        )
        enemies_cursor = self.conn.execute(
            "SELECT npc_name FROM npc_memories WHERE relationship_score <= -25 ORDER BY relationship_score ASC"
        )
        allies = [row["npc_name"] for row in allies_cursor]
        enemies = [row["npc_name"] for row in enemies_cursor]
        return allies, enemies
    
    def get_world_history_summary(self, limit: int = 10) -> str:
        """Get a summary of recent world history for LLM context."""
        events = self.list_world_events(limit=limit)
        deaths = self.list_npc_deaths(limit=5)
        factions = self.list_faction_standings()
        allies, enemies = self.get_allies_and_enemies()
        
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
        
        if allies:
            summary_parts.append(f"\nAllied NPCs: {', '.join(allies[:5])}")
        
        if enemies:
            summary_parts.append(f"\nHostile NPCs: {', '.join(enemies[:5])}")
        
        return "\n".join(summary_parts) if summary_parts else "No recorded world history."
    
    # === Export/Import ===
    
    def export_all(self) -> dict:
        """Export entire world state."""
        return {
            "factions": [f.to_dict() for f in self.list_faction_standings()],
            "npc_deaths": [d.to_dict() for d in self.list_npc_deaths(limit=1000)],
            "world_events": [e.to_dict() for e in self.list_world_events(limit=1000)],
            "npc_memories": [m.to_dict() for m in self.list_npc_memories(limit=1000)],
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
        
        for m_data in data.get("npc_memories", []):
            memory = NPCMemoryRecord.from_dict(m_data)
            # Only import if not already exists
            if self.get_npc_memory(memory.npc_name) is None:
                self.save_npc_memory(memory)


def get_world_state_path() -> Path:
    """Get default path for world state database."""
    return Path.home() / ".config" / "reverie" / "world_state.db"


def open_world_state() -> WorldStateDB:
    """Open the world state database at the default location."""
    return WorldStateDB.open(get_world_state_path())

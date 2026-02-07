"""Data models for storage."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from uuid import uuid4


@dataclass
class Campaign:
    """A campaign save file."""
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    character_id: Optional[str] = None
    current_location_id: Optional[str] = None
    playtime_seconds: int = 0
    
    @classmethod
    def create(cls, name: str) -> "Campaign":
        """Create a new campaign."""
        now = datetime.now()
        return cls(
            id=str(uuid4()),
            name=name,
            created_at=now,
            updated_at=now,
        )
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "character_id": self.character_id,
            "current_location_id": self.current_location_id,
            "playtime_seconds": self.playtime_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Campaign":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            character_id=data.get("character_id"),
            current_location_id=data.get("current_location_id"),
            playtime_seconds=data.get("playtime_seconds", 0),
        )


@dataclass
class CharacterRecord:
    """Character storage record."""
    id: str
    campaign_id: str
    name: str
    data: dict = field(default_factory=dict)  # Full character data as JSON
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "name": self.name,
            "data": self.data,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CharacterRecord":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            campaign_id=data["campaign_id"],
            name=data["name"],
            data=data.get("data", {}),
        )


@dataclass
class WorldElementRecord:
    """World element storage record."""
    id: str
    campaign_id: str
    element_type: str
    name: str
    data: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "element_type": self.element_type,
            "name": self.name,
            "data": self.data,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "WorldElementRecord":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            campaign_id=data["campaign_id"],
            element_type=data["element_type"],
            name=data["name"],
            data=data.get("data", {}),
        )


@dataclass
class NPCRecord:
    """NPC storage record."""
    id: str
    campaign_id: str
    name: str
    location_id: Optional[str] = None
    data: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "name": self.name,
            "location_id": self.location_id,
            "data": self.data,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "NPCRecord":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            campaign_id=data["campaign_id"],
            name=data["name"],
            location_id=data.get("location_id"),
            data=data.get("data", {}),
        )


@dataclass
class QuestRecord:
    """Quest storage record."""
    id: str
    campaign_id: str
    title: str
    status: str = "active"
    data: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "title": self.title,
            "status": self.status,
            "data": self.data,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "QuestRecord":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            campaign_id=data["campaign_id"],
            title=data["title"],
            status=data.get("status", "active"),
            data=data.get("data", {}),
        )


@dataclass
class EventRecord:
    """Event/history storage record."""
    id: str
    campaign_id: str
    timestamp: datetime
    event_type: str
    description: str
    data: dict = field(default_factory=dict)
    
    @classmethod
    def create(cls, campaign_id: str, event_type: str, description: str, data: Optional[dict] = None) -> "EventRecord":
        """Create a new event."""
        return cls(
            id=str(uuid4()),
            campaign_id=campaign_id,
            timestamp=datetime.now(),
            event_type=event_type,
            description=description,
            data=data or {},
        )
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "description": self.description,
            "data": self.data,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EventRecord":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            campaign_id=data["campaign_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=data["event_type"],
            description=data["description"],
            data=data.get("data", {}),
        )

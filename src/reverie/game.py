"""Game state management for Reverie.

State management, context building, and persistence.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from uuid import uuid4

from .character import Character, Stats, Equipment, PlayerClass, DangerLevel as CharDangerLevel
from .world import Location, WorldElement, ElementType
from .npc import NPC, NPCMemory, Disposition
from .quest import Quest, QuestStatus
from .combat import CombatState, CombatStatus
from .storage.database import Database
from .storage.models import (
    Campaign,
    CharacterRecord,
    WorldElementRecord,
    NPCRecord,
    QuestRecord,
    EventRecord,
)


class EventType:
    """Event type constants for history tracking."""
    NARRATION = "narration"
    PLAYER_ACTION = "player_action"
    NPC_DIALOGUE = "npc_dialogue"
    COMBAT_START = "combat_start"
    COMBAT_END = "combat_end"
    QUEST_START = "quest_start"
    QUEST_COMPLETE = "quest_complete"
    QUEST_FAIL = "quest_fail"
    LOCATION_CHANGE = "location_change"
    ITEM_ACQUIRED = "item_acquired"
    ITEM_USED = "item_used"
    LEVEL_UP = "level_up"
    DISCOVERY = "discovery"


@dataclass
class HistoryEntry:
    """A single entry in the game history."""
    id: str
    timestamp: datetime
    event_type: str
    description: str
    data: dict = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        event_type: str,
        description: str,
        data: Optional[dict] = None,
    ) -> "HistoryEntry":
        """Create a new history entry."""
        return cls(
            id=str(uuid4()),
            timestamp=datetime.now(),
            event_type=event_type,
            description=description,
            data=data or {},
        )
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "description": self.description,
            "data": self.data,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=data["event_type"],
            description=data["description"],
            data=data.get("data", {}),
        )


@dataclass
class GameState:
    """Complete game state for a session."""
    campaign: Campaign
    character: Character
    location: Optional[Location] = None
    npcs_present: list[NPC] = field(default_factory=list)
    active_quest: Optional[Quest] = None
    combat_state: Optional[CombatState] = None
    history: list[HistoryEntry] = field(default_factory=list)
    
    # Additional state
    discovered_locations: list[str] = field(default_factory=list)
    known_npcs: list[str] = field(default_factory=list)
    flags: dict[str, Any] = field(default_factory=dict)
    
    @property
    def in_combat(self) -> bool:
        """Check if player is in combat."""
        return (
            self.combat_state is not None
            and self.combat_state.status == CombatStatus.ONGOING
        )
    
    @property
    def has_active_quest(self) -> bool:
        """Check if player has an active quest."""
        return (
            self.active_quest is not None
            and self.active_quest.status == QuestStatus.ACTIVE
        )
    
    def get_recent_history(self, count: int = 10) -> list[HistoryEntry]:
        """Get the most recent history entries."""
        return self.history[-count:] if self.history else []
    
    def get_history_by_type(self, event_type: str) -> list[HistoryEntry]:
        """Get history entries of a specific type."""
        return [h for h in self.history if h.event_type == event_type]


def create_game_state(
    campaign: Campaign,
    character: Character,
    location: Optional[Location] = None,
) -> GameState:
    """Create a new game state.
    
    Args:
        campaign: The campaign this state belongs to
        character: The player's character
        location: Optional starting location
        
    Returns:
        A new GameState instance
    """
    state = GameState(
        campaign=campaign,
        character=character,
        location=location,
        npcs_present=[],
        active_quest=None,
        combat_state=None,
        history=[],
        discovered_locations=[],
        known_npcs=[],
        flags={},
    )
    
    # Add starting location to discovered
    if location:
        state.discovered_locations.append(location.id)
    
    # Add initial history entry
    add_to_history(
        state,
        EventType.NARRATION,
        f"{character.name} begins their adventure.",
        {"location_id": location.id if location else None},
    )
    
    return state


def add_to_history(
    state: GameState,
    event_type: str,
    description: str,
    data: Optional[dict] = None,
) -> HistoryEntry:
    """Add an event to the game history.
    
    Args:
        state: The game state to update
        event_type: Type of event (see EventType constants)
        description: Human-readable description
        data: Optional additional data
        
    Returns:
        The created history entry
    """
    entry = HistoryEntry.create(event_type, description, data)
    state.history.append(entry)
    return entry


def get_context(state: GameState, history_limit: int = 5) -> dict:
    """Build context dictionary for LLM prompts.
    
    Gathers relevant information from game state for context injection.
    
    Args:
        state: The current game state
        history_limit: Maximum number of history entries to include
        
    Returns:
        Dictionary with context for prompts
    """
    context: dict[str, Any] = {
        "campaign_name": state.campaign.name,
        "character": {
            "name": state.character.name,
            "race": state.character.race,
            "class": state.character.player_class.value,
            "level": state.character.level,
            "danger_level": state.character.danger_level.name,
            "stats": {
                "might": state.character.stats.might,
                "wit": state.character.stats.wit,
                "spirit": state.character.stats.spirit,
            },
            "background": state.character.background,
            "gold": state.character.gold,
        },
        "location": None,
        "npcs_present": [],
        "active_quest": None,
        "in_combat": state.in_combat,
        "recent_history": [],
    }
    
    # Add location context
    if state.location:
        context["location"] = {
            "id": state.location.id,
            "name": state.location.name,
            "description": state.location.description,
            "tags": state.location.tags,
            "exits": state.location.exits,
            "revealed_secrets": state.location.get_revealed_secrets(),
        }
    
    # Add NPC context
    for npc in state.npcs_present:
        npc_data = {
            "id": npc.id,
            "name": npc.name,
            "race": npc.race,
            "occupation": npc.occupation,
            "traits": npc.traits,
            "disposition": npc.disposition.value,
        }
        context["npcs_present"].append(npc_data)
    
    # Add quest context
    if state.active_quest:
        context["active_quest"] = {
            "id": state.active_quest.id,
            "title": state.active_quest.title,
            "hook": state.active_quest.hook,
            "objective": state.active_quest.objective,
            "current_stage": None,
            "status": state.active_quest.status.value,
        }
        # Find current (incomplete) stage
        for i, stage in enumerate(state.active_quest.stages):
            if not stage.completed:
                context["active_quest"]["current_stage"] = {
                    "index": i,
                    "description": stage.description,
                }
                break
    
    # Add combat context
    if state.combat_state:
        enemies = []
        for enemy in state.combat_state.enemies:
            enemies.append({
                "name": enemy.name,
                "danger_level": enemy.danger_level.name,
                "special": enemy.special,
            })
        context["combat"] = {
            "turn": state.combat_state.turn,
            "player_danger": state.combat_state.player_danger.name,
            "enemies": enemies,
            "status": state.combat_state.status.value,
        }
    
    # Add recent history
    recent = state.get_recent_history(history_limit)
    for entry in recent:
        context["recent_history"].append({
            "type": entry.event_type,
            "description": entry.description,
        })
    
    return context


def save_state(state: GameState, db: Database) -> None:
    """Save game state to database.
    
    Persists the current state including character, location,
    NPCs, quests, and history.
    
    Args:
        state: The game state to save
        db: Database instance
    """
    # Update campaign with current location
    state.campaign.current_location_id = (
        state.location.id if state.location else None
    )
    db.save_campaign(state.campaign)
    
    # Save character
    char_record = CharacterRecord(
        id=str(uuid4()) if not state.campaign.character_id else state.campaign.character_id,
        campaign_id=state.campaign.id,
        name=state.character.name,
        data=_serialize_character(state.character),
    )
    # Update campaign with character ID
    if not state.campaign.character_id:
        state.campaign.character_id = char_record.id
        db.save_campaign(state.campaign)
    db.save_character(char_record)
    
    # Save location if present
    if state.location:
        loc_record = WorldElementRecord(
            id=state.location.id,
            campaign_id=state.campaign.id,
            element_type=state.location.element_type.value,
            name=state.location.name,
            data=state.location.to_dict(),
        )
        db.save_world_element(loc_record)
    
    # Save NPCs present
    for npc in state.npcs_present:
        npc_record = NPCRecord(
            id=npc.id,
            campaign_id=state.campaign.id,
            name=npc.name,
            location_id=state.location.id if state.location else None,
            data=npc.to_dict(),
        )
        db.save_npc(npc_record)
    
    # Save active quest
    if state.active_quest:
        quest_record = QuestRecord(
            id=state.active_quest.id,
            campaign_id=state.campaign.id,
            title=state.active_quest.title,
            status=state.active_quest.status.value,
            data=state.active_quest.to_dict(),
        )
        db.save_quest(quest_record)
    
    # Save new history entries (only save those not already in DB)
    existing_events = db.list_events(state.campaign.id, limit=1000)
    existing_ids = {e.id for e in existing_events}
    
    for entry in state.history:
        if entry.id not in existing_ids:
            event_record = EventRecord(
                id=entry.id,
                campaign_id=state.campaign.id,
                timestamp=entry.timestamp,
                event_type=entry.event_type,
                description=entry.description,
                data=entry.data,
            )
            db.save_event(event_record)


def load_state(db: Database, campaign_id: str) -> Optional[GameState]:
    """Load game state from database.
    
    Reconstructs the game state from persisted data.
    
    Args:
        db: Database instance
        campaign_id: ID of the campaign to load
        
    Returns:
        GameState if found, None otherwise
    """
    # Load campaign
    campaign = db.load_campaign(campaign_id)
    if campaign is None:
        return None
    
    # Load character
    char_record = db.get_campaign_character(campaign_id)
    if char_record is None:
        return None
    
    character = _deserialize_character(char_record.data)
    
    # Load current location
    location = None
    if campaign.current_location_id:
        loc_record = db.load_world_element(campaign.current_location_id)
        if loc_record:
            location = Location.from_dict(loc_record.data)
    
    # Load NPCs at current location
    npcs_present = []
    if location:
        npc_records = db.list_npcs(campaign_id, location_id=location.id)
        for record in npc_records:
            npcs_present.append(NPC.from_dict(record.data))
    
    # Load active quest
    active_quest = None
    quest_records = db.list_quests(campaign_id, status="active")
    if quest_records:
        # Use the first active quest
        active_quest = Quest.from_dict(quest_records[0].data)
    
    # Load history
    event_records = db.list_events(campaign_id, limit=100)
    history = []
    for record in reversed(event_records):  # Oldest first
        history.append(HistoryEntry(
            id=record.id,
            timestamp=record.timestamp,
            event_type=record.event_type,
            description=record.description,
            data=record.data,
        ))
    
    # Load discovered locations
    all_locations = db.list_world_elements(campaign_id, element_type="location")
    discovered_locations = [loc.id for loc in all_locations]
    
    # Load known NPCs
    all_npcs = db.list_npcs(campaign_id)
    known_npcs = [npc.id for npc in all_npcs]
    
    return GameState(
        campaign=campaign,
        character=character,
        location=location,
        npcs_present=npcs_present,
        active_quest=active_quest,
        combat_state=None,  # Combat state not persisted between sessions
        history=history,
        discovered_locations=discovered_locations,
        known_npcs=known_npcs,
        flags={},
    )


# Helper functions for character serialization

def _serialize_character(char: Character) -> dict:
    """Serialize character to dictionary."""
    return {
        "name": char.name,
        "race": char.race,
        "player_class": char.player_class.value,
        "stats": {
            "might": char.stats.might,
            "wit": char.stats.wit,
            "spirit": char.stats.spirit,
        },
        "background": char.background,
        "equipment": {
            "weapon": char.equipment.weapon,
            "armor": char.equipment.armor,
            "accessory": char.equipment.accessory,
        },
        "inventory": char.inventory,
        "danger_level": char.danger_level.value,
        "gold": char.gold,
        "xp": char.xp,
        "level": char.level,
    }


def _deserialize_character(data: dict) -> Character:
    """Deserialize character from dictionary."""
    return Character(
        name=data["name"],
        race=data["race"],
        player_class=PlayerClass(data["player_class"]),
        stats=Stats(
            might=data["stats"]["might"],
            wit=data["stats"]["wit"],
            spirit=data["stats"]["spirit"],
        ),
        background=data.get("background", ""),
        equipment=Equipment(
            weapon=data["equipment"].get("weapon"),
            armor=data["equipment"].get("armor"),
            accessory=data["equipment"].get("accessory"),
        ),
        inventory=data.get("inventory", []),
        danger_level=CharDangerLevel(data.get("danger_level", 3)),
        gold=data.get("gold", 50),
        xp=data.get("xp", 0),
        level=data.get("level", 1),
    )

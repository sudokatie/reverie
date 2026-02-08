"""Game state management for Reverie.

State management, context building, and persistence.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from uuid import uuid4

import re
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


# =============================================================================
# Game Loop (Task 12)
# =============================================================================

class CommandType:
    """Command type constants."""
    LOOK = "look"
    GO = "go"
    INVENTORY = "inventory"
    STATS = "stats"
    TALK = "talk"
    HELP = "help"
    QUIT = "quit"
    QUESTS = "quests"
    SAVE = "save"
    ROLL = "roll"
    MAP = "map"
    NPCS = "npcs"


@dataclass
class Game:
    """Main game controller."""
    state: GameState
    db: Database
    llm: Optional[Any] = None  # LLM client (typed as Any to avoid circular import)
    
    def run(self) -> None:
        """Main game loop (for TUI integration)."""
        # This is a placeholder - actual TUI integration in Task 13
        pass


def process_input(game: Game, user_input: str) -> str:
    """Process player input and return response.
    
    Routes to appropriate handler based on game state
    and input type (command vs action).
    
    Args:
        game: The game instance
        user_input: Raw input from player
        
    Returns:
        Response text to display
    """
    user_input = user_input.strip()
    
    if not user_input:
        return "What would you like to do?"
    
    # Check if in combat - combat actions take priority
    if game.state.in_combat:
        return handle_combat_action(game, user_input)
    
    # Check for commands (start with / or are keywords)
    if user_input.startswith("/"):
        return handle_command(game, user_input[1:])
    
    # Check for system commands as plain text
    lower_input = user_input.lower()
    command_keywords = [
        "look", "inventory", "stats", "help", "quit", "quests", "save", "roll", "map", "npcs"
    ]
    if lower_input.split()[0] in command_keywords:
        return handle_command(game, lower_input)
    
    # Check for movement
    if lower_input.startswith("go ") or lower_input in ["north", "south", "east", "west", "up", "down"]:
        direction = lower_input.replace("go ", "").strip()
        return handle_movement(game, direction)
    
    # Check for talking to NPCs
    if lower_input.startswith("talk to ") or lower_input.startswith("speak to "):
        npc_name = re.sub(r"^(talk|speak) to ", "", lower_input)
        return handle_dialogue_start(game, npc_name)
    
    # Default: treat as a free-form action
    return handle_action(game, user_input)


def handle_command(game: Game, command: str) -> str:
    """Handle a system command.
    
    Commands are meta-actions like looking, checking inventory,
    saving, or quitting.
    
    Args:
        game: The game instance
        command: Command text (without leading /)
        
    Returns:
        Response text
    """
    parts = command.lower().split()
    cmd = parts[0] if parts else ""
    args = parts[1:] if len(parts) > 1 else []
    
    if cmd == CommandType.LOOK:
        return _cmd_look(game)
    elif cmd == CommandType.INVENTORY:
        return _cmd_inventory(game)
    elif cmd == CommandType.STATS:
        return _cmd_stats(game)
    elif cmd == CommandType.QUESTS:
        return _cmd_quests(game)
    elif cmd == CommandType.HELP:
        return _cmd_help()
    elif cmd == CommandType.SAVE:
        return _cmd_save(game)
    elif cmd == CommandType.QUIT:
        return "Goodbye, adventurer!"
    elif cmd == CommandType.GO and args:
        return handle_movement(game, args[0])
    elif cmd == CommandType.TALK and args:
        npc_name = " ".join(args)
        return handle_dialogue_start(game, npc_name)
    elif cmd == CommandType.ROLL:
        stat = args[0] if args else None
        return _cmd_roll(game, stat)
    elif cmd == CommandType.MAP:
        return _cmd_map(game)
    elif cmd == CommandType.NPCS:
        return _cmd_npcs(game)
    else:
        return f"Unknown command: {cmd}. Type 'help' for available commands."


def handle_action(game: Game, action: str) -> str:
    """Handle a free-form player action.
    
    Processes narrative actions using the LLM.
    
    Args:
        game: The game instance
        action: Player's described action
        
    Returns:
        Narration response
    """
    # Log the action
    add_to_history(
        game.state,
        EventType.PLAYER_ACTION,
        action,
    )
    
    # If no LLM, provide a simple response
    if game.llm is None:
        return f"You attempt to {action.lower()}..."
    
    # Build context and generate response
    context = get_context(game.state)
    prompt = f"""You are the dungeon master. The player attempts: "{action}"

Context:
- Location: {context['location']['name'] if context['location'] else 'Unknown'}
- NPCs present: {', '.join(n['name'] for n in context['npcs_present']) or 'None'}

Describe what happens in 2-3 sentences. Be creative but consistent with the world."""

    try:
        response = game.llm.generate(prompt)
        add_to_history(game.state, EventType.NARRATION, response)
        return response
    except Exception:
        return f"You attempt to {action.lower()}. The outcome is uncertain..."


def handle_dialogue(game: Game, npc: NPC, player_input: str) -> str:
    """Handle dialogue with an NPC.
    
    Args:
        game: The game instance
        npc: The NPC being spoken to
        player_input: What the player says
        
    Returns:
        NPC's response
    """
    # Log the conversation
    add_to_history(
        game.state,
        EventType.NPC_DIALOGUE,
        f"Player to {npc.name}: {player_input}",
        {"npc_id": npc.id},
    )
    
    # If no LLM, provide a simple response
    if game.llm is None:
        return f'{npc.name} considers your words. "That is interesting," they say.'
    
    # Build NPC context
    context = get_context(game.state)
    npc_context = f"""NPC: {npc.name}
Race: {npc.race}
Occupation: {npc.occupation}
Traits: {', '.join(npc.traits)}
Motivation: {npc.motivation}
Disposition: {npc.disposition.value}"""

    prompt = f"""You are roleplaying as {npc.name}, an NPC in a fantasy RPG.

{npc_context}

The player says: "{player_input}"

Respond in character as {npc.name}. Keep the response to 2-3 sentences."""

    try:
        response = game.llm.generate(prompt)
        # Add to NPC memory
        npc.memory.add_conversation(f"Player: {player_input} | {npc.name}: {response[:100]}...")
        add_to_history(
            game.state,
            EventType.NPC_DIALOGUE,
            f"{npc.name}: {response}",
            {"npc_id": npc.id},
        )
        return f'{npc.name}: "{response}"'
    except Exception:
        return f'{npc.name}: "I... need a moment to think."'


def handle_combat_action(game: Game, action: str) -> str:
    """Handle a combat action.
    
    Args:
        game: The game instance
        action: The combat action (attack, defend, retreat, etc.)
        
    Returns:
        Combat result narration
    """
    if game.state.combat_state is None:
        return "You are not in combat."
    
    combat = game.state.combat_state
    action_lower = action.lower().strip()
    
    # Parse action
    if action_lower.startswith("attack") or action_lower == "a":
        result = _combat_attack(game)
    elif action_lower.startswith("defend") or action_lower == "d":
        result = _combat_defend(game)
    elif action_lower.startswith("retreat") or action_lower.startswith("flee") or action_lower == "r":
        result = _combat_retreat(game)
    else:
        result = _combat_generic_action(game, action)
    
    # Check for combat end
    if combat.all_enemies_defeated():
        combat.status = CombatStatus.VICTORY
        add_to_history(game.state, EventType.COMBAT_END, "Combat ended in victory!")
        result += "\n\nVictory! All enemies have been defeated."
        game.state.combat_state = None
    elif combat.player_defeated():
        combat.status = CombatStatus.DEFEAT
        add_to_history(game.state, EventType.COMBAT_END, "Combat ended in defeat.")
        result += "\n\nYou have been defeated..."
        game.state.combat_state = None
    
    return result


def check_triggers(game: Game) -> list[str]:
    """Check for triggered events.
    
    Scans game state for conditions that trigger events
    (quest completion, random encounters, etc.)
    
    Args:
        game: The game instance
        
    Returns:
        List of triggered event descriptions
    """
    triggered = []
    
    # Check quest stage triggers
    if game.state.active_quest and game.state.location:
        quest = game.state.active_quest
        current_stage = quest.get_current_stage()
        if current_stage:
            # Check if location matches stage requirement
            location_tags = game.state.location.tags
            stage_lower = current_stage.description.lower()
            
            for tag in location_tags:
                if tag.lower() in stage_lower:
                    triggered.append(f"Quest objective progress: {current_stage.description}")
                    break
    
    # Check level up
    char = game.state.character
    xp_needed = char.level * 100
    if char.xp >= xp_needed:
        char.level += 1
        char.xp -= xp_needed
        triggered.append(f"Level up! You are now level {char.level}.")
        add_to_history(
            game.state,
            EventType.LEVEL_UP,
            f"Reached level {char.level}",
        )
    
    # Check for low health warning
    if char.danger_level == CharDangerLevel.CRITICAL:
        triggered.append("Warning: You are critically wounded!")
    
    return triggered


# =============================================================================
# Command Implementations
# =============================================================================

def _cmd_look(game: Game) -> str:
    """Look around the current location."""
    if game.state.location is None:
        return "You are nowhere in particular. This is concerning."
    
    loc = game.state.location
    parts = [f"**{loc.name}**", loc.description]
    
    # Exits
    if loc.exits:
        exits_str = ", ".join(loc.exits.keys())
        parts.append(f"Exits: {exits_str}")
    
    # NPCs
    if game.state.npcs_present:
        npc_names = [npc.name for npc in game.state.npcs_present]
        parts.append(f"You see: {', '.join(npc_names)}")
    
    # Revealed secrets
    secrets = loc.get_revealed_secrets()
    if secrets:
        parts.append(f"You notice: {'; '.join(secrets)}")
    
    return "\n\n".join(parts)


def _cmd_inventory(game: Game) -> str:
    """Show player inventory."""
    char = game.state.character
    parts = ["**Inventory**"]
    
    # Equipment
    eq = char.equipment
    if eq.weapon:
        parts.append(f"Weapon: {eq.weapon}")
    if eq.armor:
        parts.append(f"Armor: {eq.armor}")
    if eq.accessory:
        parts.append(f"Accessory: {eq.accessory}")
    
    # Items
    if char.inventory:
        parts.append(f"Items: {', '.join(char.inventory)}")
    else:
        parts.append("Items: (none)")
    
    parts.append(f"Gold: {char.gold}")
    
    return "\n".join(parts)


def _cmd_stats(game: Game) -> str:
    """Show player stats."""
    char = game.state.character
    return f"""**{char.name}** - Level {char.level} {char.player_class.value}
Race: {char.race}
Health: {char.danger_level.name}
XP: {char.xp}/{char.level * 100}

Stats:
  Might: {char.stats.might}
  Wit: {char.stats.wit}
  Spirit: {char.stats.spirit}"""


def _cmd_quests(game: Game) -> str:
    """Show active quests."""
    if not game.state.active_quest:
        return "You have no active quests."
    
    quest = game.state.active_quest
    completed, total = quest.get_progress()
    current = quest.get_current_stage()
    
    parts = [
        f"**{quest.title}**",
        quest.objective,
        f"Progress: {completed}/{total} stages",
    ]
    
    if current:
        parts.append(f"Current: {current.description}")
    
    return "\n".join(parts)


def _cmd_help() -> str:
    """Show help text."""
    return """**Commands**
look - Examine your surroundings
go <direction> - Move in a direction (north, south, east, west, etc.)
inventory - Check your belongings
stats - View your character stats
quests - View active quests
talk <name> - Speak with an NPC
roll [stat] - Roll a d20 (optionally with stat modifier)
map - Show discovered locations
npcs - Show known NPCs and relationships
save - Save your progress
help - Show this help
quit - Leave the game

You can also type actions naturally, like "search the room" or "pick up the sword"."""


def _cmd_save(game: Game) -> str:
    """Save the game."""
    try:
        save_state(game.state, game.db)
        return "Game saved."
    except Exception as e:
        return f"Failed to save: {e}"


def _cmd_roll(game: Game, stat: Optional[str] = None) -> str:
    """Roll a d20, optionally with a stat modifier.
    
    Args:
        game: The game instance
        stat: Optional stat name (might, wit, spirit)
        
    Returns:
        Roll result description
    """
    import random
    from .config import load_config
    
    roll = random.randint(1, 20)
    config = load_config()
    verbose = config.gameplay.verbose_rolls
    
    if stat:
        stat_lower = stat.lower()
        if stat_lower in ("might", "wit", "spirit"):
            modifier = game.state.character.stats.modifier(stat_lower)
            total = roll + modifier
            
            if verbose:
                sign = "+" if modifier >= 0 else ""
                return f"Rolling {stat.capitalize()}: d20({roll}) {sign}{modifier} = **{total}**"
            else:
                return f"Rolling {stat.capitalize()}: **{total}**"
        else:
            return f"Unknown stat: {stat}. Valid stats: might, wit, spirit"
    else:
        if verbose:
            return f"Rolling d20: **{roll}**"
        else:
            return f"Roll: **{roll}**"


def _cmd_map(game: Game) -> str:
    """Show discovered locations."""
    if not game.state.discovered_locations:
        return "You haven't discovered any locations yet."
    
    parts = ["**Discovered Locations**"]
    
    # Load location names from database
    if game.db:
        for loc_id in game.state.discovered_locations:
            loc_record = game.db.load_world_element(loc_id)
            if loc_record:
                name = loc_record.name
                # Mark current location
                if game.state.location and game.state.location.id == loc_id:
                    parts.append(f"  * {name} (current)")
                else:
                    parts.append(f"  - {name}")
            else:
                parts.append(f"  - Unknown location")
    else:
        parts.append(f"  {len(game.state.discovered_locations)} locations discovered")
    
    return "\n".join(parts)


def _cmd_npcs(game: Game) -> str:
    """Show known NPCs and their relationships."""
    if not game.state.known_npcs:
        return "You haven't met anyone yet."
    
    parts = ["**Known NPCs**"]
    
    # Load NPC data from database
    if game.db:
        npc_records = game.db.list_npcs(game.state.campaign.id)
        for record in npc_records:
            npc = NPC.from_dict(record.data)
            disposition_str = npc.disposition.value.capitalize()
            parts.append(f"  - {npc.name} ({npc.occupation}): {disposition_str}")
    else:
        parts.append(f"  {len(game.state.known_npcs)} NPCs known")
    
    return "\n".join(parts)


# =============================================================================
# Movement
# =============================================================================

def handle_movement(game: Game, direction: str) -> str:
    """Handle movement in a direction."""
    if game.state.location is None:
        return "You have nowhere to go from here."
    
    direction = direction.lower()
    exits = game.state.location.exits
    
    if direction not in exits:
        available = ", ".join(exits.keys()) if exits else "none"
        return f"You can't go {direction}. Available exits: {available}"
    
    # Get destination ID
    dest_id = exits[direction]
    
    # Try to load destination
    if game.db:
        dest_record = game.db.load_world_element(dest_id)
        if dest_record:
            new_location = Location.from_dict(dest_record.data)
            old_location = game.state.location
            game.state.location = new_location
            
            # Update discovered locations
            if dest_id not in game.state.discovered_locations:
                game.state.discovered_locations.append(dest_id)
            
            # Update NPCs present
            npc_records = game.db.list_npcs(game.state.campaign.id, location_id=dest_id)
            game.state.npcs_present = [NPC.from_dict(r.data) for r in npc_records]
            
            add_to_history(
                game.state,
                EventType.LOCATION_CHANGE,
                f"Traveled {direction} from {old_location.name} to {new_location.name}",
                {"from": old_location.id, "to": new_location.id},
            )
            
            return f"You travel {direction}.\n\n" + _cmd_look(game)
    
    return f"You travel {direction} into the unknown..."


def handle_dialogue_start(game: Game, npc_name: str) -> str:
    """Start dialogue with an NPC."""
    npc_name_lower = npc_name.lower()
    
    for npc in game.state.npcs_present:
        if npc.name.lower() == npc_name_lower or npc_name_lower in npc.name.lower():
            # Found the NPC - set up dialogue mode
            return f'{npc.name} turns to face you. "{_get_npc_greeting(npc)}"'
    
    return f"There is no one named '{npc_name}' here."


def _get_npc_greeting(npc: NPC) -> str:
    """Get an NPC's greeting based on disposition."""
    greetings = {
        Disposition.HOSTILE: "What do YOU want?",
        Disposition.UNFRIENDLY: "Make it quick.",
        Disposition.NEUTRAL: "Can I help you?",
        Disposition.FRIENDLY: "Hello there, friend!",
        Disposition.ALLIED: "My friend! It's good to see you!",
    }
    return greetings.get(npc.disposition, "Yes?")


# =============================================================================
# Combat Actions
# =============================================================================

def _combat_attack(game: Game) -> str:
    """Player attacks."""
    import random
    combat = game.state.combat_state
    if not combat:
        return "Not in combat."
    
    enemies = combat.get_active_enemies()
    if not enemies:
        return "No enemies to attack."
    
    target = enemies[0]  # Attack first enemy
    roll = random.randint(1, 20) + game.state.character.stats.might - 3
    
    if roll >= 10:
        target.take_damage(1)
        result = f"You strike {target.name}! ({target.danger_level.name})"
        combat.add_log(f"Player hits {target.name}")
    else:
        result = f"Your attack misses {target.name}."
        combat.add_log(f"Player misses {target.name}")
    
    # Enemy counterattack
    if not target.is_defeated():
        result += "\n" + _enemy_turn(game)
    
    combat.next_turn()
    return result


def _combat_defend(game: Game) -> str:
    """Player defends."""
    combat = game.state.combat_state
    if not combat:
        return "Not in combat."
    
    combat.add_log("Player defends")
    
    # Reduced enemy damage
    enemies = combat.get_active_enemies()
    if enemies:
        result = "You raise your guard."
        # Enemy attacks with reduced effect
        for enemy in enemies[:1]:  # Only first enemy attacks
            combat.add_log(f"{enemy.name}'s attack is partially blocked")
        result += " The enemy's attack is partially deflected."
    else:
        result = "You defend against nothing."
    
    combat.next_turn()
    return result


def _combat_retreat(game: Game) -> str:
    """Player attempts to retreat."""
    import random
    combat = game.state.combat_state
    if not combat:
        return "Not in combat."
    
    roll = random.randint(1, 20) + game.state.character.stats.spirit - 3
    
    if roll >= combat.retreat_difficulty:
        combat.status = CombatStatus.RETREAT
        add_to_history(game.state, EventType.COMBAT_END, "Fled from combat")
        game.state.combat_state = None
        return "You successfully flee from combat!"
    else:
        result = "You fail to escape!"
        result += "\n" + _enemy_turn(game)
        combat.next_turn()
        return result


def _combat_generic_action(game: Game, action: str) -> str:
    """Handle a generic combat action."""
    combat = game.state.combat_state
    if not combat:
        return "Not in combat."
    
    combat.add_log(f"Player: {action}")
    result = f"You attempt to {action}... "
    
    # Enemy still attacks
    result += "\n" + _enemy_turn(game)
    combat.next_turn()
    return result


def _enemy_turn(game: Game) -> str:
    """Process enemy turn."""
    import random
    combat = game.state.combat_state
    if not combat:
        return ""
    
    enemies = combat.get_active_enemies()
    if not enemies:
        return ""
    
    results = []
    for enemy in enemies:
        roll = random.randint(1, 20)
        if roll >= 8:
            combat.player_take_damage(enemy.damage)
            results.append(f"{enemy.name} hits you! (Now: {combat.player_danger.name})")
            combat.add_log(f"{enemy.name} hits player")
        else:
            results.append(f"{enemy.name}'s attack misses.")
            combat.add_log(f"{enemy.name} misses")
    
    return "\n".join(results)

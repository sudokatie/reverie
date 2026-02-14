"""NPC system for Reverie.

NPCs with memory, relationships, and personality.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
from uuid import uuid4


class Disposition(Enum):
    """NPC disposition toward player."""
    HOSTILE = "hostile"
    UNFRIENDLY = "unfriendly"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    ALLIED = "allied"


@dataclass
class Promise:
    """A promise made by the player to an NPC."""
    description: str
    fulfilled: bool = False


@dataclass
class Gift:
    """A gift given to an NPC."""
    item_name: str
    value: int


@dataclass
class ReputationChange:
    """A change in reputation with an NPC."""
    amount: int  # Positive or negative
    reason: str


@dataclass
class NPCMemory:
    """NPC's memory of interactions with the player."""
    conversations: list[str] = field(default_factory=list)
    promises: list[Promise] = field(default_factory=list)
    gifts: list[Gift] = field(default_factory=list)
    reputation_changes: list[ReputationChange] = field(default_factory=list)

    def add_conversation(self, summary: str) -> None:
        """Add a conversation summary."""
        self.conversations.append(summary)

    def add_promise(self, description: str, fulfilled: bool = False) -> None:
        """Add a promise."""
        self.promises.append(Promise(description=description, fulfilled=fulfilled))

    def fulfill_promise(self, index: int) -> bool:
        """Mark a promise as fulfilled. Returns True if successful."""
        if 0 <= index < len(self.promises):
            self.promises[index].fulfilled = True
            return True
        return False

    def get_unfulfilled_promises(self) -> list[Promise]:
        """Get all unfulfilled promises."""
        return [p for p in self.promises if not p.fulfilled]

    def add_gift(self, item_name: str, value: int) -> None:
        """Record a gift."""
        self.gifts.append(Gift(item_name=item_name, value=value))

    def add_reputation_change(self, amount: int, reason: str) -> None:
        """Record a reputation change."""
        self.reputation_changes.append(ReputationChange(amount=amount, reason=reason))

    def get_total_reputation(self) -> int:
        """Calculate total reputation from all changes."""
        return sum(change.amount for change in self.reputation_changes)

    def get_gift_value_total(self) -> int:
        """Get total value of gifts given."""
        return sum(gift.value for gift in self.gifts)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "conversations": self.conversations,
            "promises": [{"description": p.description, "fulfilled": p.fulfilled} for p in self.promises],
            "gifts": [{"item_name": g.item_name, "value": g.value} for g in self.gifts],
            "reputation_changes": [{"amount": r.amount, "reason": r.reason} for r in self.reputation_changes],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NPCMemory":
        """Deserialize from dictionary."""
        memory = cls()
        memory.conversations = data.get("conversations", [])
        memory.promises = [
            Promise(description=p["description"], fulfilled=p["fulfilled"])
            for p in data.get("promises", [])
        ]
        memory.gifts = [
            Gift(item_name=g["item_name"], value=g["value"])
            for g in data.get("gifts", [])
        ]
        memory.reputation_changes = [
            ReputationChange(amount=r["amount"], reason=r["reason"])
            for r in data.get("reputation_changes", [])
        ]
        return memory


@dataclass
class NPC:
    """A non-player character."""
    id: str
    name: str
    race: str
    occupation: str
    traits: list[str] = field(default_factory=list)  # 2 personality traits
    motivation: str = ""  # What they want
    secret: Optional[str] = None  # Hidden agenda
    disposition: Disposition = Disposition.NEUTRAL
    memory: NPCMemory = field(default_factory=NPCMemory)

    def update_disposition(self, change: int, reason: str) -> Disposition:
        """Update disposition based on change amount.
        
        Args:
            change: Positive improves, negative worsens
            reason: Why the change happened
            
        Returns:
            New disposition
        """
        # Record the change
        self.memory.add_reputation_change(change, reason)
        
        # Calculate new disposition based on total reputation
        total = self.memory.get_total_reputation()
        
        if total <= -10:
            self.disposition = Disposition.HOSTILE
        elif total <= -5:
            self.disposition = Disposition.UNFRIENDLY
        elif total < 5:
            self.disposition = Disposition.NEUTRAL
        elif total < 10:
            self.disposition = Disposition.FRIENDLY
        else:
            self.disposition = Disposition.ALLIED
            
        return self.disposition

    def get_relationship_summary(self) -> str:
        """Get a summary of the NPC's relationship with the player."""
        parts = [f"{self.name} ({self.disposition.value})"]
        
        total_rep = self.memory.get_total_reputation()
        if total_rep != 0:
            parts.append(f"Reputation: {total_rep:+d}")
        
        unfulfilled = self.memory.get_unfulfilled_promises()
        if unfulfilled:
            parts.append(f"Unfulfilled promises: {len(unfulfilled)}")
            
        if self.memory.gifts:
            parts.append(f"Gifts received: {len(self.memory.gifts)}")
            
        if self.memory.conversations:
            parts.append(f"Conversations: {len(self.memory.conversations)}")
            
        return " | ".join(parts)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "race": self.race,
            "occupation": self.occupation,
            "traits": self.traits,
            "motivation": self.motivation,
            "secret": self.secret,
            "disposition": self.disposition.value,
            "memory": self.memory.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NPC":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            race=data["race"],
            occupation=data["occupation"],
            traits=data.get("traits", []),
            motivation=data.get("motivation", ""),
            secret=data.get("secret"),
            disposition=Disposition(data.get("disposition", "neutral")),
            memory=NPCMemory.from_dict(data.get("memory", {})),
        )


# Generation functions

def generate_npc(
    context: Optional[dict[str, Any]] = None,
    llm: Optional[Any] = None,
) -> NPC:
    """Generate a new NPC.
    
    Args:
        context: Optional dict with location, player info, etc.
        llm: Optional LLM client for generating descriptions
        
    Returns:
        A new NPC instance
    """
    context = context or {}
    
    # Defaults or from context
    name = context.get("name", "Unnamed Stranger")
    race = context.get("race", "human")
    occupation = context.get("occupation", "commoner")
    traits = context.get("traits", ["curious", "cautious"])
    motivation = context.get("motivation", "seeking a better life")
    secret = context.get("secret")
    disposition = context.get("disposition", Disposition.NEUTRAL)
    
    if isinstance(disposition, str):
        disposition = Disposition(disposition)
    
    return NPC(
        id=str(uuid4()),
        name=name,
        race=race,
        occupation=occupation,
        traits=traits[:2],  # Max 2 traits
        motivation=motivation,
        secret=secret,
        disposition=disposition,
    )


def update_disposition(npc: NPC, change: int, reason: str) -> Disposition:
    """Update an NPC's disposition toward the player.
    
    Args:
        npc: The NPC to update
        change: Positive improves, negative worsens
        reason: Why the change happened
        
    Returns:
        The new disposition
    """
    return npc.update_disposition(change, reason)


def add_conversation(npc: NPC, summary: str) -> None:
    """Add a conversation summary to NPC memory.
    
    Args:
        npc: The NPC
        summary: Summary of what was discussed
    """
    npc.memory.add_conversation(summary)


def add_promise(npc: NPC, promise: str, fulfilled: bool = False) -> None:
    """Add a promise to NPC memory.
    
    Args:
        npc: The NPC
        promise: Description of the promise
        fulfilled: Whether it's already fulfilled
    """
    npc.memory.add_promise(promise, fulfilled)


def get_relationship_summary(npc: NPC) -> str:
    """Get a summary of the NPC's relationship with the player.
    
    Args:
        npc: The NPC
        
    Returns:
        A formatted string summary
    """
    return npc.get_relationship_summary()


def is_npc_dead_in_world(npc_name: str, world_state: Optional[Any] = None) -> bool:
    """Check if an NPC has died in any previous campaign.
    
    Used to prevent respawning NPCs who were killed in the
    persistent world state.
    
    Args:
        npc_name: The NPC's name to check
        world_state: WorldStateDB instance (optional)
        
    Returns:
        True if the NPC is recorded as dead
    """
    if world_state is None:
        return False
    return world_state.is_npc_dead(npc_name)


def get_npc_death_info(npc_name: str, world_state: Optional[Any] = None) -> Optional[str]:
    """Get information about how an NPC died.
    
    Args:
        npc_name: The NPC's name
        world_state: WorldStateDB instance (optional)
        
    Returns:
        Description of death or None if NPC is alive
    """
    if world_state is None:
        return None
    death = world_state.get_npc_death(npc_name)
    if death is None:
        return None
    return f"{npc_name} died at {death.location}: {death.cause}"

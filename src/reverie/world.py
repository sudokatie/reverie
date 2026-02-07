"""World generation for Reverie.

Lazy generation of regions, settlements, dungeons, and wilderness areas.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
from uuid import uuid4


class ElementType(Enum):
    """Types of world elements."""
    REGION = "region"
    SETTLEMENT = "settlement"
    DUNGEON = "dungeon"
    WILDERNESS = "wilderness"


@dataclass
class WorldElement:
    """Base class for all world elements."""
    id: str
    element_type: ElementType
    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    secrets: list[str] = field(default_factory=list)
    connections: list[str] = field(default_factory=list)  # IDs of connected elements
    revealed_secrets: list[int] = field(default_factory=list)  # Indices of revealed secrets

    def has_tag(self, tag: str) -> bool:
        """Check if element has a specific tag (case-insensitive)."""
        return tag.lower() in [t.lower() for t in self.tags]

    def add_connection(self, element_id: str) -> None:
        """Add a connection to another element."""
        if element_id not in self.connections:
            self.connections.append(element_id)

    def remove_connection(self, element_id: str) -> bool:
        """Remove a connection. Returns True if removed."""
        if element_id in self.connections:
            self.connections.remove(element_id)
            return True
        return False

    def reveal_secret(self, index: int) -> Optional[str]:
        """Reveal a secret by index. Returns the secret text or None."""
        if 0 <= index < len(self.secrets) and index not in self.revealed_secrets:
            self.revealed_secrets.append(index)
            return self.secrets[index]
        return None

    def get_revealed_secrets(self) -> list[str]:
        """Get all revealed secrets."""
        return [self.secrets[i] for i in self.revealed_secrets if i < len(self.secrets)]

    def get_hidden_secret_count(self) -> int:
        """Get count of unrevealed secrets."""
        return len(self.secrets) - len(self.revealed_secrets)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "element_type": self.element_type.value,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "secrets": self.secrets,
            "connections": self.connections,
            "revealed_secrets": self.revealed_secrets,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorldElement":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            element_type=ElementType(data["element_type"]),
            name=data["name"],
            description=data["description"],
            tags=data.get("tags", []),
            secrets=data.get("secrets", []),
            connections=data.get("connections", []),
            revealed_secrets=data.get("revealed_secrets", []),
        )


@dataclass
class Location(WorldElement):
    """A specific location with exits."""
    exits: dict[str, str] = field(default_factory=dict)  # direction -> location_id

    def add_exit(self, direction: str, location_id: str) -> None:
        """Add an exit in a direction."""
        self.exits[direction.lower()] = location_id

    def remove_exit(self, direction: str) -> bool:
        """Remove an exit. Returns True if removed."""
        direction = direction.lower()
        if direction in self.exits:
            del self.exits[direction]
            return True
        return False

    def get_exit_directions(self) -> list[str]:
        """Get all available exit directions."""
        return list(self.exits.keys())

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        data = super().to_dict()
        data["exits"] = self.exits
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Location":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            element_type=ElementType(data["element_type"]),
            name=data["name"],
            description=data["description"],
            tags=data.get("tags", []),
            secrets=data.get("secrets", []),
            connections=data.get("connections", []),
            revealed_secrets=data.get("revealed_secrets", []),
            exits=data.get("exits", {}),
        )


@dataclass
class Region(WorldElement):
    """A region containing settlements and dungeons."""
    climate: str = ""
    terrain: str = ""
    culture: str = ""
    settlements: list[str] = field(default_factory=list)  # Settlement IDs
    dungeons: list[str] = field(default_factory=list)  # Dungeon IDs
    wilderness_areas: list[str] = field(default_factory=list)  # Wilderness IDs

    def add_settlement(self, settlement_id: str) -> None:
        """Add a settlement to this region."""
        if settlement_id not in self.settlements:
            self.settlements.append(settlement_id)
            self.add_connection(settlement_id)

    def add_dungeon(self, dungeon_id: str) -> None:
        """Add a dungeon to this region."""
        if dungeon_id not in self.dungeons:
            self.dungeons.append(dungeon_id)
            self.add_connection(dungeon_id)

    def add_wilderness(self, wilderness_id: str) -> None:
        """Add a wilderness area to this region."""
        if wilderness_id not in self.wilderness_areas:
            self.wilderness_areas.append(wilderness_id)
            self.add_connection(wilderness_id)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        data = super().to_dict()
        data["climate"] = self.climate
        data["terrain"] = self.terrain
        data["culture"] = self.culture
        data["settlements"] = self.settlements
        data["dungeons"] = self.dungeons
        data["wilderness_areas"] = self.wilderness_areas
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Region":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            element_type=ElementType(data["element_type"]),
            name=data["name"],
            description=data["description"],
            tags=data.get("tags", []),
            secrets=data.get("secrets", []),
            connections=data.get("connections", []),
            revealed_secrets=data.get("revealed_secrets", []),
            climate=data.get("climate", ""),
            terrain=data.get("terrain", ""),
            culture=data.get("culture", ""),
            settlements=data.get("settlements", []),
            dungeons=data.get("dungeons", []),
            wilderness_areas=data.get("wilderness_areas", []),
        )


# Generation functions (work with or without LLM)

def generate_region(
    constraints: Optional[dict[str, Any]] = None,
    llm: Optional[Any] = None,
) -> Region:
    """Generate a new region.
    
    Args:
        constraints: Optional dict with keys like 'climate', 'terrain', 'culture'
        llm: Optional LLM client for generating descriptions
        
    Returns:
        A new Region instance
    """
    constraints = constraints or {}
    
    # Default values
    climate = constraints.get("climate", "temperate")
    terrain = constraints.get("terrain", "plains")
    culture = constraints.get("culture", "human kingdom")
    name = constraints.get("name", f"The {terrain.title()} of {culture.split()[0].title()}")
    
    # Generate description (use LLM if available, otherwise default)
    if llm is not None:
        # LLM integration would go here
        description = f"A {climate} {terrain} region dominated by {culture}."
    else:
        description = f"A {climate} {terrain} region dominated by {culture}."
    
    tags = [climate, terrain]
    if "tags" in constraints:
        tags.extend(constraints["tags"])
    
    secrets = constraints.get("secrets", [])
    
    return Region(
        id=str(uuid4()),
        element_type=ElementType.REGION,
        name=name,
        description=description,
        tags=tags,
        secrets=secrets,
        climate=climate,
        terrain=terrain,
        culture=culture,
    )


def generate_settlement(
    region: Region,
    constraints: Optional[dict[str, Any]] = None,
    llm: Optional[Any] = None,
) -> Location:
    """Generate a settlement within a region.
    
    Args:
        region: The parent region
        constraints: Optional dict with keys like 'size', 'government', 'name'
        llm: Optional LLM client for generating descriptions
        
    Returns:
        A new Location instance representing a settlement
    """
    constraints = constraints or {}
    
    size = constraints.get("size", "village")
    government = constraints.get("government", "mayor")
    name = constraints.get("name", f"{size.title()} of the {region.terrain.title()}")
    
    if llm is not None:
        description = f"A {size} governed by a {government} in the {region.name}."
    else:
        description = f"A {size} governed by a {government} in the {region.name}."
    
    tags = [size, "settlement", region.climate]
    if "tags" in constraints:
        tags.extend(constraints["tags"])
    
    secrets = constraints.get("secrets", [])
    
    settlement = Location(
        id=str(uuid4()),
        element_type=ElementType.SETTLEMENT,
        name=name,
        description=description,
        tags=tags,
        secrets=secrets,
    )
    
    # Connect to region
    settlement.add_connection(region.id)
    region.add_settlement(settlement.id)
    
    return settlement


def generate_dungeon(
    region: Region,
    constraints: Optional[dict[str, Any]] = None,
    llm: Optional[Any] = None,
) -> Location:
    """Generate a dungeon within a region.
    
    Args:
        region: The parent region
        constraints: Optional dict with keys like 'theme', 'difficulty', 'boss'
        llm: Optional LLM client for generating descriptions
        
    Returns:
        A new Location instance representing a dungeon
    """
    constraints = constraints or {}
    
    theme = constraints.get("theme", "abandoned")
    difficulty = constraints.get("difficulty", "moderate")
    boss = constraints.get("boss", "guardian")
    name = constraints.get("name", f"The {theme.title()} Depths")
    
    if llm is not None:
        description = f"A {difficulty} difficulty {theme} dungeon guarded by a {boss}."
    else:
        description = f"A {difficulty} difficulty {theme} dungeon guarded by a {boss}."
    
    tags = [theme, "dungeon", difficulty]
    if "tags" in constraints:
        tags.extend(constraints["tags"])
    
    secrets = constraints.get("secrets", ["A hidden treasure room lies beyond the boss."])
    
    dungeon = Location(
        id=str(uuid4()),
        element_type=ElementType.DUNGEON,
        name=name,
        description=description,
        tags=tags,
        secrets=secrets,
    )
    
    # Connect to region
    dungeon.add_connection(region.id)
    region.add_dungeon(dungeon.id)
    
    return dungeon


def generate_wilderness(
    region: Region,
    llm: Optional[Any] = None,
) -> Location:
    """Generate a wilderness area within a region.
    
    Args:
        region: The parent region
        llm: Optional LLM client for generating descriptions
        
    Returns:
        A new Location instance representing wilderness
    """
    # Use region's terrain for wilderness
    terrain = region.terrain
    name = f"The Wild {terrain.title()}"
    
    if llm is not None:
        description = f"Untamed {terrain} stretching across the {region.name}."
    else:
        description = f"Untamed {terrain} stretching across the {region.name}."
    
    tags = [terrain, "wilderness", "dangerous"]
    
    wilderness = Location(
        id=str(uuid4()),
        element_type=ElementType.WILDERNESS,
        name=name,
        description=description,
        tags=tags,
        secrets=["Ancient ruins lie hidden somewhere in the wilds."],
    )
    
    # Connect to region
    wilderness.add_connection(region.id)
    region.add_wilderness(wilderness.id)
    
    return wilderness


def get_connected_locations(
    element_id: str,
    elements: dict[str, WorldElement],
) -> list[WorldElement]:
    """Get all elements connected to a given element.
    
    Args:
        element_id: The ID of the element to check
        elements: Dictionary of all elements by ID
        
    Returns:
        List of connected WorldElement instances
    """
    if element_id not in elements:
        return []
    
    element = elements[element_id]
    return [
        elements[conn_id]
        for conn_id in element.connections
        if conn_id in elements
    ]


def filter_by_tag(
    elements: list[WorldElement],
    tag: str,
) -> list[WorldElement]:
    """Filter elements by tag.
    
    Args:
        elements: List of elements to filter
        tag: Tag to filter by (case-insensitive)
        
    Returns:
        List of elements that have the tag
    """
    return [e for e in elements if e.has_tag(tag)]


def filter_by_type(
    elements: list[WorldElement],
    element_type: ElementType,
) -> list[WorldElement]:
    """Filter elements by type.
    
    Args:
        elements: List of elements to filter
        element_type: Type to filter by
        
    Returns:
        List of elements of that type
    """
    return [e for e in elements if e.element_type == element_type]

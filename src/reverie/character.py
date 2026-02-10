"""Character creation and management."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PlayerClass(Enum):
    """Available player classes."""

    # Original corporate parody classes
    CODE_WARRIOR = "Code Warrior"
    MEETING_SURVIVOR = "Meeting Survivor"
    INBOX_KNIGHT = "Inbox Knight"
    WANDERER = "Wanderer"
    
    # New classes
    STACK_OVERFLOW = "Stack Overflow"      # Knowledge mage, wit-focused
    SCRUM_MASTER = "Scrum Master"          # Support/buff, spirit-focused  
    LEGACY_MAINTAINER = "Legacy Maintainer"  # Tank, might-focused
    DEPLOY_NINJA = "Deploy Ninja"          # Speed/stealth, balanced


class DangerLevel(Enum):
    """Abstract HP as danger level."""

    FRESH = 3
    BLOODIED = 2
    CRITICAL = 1
    DEFEATED = 0


@dataclass
class Stats:
    """Character stats. Total must be 12, max 6 per stat."""

    might: int = 4
    wit: int = 4
    spirit: int = 4

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate stat allocation."""
        if not all(0 <= s <= 6 for s in [self.might, self.wit, self.spirit]):
            raise ValueError("Each stat must be between 0 and 6")
        if self.total != 12:
            raise ValueError(f"Stats must total 12, got {self.total}")

    @property
    def total(self) -> int:
        """Sum of all stats."""
        return self.might + self.wit + self.spirit

    def modifier(self, stat: str) -> int:
        """Get modifier for a stat (stat - 3)."""
        value = getattr(self, stat.lower(), 0)
        return value - 3


@dataclass
class Equipment:
    """Equipped items."""

    weapon: Optional[str] = None
    armor: Optional[str] = None
    accessory: Optional[str] = None


@dataclass
class Character:
    """Player character."""

    name: str
    race: str
    player_class: PlayerClass
    stats: Stats
    background: str = ""
    equipment: Equipment = field(default_factory=Equipment)
    inventory: List[str] = field(default_factory=list)
    danger_level: DangerLevel = DangerLevel.FRESH
    gold: int = 50
    xp: int = 0
    level: int = 1

    @property
    def hp(self) -> int:
        """Danger level as numeric HP."""
        return self.danger_level.value

    @property
    def max_hp(self) -> int:
        """Maximum danger level (always 3)."""
        return DangerLevel.FRESH.value

    @property
    def damage_bonus(self) -> int:
        """Bonus damage from class."""
        if self.player_class == PlayerClass.CODE_WARRIOR:
            return 10
        if self.player_class == PlayerClass.DEPLOY_NINJA:
            return 8  # Precision strikes
        return 0

    @property
    def hp_bonus(self) -> int:
        """Bonus HP from class (affects nothing in abstract system)."""
        if self.player_class == PlayerClass.MEETING_SURVIVOR:
            return 20
        if self.player_class == PlayerClass.LEGACY_MAINTAINER:
            return 30  # Battle-hardened from ancient code
        return 0

    @property
    def focus_bonus(self) -> int:
        """Bonus focus from class."""
        if self.player_class == PlayerClass.INBOX_KNIGHT:
            return 10
        if self.player_class == PlayerClass.SCRUM_MASTER:
            return 15  # Team coordination
        return 0

    @property
    def wit_bonus(self) -> int:
        """Bonus wit from class."""
        if self.player_class == PlayerClass.STACK_OVERFLOW:
            return 12  # Knowledge is power
        return 0

    @property
    def initiative_bonus(self) -> int:
        """Bonus to initiative/speed."""
        if self.player_class == PlayerClass.DEPLOY_NINJA:
            return 5  # Always first to production
        return 0

    def xp_for_next_level(self) -> int:
        """XP required to reach next level."""
        # 100, 300, 600, 1000, 1500, ...
        return sum(100 * i for i in range(1, self.level + 1))

    def can_level_up(self) -> bool:
        """Check if character has enough XP to level up."""
        return self.xp >= self.xp_for_next_level()


def create_character(
    name: str,
    race: str,
    player_class: PlayerClass,
    stats: Stats,
    background: str = "",
) -> Character:
    """Create a new character with starting equipment."""
    equipment = Equipment()

    # Class-based starting equipment
    if player_class == PlayerClass.CODE_WARRIOR:
        equipment.weapon = "Keyboard Blade"
        equipment.armor = "Debug Vest"
    elif player_class == PlayerClass.MEETING_SURVIVOR:
        equipment.weapon = "Agenda Shield"
        equipment.armor = "Corporate Armor"
    elif player_class == PlayerClass.INBOX_KNIGHT:
        equipment.weapon = "Reply-All Staff"
        equipment.accessory = "Unread Badge"
    elif player_class == PlayerClass.STACK_OVERFLOW:
        equipment.weapon = "Citation Wand"
        equipment.accessory = "Reputation Ring"
    elif player_class == PlayerClass.SCRUM_MASTER:
        equipment.weapon = "Sprint Baton"
        equipment.armor = "Kanban Cloak"
    elif player_class == PlayerClass.LEGACY_MAINTAINER:
        equipment.weapon = "Deprecated Greatsword"
        equipment.armor = "COBOL Platemail"
        equipment.accessory = "Ancient Documentation"
    elif player_class == PlayerClass.DEPLOY_NINJA:
        equipment.weapon = "Pipeline Daggers"
        equipment.accessory = "CI/CD Smoke Bomb"
    else:  # Wanderer
        equipment.weapon = "Traveler's Dagger"

    return Character(
        name=name,
        race=race,
        player_class=player_class,
        stats=stats,
        background=background,
        equipment=equipment,
    )


def roll_d20() -> int:
    """Roll a d20."""
    return random.randint(1, 20)


def roll_check(character: Character, stat: str) -> tuple[int, str]:
    """Roll a stat check and return (roll, result_description)."""
    roll = roll_d20()
    modifier = character.stats.modifier(stat)

    # Add class bonus for relevant checks
    if stat.lower() == "spirit" and character.player_class == PlayerClass.INBOX_KNIGHT:
        modifier += 2  # Focus bonus helps spirit checks

    total = roll + modifier

    if total >= 20:
        result = "Critical success"
    elif total >= 16:
        result = "Success with bonus"
    elif total >= 11:
        result = "Success"
    elif total >= 6:
        result = "Partial success"
    else:
        result = "Failure with complication"

    return total, result


def take_damage(character: Character, amount: int = 1) -> None:
    """Reduce character's danger level."""
    current = character.danger_level.value
    new_level = max(0, current - amount)
    character.danger_level = DangerLevel(new_level)


def heal(character: Character, amount: int = 1) -> None:
    """Increase character's danger level."""
    current = character.danger_level.value
    new_level = min(3, current + amount)
    character.danger_level = DangerLevel(new_level)


def gain_xp(character: Character, amount: int) -> bool:
    """Add XP and return True if level up is available."""
    character.xp += amount
    return character.can_level_up()


def level_up(character: Character) -> bool:
    """Level up if possible. Returns True if successful."""
    if not character.can_level_up():
        return False

    character.level += 1
    # Full heal on level up
    character.danger_level = DangerLevel.FRESH
    return True


def serialize_character(character: Character) -> dict:
    """Convert character to dictionary for saving."""
    return {
        "name": character.name,
        "race": character.race,
        "player_class": character.player_class.value,
        "stats": {
            "might": character.stats.might,
            "wit": character.stats.wit,
            "spirit": character.stats.spirit,
        },
        "background": character.background,
        "equipment": {
            "weapon": character.equipment.weapon,
            "armor": character.equipment.armor,
            "accessory": character.equipment.accessory,
        },
        "inventory": character.inventory,
        "danger_level": character.danger_level.value,
        "gold": character.gold,
        "xp": character.xp,
        "level": character.level,
    }


def deserialize_character(data: dict) -> Character:
    """Create character from dictionary."""
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
        danger_level=DangerLevel(data.get("danger_level", 3)),
        gold=data.get("gold", 50),
        xp=data.get("xp", 0),
        level=data.get("level", 1),
    )

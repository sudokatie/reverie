"""Inventory system for Reverie.

Slot-based inventory with equipment and gold.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
from uuid import uuid4


class ItemType(Enum):
    """Types of items."""
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"
    CONSUMABLE = "consumable"
    KEY = "key"
    MISC = "misc"


class EquipSlot(Enum):
    """Equipment slots."""
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"


@dataclass
class ItemEffect:
    """Effect when item is used."""
    stat: str  # "hp", "might", "wit", "spirit", etc.
    amount: int
    duration: int = 0  # 0 = instant, >0 = turns
    description: str = ""


@dataclass
class Item:
    """An item in the game."""
    id: str
    name: str
    description: str
    item_type: ItemType
    value: int = 0  # Gold value
    effect: Optional[ItemEffect] = None
    equip_stat_bonus: int = 0  # Stat bonus when equipped
    
    def is_equippable(self) -> bool:
        """Check if item can be equipped."""
        return self.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY)
    
    def is_consumable(self) -> bool:
        """Check if item can be consumed."""
        return self.item_type == ItemType.CONSUMABLE
    
    def is_key_item(self) -> bool:
        """Check if item is a key item (doesn't take inventory space)."""
        return self.item_type == ItemType.KEY
    
    def get_equip_slot(self) -> Optional[EquipSlot]:
        """Get the slot this item equips to."""
        if self.item_type == ItemType.WEAPON:
            return EquipSlot.WEAPON
        elif self.item_type == ItemType.ARMOR:
            return EquipSlot.ARMOR
        elif self.item_type == ItemType.ACCESSORY:
            return EquipSlot.ACCESSORY
        return None
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "item_type": self.item_type.value,
            "value": self.value,
            "equip_stat_bonus": self.equip_stat_bonus,
        }
        if self.effect:
            data["effect"] = {
                "stat": self.effect.stat,
                "amount": self.effect.amount,
                "duration": self.effect.duration,
                "description": self.effect.description,
            }
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        """Deserialize from dictionary."""
        effect = None
        if "effect" in data:
            e = data["effect"]
            effect = ItemEffect(
                stat=e["stat"],
                amount=e["amount"],
                duration=e.get("duration", 0),
                description=e.get("description", ""),
            )
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            item_type=ItemType(data["item_type"]),
            value=data.get("value", 0),
            effect=effect,
            equip_stat_bonus=data.get("equip_stat_bonus", 0),
        )


@dataclass
class Inventory:
    """Player inventory."""
    items: list[Item] = field(default_factory=list)
    max_slots: int = 10
    equipped: dict[EquipSlot, Optional[Item]] = field(default_factory=dict)
    gold: int = 0
    key_items: list[Item] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize equipped slots."""
        if not self.equipped:
            self.equipped = {
                EquipSlot.WEAPON: None,
                EquipSlot.ARMOR: None,
                EquipSlot.ACCESSORY: None,
            }
    
    def used_slots(self) -> int:
        """Get number of used inventory slots."""
        return len(self.items)
    
    def free_slots(self) -> int:
        """Get number of free inventory slots."""
        return self.max_slots - self.used_slots()
    
    def can_carry(self) -> bool:
        """Check if there's room for more items."""
        return self.used_slots() < self.max_slots
    
    def add_item(self, item: Item) -> bool:
        """Add an item to inventory.
        
        Returns True if successful.
        """
        if item.is_key_item():
            self.key_items.append(item)
            return True
        
        if not self.can_carry():
            return False
        
        self.items.append(item)
        return True
    
    def remove_item(self, item_id: str) -> Optional[Item]:
        """Remove an item by ID.
        
        Returns the removed item or None.
        """
        for i, item in enumerate(self.items):
            if item.id == item_id:
                return self.items.pop(i)
        
        # Check key items
        for i, item in enumerate(self.key_items):
            if item.id == item_id:
                return self.key_items.pop(i)
        
        return None
    
    def get_item(self, item_id: str) -> Optional[Item]:
        """Get an item by ID without removing it."""
        for item in self.items:
            if item.id == item_id:
                return item
        for item in self.key_items:
            if item.id == item_id:
                return item
        return None
    
    def has_item(self, item_id: str) -> bool:
        """Check if inventory contains an item."""
        return self.get_item(item_id) is not None
    
    def equip_item(self, item_id: str) -> bool:
        """Equip an item from inventory.
        
        Returns True if successful.
        """
        item = self.get_item(item_id)
        if item is None or not item.is_equippable():
            return False
        
        slot = item.get_equip_slot()
        if slot is None:
            return False
        
        # Unequip current item in slot (move to inventory)
        current = self.equipped.get(slot)
        if current is not None:
            self.items.append(current)
        
        # Remove new item from inventory and equip
        self.remove_item(item_id)
        self.equipped[slot] = item
        return True
    
    def unequip_item(self, slot: EquipSlot) -> Optional[Item]:
        """Unequip an item from a slot.
        
        Returns the unequipped item or None.
        """
        item = self.equipped.get(slot)
        if item is None:
            return None
        
        if not self.can_carry():
            return None  # No room in inventory
        
        self.equipped[slot] = None
        self.items.append(item)
        return item
    
    def get_equipped(self, slot: EquipSlot) -> Optional[Item]:
        """Get item equipped in a slot."""
        return self.equipped.get(slot)
    
    def add_gold(self, amount: int) -> int:
        """Add gold. Returns new total."""
        self.gold += amount
        return self.gold
    
    def spend_gold(self, amount: int) -> bool:
        """Spend gold if possible. Returns True if successful."""
        if amount > self.gold:
            return False
        self.gold -= amount
        return True
    
    def can_afford(self, amount: int) -> bool:
        """Check if can afford an amount."""
        return self.gold >= amount
    
    def get_total_equip_bonus(self) -> int:
        """Get total stat bonus from equipped items."""
        total = 0
        for item in self.equipped.values():
            if item is not None:
                total += item.equip_stat_bonus
        return total
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        equipped_data = {}
        for slot, item in self.equipped.items():
            equipped_data[slot.value] = item.to_dict() if item else None
        
        return {
            "items": [item.to_dict() for item in self.items],
            "max_slots": self.max_slots,
            "equipped": equipped_data,
            "gold": self.gold,
            "key_items": [item.to_dict() for item in self.key_items],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Inventory":
        """Deserialize from dictionary."""
        inv = cls(
            items=[Item.from_dict(i) for i in data.get("items", [])],
            max_slots=data.get("max_slots", 10),
            gold=data.get("gold", 0),
            key_items=[Item.from_dict(i) for i in data.get("key_items", [])],
        )
        
        for slot_name, item_data in data.get("equipped", {}).items():
            slot = EquipSlot(slot_name)
            inv.equipped[slot] = Item.from_dict(item_data) if item_data else None
        
        return inv


# Helper functions

def create_item(
    name: str,
    item_type: ItemType,
    description: str = "",
    value: int = 0,
    effect: Optional[ItemEffect] = None,
    equip_stat_bonus: int = 0,
) -> Item:
    """Create a new item."""
    return Item(
        id=str(uuid4()),
        name=name,
        description=description,
        item_type=item_type,
        value=value,
        effect=effect,
        equip_stat_bonus=equip_stat_bonus,
    )


def add_item(inventory: Inventory, item: Item) -> bool:
    """Add an item to inventory."""
    return inventory.add_item(item)


def remove_item(inventory: Inventory, item_id: str) -> Optional[Item]:
    """Remove an item from inventory."""
    return inventory.remove_item(item_id)


def equip_item(inventory: Inventory, item_id: str) -> bool:
    """Equip an item."""
    return inventory.equip_item(item_id)


def unequip_item(inventory: Inventory, slot: EquipSlot) -> Optional[Item]:
    """Unequip an item."""
    return inventory.unequip_item(slot)


def use_item(inventory: Inventory, item_id: str, character: Any = None) -> str:
    """Use a consumable item.
    
    Args:
        inventory: The inventory
        item_id: ID of item to use
        character: Optional character to apply effects to
        
    Returns:
        Description of what happened
    """
    item = inventory.get_item(item_id)
    if item is None:
        return "Item not found."
    
    if not item.is_consumable():
        return f"{item.name} cannot be used."
    
    # Remove the item
    inventory.remove_item(item_id)
    
    # Apply effect if character provided
    if character is not None and item.effect is not None:
        effect = item.effect
        if effect.stat == "hp":
            # Heal character
            if hasattr(character, "heal"):
                character.heal(effect.amount)
            return f"Used {item.name}. {effect.description or f'Restored {effect.amount} HP.'}"
        else:
            # Stat boost
            return f"Used {item.name}. {effect.description or f'+{effect.amount} {effect.stat}.'}"
    
    return f"Used {item.name}."


def can_carry(inventory: Inventory) -> bool:
    """Check if inventory has room."""
    return inventory.can_carry()

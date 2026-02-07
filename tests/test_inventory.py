"""Tests for inventory system."""

import pytest

from reverie.inventory import (
    ItemType,
    EquipSlot,
    ItemEffect,
    Item,
    Inventory,
    create_item,
    add_item,
    remove_item,
    equip_item,
    unequip_item,
    use_item,
    can_carry,
)


class TestItem:
    """Tests for Item class."""

    def test_create_item(self):
        """Create a basic item."""
        item = create_item(
            name="Iron Sword",
            item_type=ItemType.WEAPON,
            description="A sturdy iron sword.",
            value=50,
            equip_stat_bonus=2,
        )
        assert item.name == "Iron Sword"
        assert item.item_type == ItemType.WEAPON
        assert item.value == 50

    def test_item_is_equippable(self):
        """Check equippable items."""
        weapon = create_item("Sword", ItemType.WEAPON)
        armor = create_item("Armor", ItemType.ARMOR)
        potion = create_item("Potion", ItemType.CONSUMABLE)
        key = create_item("Key", ItemType.KEY)
        
        assert weapon.is_equippable()
        assert armor.is_equippable()
        assert not potion.is_equippable()
        assert not key.is_equippable()

    def test_item_is_consumable(self):
        """Check consumable items."""
        potion = create_item("Potion", ItemType.CONSUMABLE)
        sword = create_item("Sword", ItemType.WEAPON)
        
        assert potion.is_consumable()
        assert not sword.is_consumable()

    def test_item_is_key_item(self):
        """Check key items."""
        key = create_item("Magic Key", ItemType.KEY)
        misc = create_item("Rock", ItemType.MISC)
        
        assert key.is_key_item()
        assert not misc.is_key_item()

    def test_get_equip_slot(self):
        """Get correct equip slot."""
        weapon = create_item("Sword", ItemType.WEAPON)
        armor = create_item("Plate", ItemType.ARMOR)
        ring = create_item("Ring", ItemType.ACCESSORY)
        potion = create_item("Potion", ItemType.CONSUMABLE)
        
        assert weapon.get_equip_slot() == EquipSlot.WEAPON
        assert armor.get_equip_slot() == EquipSlot.ARMOR
        assert ring.get_equip_slot() == EquipSlot.ACCESSORY
        assert potion.get_equip_slot() is None

    def test_item_serialization(self):
        """Item serializes and deserializes."""
        effect = ItemEffect(stat="hp", amount=20, description="Heals 20 HP")
        original = create_item(
            name="Health Potion",
            item_type=ItemType.CONSUMABLE,
            value=25,
            effect=effect,
        )
        
        data = original.to_dict()
        restored = Item.from_dict(data)
        
        assert restored.name == original.name
        assert restored.effect.amount == 20


class TestInventory:
    """Tests for Inventory class."""

    def test_create_inventory(self):
        """Create an inventory."""
        inv = Inventory()
        assert inv.max_slots == 10
        assert inv.used_slots() == 0
        assert inv.gold == 0

    def test_add_item(self):
        """Add items to inventory."""
        inv = Inventory()
        sword = create_item("Sword", ItemType.WEAPON)
        
        assert add_item(inv, sword)
        assert inv.used_slots() == 1
        assert inv.has_item(sword.id)

    def test_add_key_item_no_slot(self):
        """Key items don't use inventory slots."""
        inv = Inventory(max_slots=1)
        key = create_item("Magic Key", ItemType.KEY)
        sword = create_item("Sword", ItemType.WEAPON)
        
        assert add_item(inv, key)
        assert add_item(inv, sword)
        assert inv.used_slots() == 1  # Only sword takes slot

    def test_inventory_capacity(self):
        """Inventory respects capacity."""
        inv = Inventory(max_slots=2)
        
        assert add_item(inv, create_item("Item 1", ItemType.MISC))
        assert add_item(inv, create_item("Item 2", ItemType.MISC))
        assert not add_item(inv, create_item("Item 3", ItemType.MISC))

    def test_remove_item(self):
        """Remove items from inventory."""
        inv = Inventory()
        sword = create_item("Sword", ItemType.WEAPON)
        add_item(inv, sword)
        
        removed = remove_item(inv, sword.id)
        assert removed is not None
        assert removed.name == "Sword"
        assert inv.used_slots() == 0

    def test_remove_nonexistent_item(self):
        """Removing nonexistent item returns None."""
        inv = Inventory()
        removed = remove_item(inv, "fake-id")
        assert removed is None

    def test_can_carry(self):
        """Check inventory capacity."""
        inv = Inventory(max_slots=1)
        assert can_carry(inv)
        
        add_item(inv, create_item("Item", ItemType.MISC))
        assert not can_carry(inv)


class TestEquipment:
    """Tests for equipment functionality."""

    def test_equip_item(self):
        """Equip an item."""
        inv = Inventory()
        sword = create_item("Sword", ItemType.WEAPON)
        add_item(inv, sword)
        
        assert equip_item(inv, sword.id)
        assert inv.get_equipped(EquipSlot.WEAPON) is not None
        assert inv.used_slots() == 0  # Moved to equipped

    def test_equip_replaces_current(self):
        """Equipping replaces current item."""
        inv = Inventory()
        sword1 = create_item("Sword 1", ItemType.WEAPON)
        sword2 = create_item("Sword 2", ItemType.WEAPON)
        
        add_item(inv, sword1)
        add_item(inv, sword2)
        
        equip_item(inv, sword1.id)
        equip_item(inv, sword2.id)
        
        # Sword 1 should be back in inventory
        assert inv.has_item(sword1.id)
        assert inv.get_equipped(EquipSlot.WEAPON).name == "Sword 2"

    def test_unequip_item(self):
        """Unequip an item."""
        inv = Inventory()
        sword = create_item("Sword", ItemType.WEAPON)
        add_item(inv, sword)
        equip_item(inv, sword.id)
        
        unequipped = unequip_item(inv, EquipSlot.WEAPON)
        assert unequipped is not None
        assert unequipped.name == "Sword"
        assert inv.get_equipped(EquipSlot.WEAPON) is None
        assert inv.used_slots() == 1  # Back in inventory

    def test_unequip_empty_slot(self):
        """Unequipping empty slot returns None."""
        inv = Inventory()
        unequipped = unequip_item(inv, EquipSlot.WEAPON)
        assert unequipped is None

    def test_equip_stat_bonus(self):
        """Total equip bonus calculated correctly."""
        inv = Inventory()
        sword = create_item("Sword", ItemType.WEAPON, equip_stat_bonus=3)
        armor = create_item("Armor", ItemType.ARMOR, equip_stat_bonus=2)
        
        add_item(inv, sword)
        add_item(inv, armor)
        equip_item(inv, sword.id)
        equip_item(inv, armor.id)
        
        assert inv.get_total_equip_bonus() == 5


class TestGold:
    """Tests for gold management."""

    def test_add_gold(self):
        """Add gold to inventory."""
        inv = Inventory()
        inv.add_gold(100)
        assert inv.gold == 100
        
        inv.add_gold(50)
        assert inv.gold == 150

    def test_spend_gold_success(self):
        """Spend gold when affordable."""
        inv = Inventory()
        inv.add_gold(100)
        
        assert inv.spend_gold(75)
        assert inv.gold == 25

    def test_spend_gold_failure(self):
        """Cannot spend more than available."""
        inv = Inventory()
        inv.add_gold(50)
        
        assert not inv.spend_gold(100)
        assert inv.gold == 50  # Unchanged

    def test_can_afford(self):
        """Check affordability."""
        inv = Inventory()
        inv.add_gold(100)
        
        assert inv.can_afford(50)
        assert inv.can_afford(100)
        assert not inv.can_afford(101)


class TestUseItem:
    """Tests for using consumable items."""

    def test_use_consumable(self):
        """Use a consumable item."""
        inv = Inventory()
        potion = create_item("Health Potion", ItemType.CONSUMABLE)
        add_item(inv, potion)
        
        result = use_item(inv, potion.id)
        assert "Health Potion" in result
        assert not inv.has_item(potion.id)

    def test_use_non_consumable(self):
        """Cannot use non-consumable items."""
        inv = Inventory()
        sword = create_item("Sword", ItemType.WEAPON)
        add_item(inv, sword)
        
        result = use_item(inv, sword.id)
        assert "cannot be used" in result
        assert inv.has_item(sword.id)  # Still in inventory

    def test_use_missing_item(self):
        """Using missing item returns error."""
        inv = Inventory()
        result = use_item(inv, "fake-id")
        assert "not found" in result


class TestSerialization:
    """Tests for inventory serialization."""

    def test_inventory_roundtrip(self):
        """Inventory serializes and deserializes."""
        inv = Inventory(max_slots=5)
        inv.add_gold(250)
        
        sword = create_item("Sword", ItemType.WEAPON, equip_stat_bonus=2)
        armor = create_item("Armor", ItemType.ARMOR)
        key = create_item("Magic Key", ItemType.KEY)
        
        add_item(inv, sword)
        add_item(inv, armor)
        add_item(inv, key)
        equip_item(inv, sword.id)
        
        data = inv.to_dict()
        restored = Inventory.from_dict(data)
        
        assert restored.gold == 250
        assert restored.max_slots == 5
        assert len(restored.key_items) == 1
        assert restored.get_equipped(EquipSlot.WEAPON) is not None

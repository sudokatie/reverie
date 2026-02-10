"""Tests for character module."""

import pytest

from reverie.character import (
    Character,
    DangerLevel,
    Equipment,
    PlayerClass,
    Stats,
    create_character,
    deserialize_character,
    gain_xp,
    heal,
    level_up,
    roll_check,
    serialize_character,
    take_damage,
)


class TestStats:
    def test_valid_stats(self):
        stats = Stats(might=6, wit=4, spirit=2)
        assert stats.total == 12

    def test_invalid_total(self):
        with pytest.raises(ValueError, match="must total 12"):
            Stats(might=6, wit=6, spirit=6)

    def test_stat_too_high(self):
        with pytest.raises(ValueError, match="between 0 and 6"):
            Stats(might=7, wit=3, spirit=2)

    def test_stat_negative(self):
        with pytest.raises(ValueError, match="between 0 and 6"):
            Stats(might=-1, wit=7, spirit=6)

    def test_modifier_positive(self):
        stats = Stats(might=6, wit=4, spirit=2)
        assert stats.modifier("might") == 3

    def test_modifier_zero(self):
        stats = Stats(might=3, wit=4, spirit=5)
        assert stats.modifier("might") == 0

    def test_modifier_negative(self):
        stats = Stats(might=2, wit=4, spirit=6)
        assert stats.modifier("might") == -1


class TestEquipment:
    def test_empty_equipment(self):
        equip = Equipment()
        assert equip.weapon is None
        assert equip.armor is None
        assert equip.accessory is None

    def test_equipped_items(self):
        equip = Equipment(weapon="Sword", armor="Plate")
        assert equip.weapon == "Sword"
        assert equip.armor == "Plate"


class TestCharacter:
    @pytest.fixture
    def warrior(self):
        return create_character(
            name="Test Hero",
            race="Human",
            player_class=PlayerClass.CODE_WARRIOR,
            stats=Stats(might=6, wit=3, spirit=3),
            background="A test character",
        )

    def test_create_character(self, warrior):
        assert warrior.name == "Test Hero"
        assert warrior.race == "Human"
        assert warrior.player_class == PlayerClass.CODE_WARRIOR
        assert warrior.stats.might == 6

    def test_starting_hp(self, warrior):
        assert warrior.hp == 3
        assert warrior.danger_level == DangerLevel.FRESH

    def test_starting_gold(self, warrior):
        assert warrior.gold == 50

    def test_starting_level(self, warrior):
        assert warrior.level == 1
        assert warrior.xp == 0

    def test_code_warrior_equipment(self, warrior):
        assert warrior.equipment.weapon == "Keyboard Blade"
        assert warrior.equipment.armor == "Debug Vest"

    def test_code_warrior_damage_bonus(self, warrior):
        assert warrior.damage_bonus == 10

    def test_meeting_survivor_hp_bonus(self):
        char = create_character(
            name="Survivor",
            race="Human",
            player_class=PlayerClass.MEETING_SURVIVOR,
            stats=Stats(might=4, wit=4, spirit=4),
        )
        assert char.hp_bonus == 20

    def test_inbox_knight_focus_bonus(self):
        char = create_character(
            name="Knight",
            race="Human",
            player_class=PlayerClass.INBOX_KNIGHT,
            stats=Stats(might=4, wit=4, spirit=4),
        )
        assert char.focus_bonus == 10


class TestDamageAndHealing:
    @pytest.fixture
    def character(self):
        return create_character(
            name="Test",
            race="Human",
            player_class=PlayerClass.WANDERER,
            stats=Stats(might=4, wit=4, spirit=4),
        )

    def test_take_damage(self, character):
        assert character.danger_level == DangerLevel.FRESH
        take_damage(character)
        assert character.danger_level == DangerLevel.BLOODIED

    def test_take_multiple_damage(self, character):
        take_damage(character, 2)
        assert character.danger_level == DangerLevel.CRITICAL

    def test_damage_floors_at_zero(self, character):
        take_damage(character, 10)
        assert character.danger_level == DangerLevel.DEFEATED

    def test_heal(self, character):
        take_damage(character, 2)
        heal(character)
        assert character.danger_level == DangerLevel.BLOODIED

    def test_heal_caps_at_max(self, character):
        heal(character, 10)
        assert character.danger_level == DangerLevel.FRESH


class TestXPAndLeveling:
    @pytest.fixture
    def character(self):
        return create_character(
            name="Test",
            race="Human",
            player_class=PlayerClass.WANDERER,
            stats=Stats(might=4, wit=4, spirit=4),
        )

    def test_xp_for_level_1(self, character):
        assert character.xp_for_next_level() == 100

    def test_xp_for_level_2(self, character):
        character.level = 2
        assert character.xp_for_next_level() == 300  # 100 + 200

    def test_gain_xp(self, character):
        result = gain_xp(character, 50)
        assert character.xp == 50
        assert result is False  # Can't level up yet

    def test_gain_xp_enough_to_level(self, character):
        result = gain_xp(character, 100)
        assert result is True  # Can level up

    def test_level_up(self, character):
        gain_xp(character, 100)
        take_damage(character)  # Get hurt first
        result = level_up(character)
        assert result is True
        assert character.level == 2
        assert character.danger_level == DangerLevel.FRESH  # Healed on level up

    def test_level_up_not_enough_xp(self, character):
        result = level_up(character)
        assert result is False
        assert character.level == 1


class TestRollCheck:
    def test_roll_returns_tuple(self):
        character = create_character(
            name="Test",
            race="Human",
            player_class=PlayerClass.WANDERER,
            stats=Stats(might=4, wit=4, spirit=4),
        )
        total, result = roll_check(character, "might")
        assert isinstance(total, int)
        assert isinstance(result, str)
        assert total >= 1  # Min roll + modifier
        assert total <= 23  # Max roll + max modifier


class TestSerialization:
    @pytest.fixture
    def character(self):
        char = create_character(
            name="Test Hero",
            race="Elf",
            player_class=PlayerClass.CODE_WARRIOR,
            stats=Stats(might=6, wit=3, spirit=3),
            background="Test background",
        )
        char.gold = 100
        char.xp = 50
        char.inventory = ["Potion", "Key"]
        return char

    def test_serialize(self, character):
        data = serialize_character(character)
        assert data["name"] == "Test Hero"
        assert data["race"] == "Elf"
        assert data["player_class"] == "Code Warrior"
        assert data["stats"]["might"] == 6
        assert data["gold"] == 100
        assert data["inventory"] == ["Potion", "Key"]

    def test_deserialize(self, character):
        data = serialize_character(character)
        restored = deserialize_character(data)
        assert restored.name == character.name
        assert restored.race == character.race
        assert restored.player_class == character.player_class
        assert restored.stats.might == character.stats.might
        assert restored.gold == character.gold

    def test_roundtrip(self, character):
        data = serialize_character(character)
        restored = deserialize_character(data)
        data2 = serialize_character(restored)
        assert data == data2


class TestClassDialogueOptions:
    """Tests for class-specific dialogue options."""

    def test_code_warrior_has_dialogue_options(self):
        """Code Warrior should have intimidate options."""
        from reverie.character import get_class_dialogue_options, PlayerClass
        
        options = get_class_dialogue_options(PlayerClass.CODE_WARRIOR, "intimidate")
        assert len(options) >= 1
        assert any("refactor" in opt.lower() or "debug" in opt.lower() for opt in options)

    def test_stack_overflow_has_knowledge_options(self):
        """Stack Overflow should have knowledge options."""
        from reverie.character import get_class_dialogue_options, PlayerClass
        
        options = get_class_dialogue_options(PlayerClass.STACK_OVERFLOW, "knowledge")
        assert len(options) >= 1
        assert any("cite" in opt.lower() or "answer" in opt.lower() for opt in options)

    def test_scrum_master_has_motivate_options(self):
        """Scrum Master should have motivate options."""
        from reverie.character import get_class_dialogue_options, PlayerClass
        
        options = get_class_dialogue_options(PlayerClass.SCRUM_MASTER, "motivate")
        assert len(options) >= 1

    def test_deploy_ninja_has_stealth_options(self):
        """Deploy Ninja should have stealth options."""
        from reverie.character import get_class_dialogue_options, PlayerClass
        
        options = get_class_dialogue_options(PlayerClass.DEPLOY_NINJA, "stealth")
        assert len(options) >= 1
        assert any("shadow" in opt.lower() or "prod" in opt.lower() for opt in options)

    def test_get_all_class_options(self):
        """Should return all options when no situation specified."""
        from reverie.character import get_class_dialogue_options, PlayerClass
        
        all_options = get_class_dialogue_options(PlayerClass.STACK_OVERFLOW)
        assert len(all_options) >= 3  # Has knowledge, pedantic, wisdom

    def test_get_dialogue_categories(self):
        """Should return category names for a class."""
        from reverie.character import get_class_dialogue_categories, PlayerClass
        
        categories = get_class_dialogue_categories(PlayerClass.SCRUM_MASTER)
        assert "motivate" in categories
        assert "organize" in categories
        assert "teamwork" in categories

    def test_unknown_situation_returns_empty(self):
        """Unknown situation should return empty list."""
        from reverie.character import get_class_dialogue_options, PlayerClass
        
        options = get_class_dialogue_options(PlayerClass.CODE_WARRIOR, "unknown_situation")
        assert options == []

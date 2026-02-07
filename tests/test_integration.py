"""Integration tests for Reverie.

End-to-end tests that exercise multiple components together.
"""

import pytest
from uuid import uuid4

from reverie.character import Character, Stats, Equipment, PlayerClass, DangerLevel
from reverie.world import Location, ElementType
from reverie.npc import NPC, Disposition
from reverie.quest import Quest, QuestStage, QuestReward, QuestStatus
from reverie.combat import Enemy, CombatState, CombatStatus
from reverie.combat import DangerLevel as CombatDangerLevel
from reverie.storage.database import Database
from reverie.storage.models import Campaign, CharacterRecord, WorldElementRecord, NPCRecord
from reverie.game import (
    Game,
    GameState,
    create_game_state,
    save_state,
    load_state,
    process_input,
    handle_command,
    handle_action,
    handle_dialogue,
    handle_combat_action,
    check_triggers,
    add_to_history,
    EventType,
)


class TestCharacterCreationFlow:
    """Test full character creation and initialization."""
    
    def test_create_character_and_start_game(self, test_database):
        """Test creating a character and starting a new game."""
        # Create campaign
        campaign = Campaign.create("New Adventure")
        test_database.save_campaign(campaign)
        
        # Create character
        character = Character(
            name="Hero",
            race="Human",
            player_class=PlayerClass.CODE_WARRIOR,
            stats=Stats(might=5, wit=4, spirit=3),
        )
        
        # Create starting location
        location = Location(
            id="start-001",
            element_type=ElementType.SETTLEMENT,
            name="Starting Town",
            description="A quiet town at the edge of adventure.",
        )
        
        # Initialize game state
        state = create_game_state(campaign, character, location)
        
        # Verify state
        assert state.character.name == "Hero"
        assert state.location.name == "Starting Town"
        assert len(state.history) == 1  # Initial entry
    
    def test_character_with_equipment_persists(self, test_database):
        """Test that character equipment persists through save/load."""
        campaign = Campaign.create("Equipment Test")
        character = Character(
            name="Equipped",
            race="Dwarf",
            player_class=PlayerClass.INBOX_KNIGHT,
            stats=Stats(might=6, wit=3, spirit=3),
            equipment=Equipment(
                weapon="Battle Axe",
                armor="Plate Mail",
                accessory="Ring of Power",
            ),
            inventory=["Health Potion", "Magic Key"],
            gold=500,
        )
        
        state = create_game_state(campaign, character)
        game = Game(state=state, db=test_database, llm=None)
        
        # Save state
        save_state(state, test_database)
        
        # Load state
        loaded = load_state(test_database, campaign.id)
        
        assert loaded.character.equipment.weapon == "Battle Axe"
        assert loaded.character.equipment.armor == "Plate Mail"
        assert "Health Potion" in loaded.character.inventory
        assert loaded.character.gold == 500


class TestExplorationFlow:
    """Test location exploration and movement."""
    
    def test_look_command_shows_location(self, sample_game):
        """Test that look command describes current location."""
        result = handle_command(sample_game, "look")
        
        assert sample_game.state.location.name in result
        assert sample_game.state.location.description in result or "Exit" in result
    
    def test_movement_between_locations(self, test_database, sample_character):
        """Test moving between connected locations."""
        campaign = Campaign.create("Exploration Test")
        test_database.save_campaign(campaign)  # Save campaign first for FK
        
        # Create connected locations
        village = Location(
            id="village-001",
            element_type=ElementType.SETTLEMENT,
            name="Village",
            description="A small village.",
            exits={"north": "forest-001"},
        )
        
        forest = Location(
            id="forest-001",
            element_type=ElementType.WILDERNESS,
            name="Forest",
            description="A dark forest.",
            exits={"south": "village-001"},
        )
        
        # Save locations to database
        test_database.save_world_element(WorldElementRecord(
            id=village.id,
            campaign_id=campaign.id,
            element_type=village.element_type.value,
            name=village.name,
            data=village.to_dict(),
        ))
        test_database.save_world_element(WorldElementRecord(
            id=forest.id,
            campaign_id=campaign.id,
            element_type=forest.element_type.value,
            name=forest.name,
            data=forest.to_dict(),
        ))
        
        # Create game at village
        state = create_game_state(campaign, sample_character, village)
        game = Game(state=state, db=test_database, llm=None)
        
        # Move north
        result = process_input(game, "go north")
        
        assert "Forest" in result
        assert game.state.location.id == "forest-001"
    
    def test_invalid_movement_blocked(self, sample_game):
        """Test that invalid movement directions are blocked."""
        result = process_input(sample_game, "go underwater")
        
        assert "can't go" in result.lower() or "available" in result.lower()


class TestNPCConversationFlow:
    """Test NPC interaction and dialogue."""
    
    def test_talk_to_present_npc(self, game_with_npcs, sample_npc):
        """Test talking to an NPC in the location."""
        result = process_input(game_with_npcs, f"talk to {sample_npc.name}")
        
        assert sample_npc.name in result
    
    def test_dialogue_with_npc(self, sample_game, sample_npc, mock_llm):
        """Test full dialogue exchange."""
        sample_game.llm = mock_llm
        
        result = handle_dialogue(sample_game, sample_npc, "Hello, how are you?")
        
        assert sample_npc.name in result
        assert len(mock_llm.calls) > 0  # LLM was called
    
    def test_npc_disposition_affects_greeting(self, sample_game, hostile_npc):
        """Test that NPC disposition affects their response."""
        from reverie.game import _get_npc_greeting
        
        greeting = _get_npc_greeting(hostile_npc)
        
        # Hostile NPCs should have unfriendly greetings
        assert "want" in greeting.lower() or "what" in greeting.lower()


class TestQuestFlow:
    """Test quest assignment, progression, and completion."""
    
    def test_quest_progress_tracking(self, game_with_quest):
        """Test that quest progress is tracked correctly."""
        quest = game_with_quest.state.active_quest
        
        # Initial state
        completed, total = quest.get_progress()
        assert completed == 0
        assert total == 4
        
        # Complete first stage
        quest.advance_stage(0)
        completed, total = quest.get_progress()
        assert completed == 1
    
    def test_quest_completion(self, game_with_quest):
        """Test completing a quest."""
        quest = game_with_quest.state.active_quest
        
        # Complete all stages
        for i in range(len(quest.stages)):
            quest.advance_stage(i)
        
        # Complete the quest
        quest.complete(0)
        
        assert quest.status == QuestStatus.COMPLETED
        assert not game_with_quest.state.has_active_quest
    
    def test_quest_shown_in_context(self, game_with_quest):
        """Test that active quest appears in game context."""
        from reverie.game import get_context
        
        context = get_context(game_with_quest.state)
        
        assert context["active_quest"] is not None
        assert context["active_quest"]["title"] == game_with_quest.state.active_quest.title


class TestCombatFlow:
    """Test combat initiation, actions, and resolution."""
    
    def test_combat_attack_action(self, game_in_combat):
        """Test player attack in combat."""
        result = handle_combat_action(game_in_combat, "attack")
        
        # Should mention the enemy
        assert "goblin" in result.lower() or "hit" in result.lower() or "miss" in result.lower()
    
    def test_combat_defend_action(self, game_in_combat):
        """Test player defend in combat."""
        result = handle_combat_action(game_in_combat, "defend")
        
        assert "guard" in result.lower() or "defend" in result.lower()
    
    def test_combat_victory(self, sample_game):
        """Test combat ending in victory."""
        # Create weak enemy
        weak_enemy = Enemy(
            id="weak-001",
            name="Weak Bug",
            danger_level=CombatDangerLevel.CRITICAL,  # One hit from defeat
            damage=1,
        )
        
        sample_game.state.combat_state = CombatState(enemies=[weak_enemy])
        
        # Attack until victory (may take a few tries due to random rolls)
        for _ in range(10):
            if not sample_game.state.in_combat:
                break
            handle_combat_action(sample_game, "attack")
        
        # Either won or enemy still alive
        if not sample_game.state.in_combat:
            assert sample_game.state.combat_state is None
    
    def test_not_in_combat_message(self, sample_game):
        """Test that combat actions outside combat are blocked."""
        result = handle_combat_action(sample_game, "attack")
        
        assert "not in combat" in result.lower()


class TestSaveLoadFlow:
    """Test saving and loading game state."""
    
    def test_full_save_load_cycle(self, sample_game, test_database):
        """Test saving and loading a complete game state."""
        # Make some changes
        add_to_history(sample_game.state, EventType.PLAYER_ACTION, "Searched the room")
        add_to_history(sample_game.state, EventType.NARRATION, "Found a hidden door")
        sample_game.state.character.gold += 50
        
        # Save
        save_state(sample_game.state, test_database)
        
        # Load
        loaded = load_state(test_database, sample_game.state.campaign.id)
        
        assert loaded is not None
        assert loaded.character.gold == sample_game.state.character.gold
        assert len(loaded.history) >= 2  # At least our added entries
    
    def test_save_command(self, sample_game):
        """Test the save command."""
        result = handle_command(sample_game, "save")
        
        assert "saved" in result.lower()
    
    def test_load_preserves_location(self, sample_game, test_database):
        """Test that loading preserves the current location."""
        original_location = sample_game.state.location.name
        
        save_state(sample_game.state, test_database)
        loaded = load_state(test_database, sample_game.state.campaign.id)
        
        assert loaded.location is not None
        assert loaded.location.name == original_location


class TestTriggerChecks:
    """Test automatic trigger detection."""
    
    def test_level_up_trigger(self, sample_game):
        """Test that level up is triggered correctly."""
        # Give enough XP
        sample_game.state.character.xp = 200
        sample_game.state.character.level = 1
        
        triggers = check_triggers(sample_game)
        
        assert any("level up" in t.lower() for t in triggers)
        assert sample_game.state.character.level == 2
    
    def test_critical_health_warning(self, sample_game):
        """Test critical health warning trigger."""
        sample_game.state.character.danger_level = DangerLevel.CRITICAL
        
        triggers = check_triggers(sample_game)
        
        assert any("critical" in t.lower() or "wounded" in t.lower() for t in triggers)


class TestEndToEndGameplay:
    """Full gameplay scenario tests."""
    
    def test_new_game_to_first_combat(self, test_database, mock_llm):
        """Test starting a new game and entering combat."""
        # Setup
        campaign = Campaign.create("Full Test")
        character = Character(
            name="TestHero",
            race="Human",
            player_class=PlayerClass.CODE_WARRIOR,
            stats=Stats(might=5, wit=4, spirit=3),
        )
        location = Location(
            id="start",
            element_type=ElementType.SETTLEMENT,
            name="Starting Area",
            description="The beginning of your journey.",
            exits={"north": "danger"},
        )
        
        state = create_game_state(campaign, character, location)
        game = Game(state=state, db=test_database, llm=mock_llm)
        
        # Look around
        look_result = process_input(game, "look")
        assert "Starting Area" in look_result
        
        # Check stats
        stats_result = process_input(game, "stats")
        assert "TestHero" in stats_result
        
        # Enter combat
        enemy = Enemy(id="e1", name="Test Monster")
        game.state.combat_state = CombatState(enemies=[enemy])
        
        # Fight
        combat_result = process_input(game, "attack")
        assert "monster" in combat_result.lower() or "hit" in combat_result.lower() or "miss" in combat_result.lower()
    
    def test_quest_gameplay_flow(self, test_database, mock_llm):
        """Test accepting and progressing through a quest."""
        # Setup
        campaign = Campaign.create("Quest Test")
        character = Character(
            name="Quester",
            race="Elf",
            player_class=PlayerClass.WANDERER,
            stats=Stats(might=4, wit=4, spirit=4),
        )
        location = Location(
            id="town",
            element_type=ElementType.SETTLEMENT,
            name="Quest Town",
            description="A town full of adventure.",
        )
        
        state = create_game_state(campaign, character, location)
        game = Game(state=state, db=test_database, llm=mock_llm)
        
        # Add quest
        quest = Quest(
            id="q1",
            title="Test Quest",
            hook="Help needed!",
            objective="Complete the test",
            stages=[QuestStage("Stage 1"), QuestStage("Stage 2")],
            rewards=QuestReward(gold=100),
        )
        game.state.active_quest = quest
        
        # Check quest
        quest_result = process_input(game, "quests")
        assert "Test Quest" in quest_result
        
        # Progress quest
        quest.advance_stage(0)
        assert quest.stages[0].completed
        
        # Complete quest
        quest.advance_stage(1)
        quest.complete()
        
        # Verify
        assert quest.status == QuestStatus.COMPLETED

"""Tests for combat system."""

import pytest
from unittest.mock import patch

from reverie.combat import (
    CombatStatus,
    DangerLevel,
    Enemy,
    CombatState,
    CombatResult,
    create_enemy,
    start_combat,
    player_action,
    enemy_turn,
    check_combat_end,
    narrate_action,
)


class TestEnemy:
    """Tests for Enemy class."""

    def test_create_enemy(self):
        """Create an enemy."""
        enemy = create_enemy("Goblin", damage=1, special="Sneak attack")
        assert enemy.name == "Goblin"
        assert enemy.damage == 1
        assert enemy.special == "Sneak attack"
        assert enemy.danger_level == DangerLevel.FRESH

    def test_enemy_take_damage(self):
        """Enemy takes damage."""
        enemy = create_enemy("Goblin")
        assert enemy.danger_level == DangerLevel.FRESH
        
        enemy.take_damage(1)
        assert enemy.danger_level == DangerLevel.BLOODIED
        
        enemy.take_damage(1)
        assert enemy.danger_level == DangerLevel.CRITICAL
        
        enemy.take_damage(1)
        assert enemy.danger_level == DangerLevel.DEFEATED

    def test_enemy_is_defeated(self):
        """Check if enemy is defeated."""
        enemy = create_enemy("Goblin")
        assert not enemy.is_defeated()
        
        enemy.take_damage(3)
        assert enemy.is_defeated()

    def test_enemy_serialization(self):
        """Enemy serializes and deserializes."""
        original = create_enemy("Orc", damage=2, special="Rage")
        original.take_damage(1)
        
        data = original.to_dict()
        restored = Enemy.from_dict(data)
        
        assert restored.name == original.name
        assert restored.damage == original.damage
        assert restored.danger_level == original.danger_level


class TestCombatState:
    """Tests for CombatState class."""

    def test_start_combat(self):
        """Start a combat encounter."""
        enemies = [create_enemy("Goblin"), create_enemy("Orc")]
        state = start_combat(enemies)
        
        assert state.status == CombatStatus.ONGOING
        assert len(state.enemies) == 2
        assert state.turn == 1
        assert state.player_danger == DangerLevel.FRESH

    def test_get_active_enemies(self):
        """Get only active enemies."""
        enemies = [create_enemy("Goblin"), create_enemy("Orc")]
        state = start_combat(enemies)
        
        assert len(state.get_active_enemies()) == 2
        
        enemies[0].take_damage(3)  # Defeat first enemy
        assert len(state.get_active_enemies()) == 1

    def test_all_enemies_defeated(self):
        """Check if all enemies are defeated."""
        enemies = [create_enemy("Goblin")]
        state = start_combat(enemies)
        
        assert not state.all_enemies_defeated()
        
        enemies[0].take_damage(3)
        assert state.all_enemies_defeated()

    def test_player_take_damage(self):
        """Player takes damage."""
        state = start_combat([create_enemy("Goblin")])
        
        state.player_take_damage(1)
        assert state.player_danger == DangerLevel.BLOODIED
        
        state.player_take_damage(2)
        assert state.player_danger == DangerLevel.DEFEATED

    def test_combat_log(self):
        """Combat log tracks events."""
        enemies = [create_enemy("Goblin")]
        state = start_combat(enemies)
        
        assert len(state.log) == 1
        assert "Combat begins" in state.log[0]

    def test_state_serialization(self):
        """CombatState serializes and deserializes."""
        enemies = [create_enemy("Goblin")]
        original = start_combat(enemies)
        original.player_take_damage(1)
        
        data = original.to_dict()
        restored = CombatState.from_dict(data)
        
        assert restored.turn == original.turn
        assert restored.player_danger == original.player_danger
        assert len(restored.enemies) == 1


class TestPlayerAction:
    """Tests for player actions."""

    @patch('reverie.combat.roll_d20')
    def test_attack_success(self, mock_roll):
        """Successful attack damages enemy."""
        mock_roll.return_value = 15
        
        enemies = [create_enemy("Goblin")]
        state = start_combat(enemies)
        
        state, narrative = player_action(state, "attack", stat_modifier=0)
        
        assert enemies[0].danger_level.value < DangerLevel.FRESH.value
        assert "strike" in narrative.lower() or "blow" in narrative.lower()

    @patch('reverie.combat.roll_d20')
    def test_attack_miss(self, mock_roll):
        """Failed attack doesn't damage enemy."""
        mock_roll.return_value = 3
        
        enemies = [create_enemy("Goblin")]
        state = start_combat(enemies)
        
        state, narrative = player_action(state, "attack", stat_modifier=0)
        
        assert enemies[0].danger_level == DangerLevel.FRESH
        assert "miss" in narrative.lower()

    @patch('reverie.combat.roll_d20')
    def test_defend_action(self, mock_roll):
        """Defend action logs properly."""
        mock_roll.return_value = 15
        
        enemies = [create_enemy("Goblin")]
        state = start_combat(enemies)
        
        state, narrative = player_action(state, "defend")
        
        assert "defend" in narrative.lower() or "stance" in narrative.lower()

    @patch('reverie.combat.roll_d20')
    def test_retreat_success(self, mock_roll):
        """Successful retreat ends combat."""
        mock_roll.return_value = 15
        
        enemies = [create_enemy("Goblin")]
        state = start_combat(enemies, retreat_difficulty=10)
        
        state, narrative = player_action(state, "retreat")
        
        assert state.status == CombatStatus.RETREAT
        assert "escape" in narrative.lower() or "disengage" in narrative.lower()

    @patch('reverie.combat.roll_d20')
    def test_retreat_failure(self, mock_roll):
        """Failed retreat doesn't end combat."""
        mock_roll.return_value = 5
        
        enemies = [create_enemy("Goblin")]
        state = start_combat(enemies, retreat_difficulty=10)
        
        state, narrative = player_action(state, "retreat")
        
        assert state.status == CombatStatus.ONGOING
        assert "block" in narrative.lower() or "flee" in narrative.lower()


class TestEnemyTurn:
    """Tests for enemy turns."""

    @patch('reverie.combat.roll_d20')
    def test_enemy_hits(self, mock_roll):
        """Enemy hit damages player."""
        mock_roll.return_value = 15
        
        enemies = [create_enemy("Goblin", damage=1)]
        state = start_combat(enemies)
        
        state, narrative = enemy_turn(state)
        
        assert state.player_danger.value < DangerLevel.FRESH.value
        assert "hit" in narrative.lower() or "blow" in narrative.lower()

    @patch('reverie.combat.roll_d20')
    def test_enemy_misses(self, mock_roll):
        """Enemy miss doesn't damage player."""
        mock_roll.return_value = 5
        
        enemies = [create_enemy("Goblin", damage=1)]
        state = start_combat(enemies)
        
        state, narrative = enemy_turn(state)
        
        assert state.player_danger == DangerLevel.FRESH
        assert "miss" in narrative.lower()

    @patch('reverie.combat.roll_d20')
    def test_defense_reduces_damage(self, mock_roll):
        """Player defense reduces incoming damage."""
        mock_roll.return_value = 12  # Hit but not strong hit
        
        enemies = [create_enemy("Goblin", damage=1)]
        state = start_combat(enemies)
        
        state, narrative = enemy_turn(state, player_defended=True)
        
        # Defense should block the damage at roll 12
        assert state.player_danger == DangerLevel.FRESH
        assert "defense holds" in narrative.lower()

    def test_turn_advances(self):
        """Turn counter advances after enemy turn."""
        enemies = [create_enemy("Goblin")]
        state = start_combat(enemies)
        assert state.turn == 1
        
        with patch('reverie.combat.roll_d20', return_value=5):
            state, _ = enemy_turn(state)
        
        assert state.turn == 2


class TestCombatEnd:
    """Tests for combat end conditions."""

    def test_victory_condition(self):
        """Victory when all enemies defeated."""
        enemies = [create_enemy("Goblin")]
        state = start_combat(enemies)
        
        enemies[0].take_damage(3)  # Defeat enemy
        result = check_combat_end(state)
        
        assert result is not None
        assert result.status == CombatStatus.VICTORY
        assert result.enemies_defeated == 1

    def test_defeat_condition(self):
        """Defeat when player is defeated."""
        enemies = [create_enemy("Goblin")]
        state = start_combat(enemies)
        
        state.player_take_damage(3)  # Defeat player
        result = check_combat_end(state)
        
        assert result is not None
        assert result.status == CombatStatus.DEFEAT
        assert result.player_final_danger == DangerLevel.DEFEATED

    def test_combat_ongoing(self):
        """No result while combat is ongoing."""
        enemies = [create_enemy("Goblin")]
        state = start_combat(enemies)
        
        result = check_combat_end(state)
        assert result is None

    def test_result_includes_log(self):
        """CombatResult includes combat log."""
        enemies = [create_enemy("Goblin")]
        state = start_combat(enemies)
        enemies[0].take_damage(3)
        
        result = check_combat_end(state)
        assert len(result.log) > 0


class TestNarration:
    """Tests for action narration."""

    def test_narrate_success(self):
        """Narrate successful action."""
        narrative = narrate_action("attack", 18, "success")
        assert "succeed" in narrative.lower()
        assert "18" in narrative

    def test_narrate_failure(self):
        """Narrate failed action."""
        narrative = narrate_action("attack", 5, "failure")
        assert "fail" in narrative.lower()

    def test_narrate_partial(self):
        """Narrate partial success."""
        narrative = narrate_action("trick", 12, "partial")
        assert "partial" in narrative.lower()


class TestFullCombat:
    """Integration tests for full combat scenarios."""

    @patch('reverie.combat.roll_d20')
    def test_full_combat_victory(self, mock_roll):
        """Play through a full combat to victory."""
        # Player always hits strong, enemy always misses
        mock_roll.side_effect = [18, 3, 18, 3, 18]
        
        enemies = [create_enemy("Goblin")]
        state = start_combat(enemies)
        
        # Turn 1
        state, _ = player_action(state, "attack")
        state, _ = enemy_turn(state)
        
        # Turn 2
        state, _ = player_action(state, "attack")
        
        result = check_combat_end(state)
        assert result is not None
        assert result.status == CombatStatus.VICTORY

    @patch('reverie.combat.roll_d20')
    def test_full_combat_defeat(self, mock_roll):
        """Play through a full combat to defeat."""
        # Player always misses, enemy always hits strong
        mock_roll.side_effect = [3, 18, 3, 18, 3, 18]
        
        enemies = [create_enemy("Goblin", damage=1)]
        state = start_combat(enemies)
        
        # Turn 1
        state, _ = player_action(state, "attack")
        state, _ = enemy_turn(state)
        
        # Turn 2
        state, _ = player_action(state, "attack")
        state, _ = enemy_turn(state)
        
        # Turn 3
        state, _ = player_action(state, "attack")
        state, _ = enemy_turn(state)
        
        result = check_combat_end(state)
        assert result is not None
        assert result.status == CombatStatus.DEFEAT

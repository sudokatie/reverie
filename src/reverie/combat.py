"""Combat system for Reverie.

Abstract combat without detailed positioning.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
from uuid import uuid4
import random


class CombatStatus(Enum):
    """Status of combat."""
    ONGOING = "ongoing"
    VICTORY = "victory"
    DEFEAT = "defeat"
    RETREAT = "retreat"


class DangerLevel(Enum):
    """Abstract HP as danger level."""
    FRESH = 3      # Full health
    BLOODIED = 2   # Taking damage
    CRITICAL = 1   # Near defeat
    DEFEATED = 0   # Out of combat


@dataclass
class Enemy:
    """An enemy in combat."""
    id: str
    name: str
    danger_level: DangerLevel = DangerLevel.FRESH
    damage: int = 1  # Danger levels dealt per hit
    special: Optional[str] = None  # Special ability description
    
    def is_defeated(self) -> bool:
        """Check if enemy is defeated."""
        return self.danger_level == DangerLevel.DEFEATED
    
    def take_damage(self, amount: int = 1) -> DangerLevel:
        """Take damage, reducing danger level."""
        current = self.danger_level.value
        new_level = max(0, current - amount)
        self.danger_level = DangerLevel(new_level)
        return self.danger_level
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "danger_level": self.danger_level.value,
            "damage": self.damage,
            "special": self.special,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Enemy":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            danger_level=DangerLevel(data.get("danger_level", 3)),
            damage=data.get("damage", 1),
            special=data.get("special"),
        )


@dataclass
class CombatState:
    """Current state of combat."""
    player_danger: DangerLevel = DangerLevel.FRESH
    enemies: list[Enemy] = field(default_factory=list)
    turn: int = 1
    status: CombatStatus = CombatStatus.ONGOING
    log: list[str] = field(default_factory=list)
    retreat_difficulty: int = 10  # DC to retreat
    
    def add_log(self, message: str) -> None:
        """Add a message to the combat log."""
        self.log.append(f"Turn {self.turn}: {message}")
    
    def get_active_enemies(self) -> list[Enemy]:
        """Get enemies still in combat."""
        return [e for e in self.enemies if not e.is_defeated()]
    
    def all_enemies_defeated(self) -> bool:
        """Check if all enemies are defeated."""
        return all(e.is_defeated() for e in self.enemies)
    
    def player_defeated(self) -> bool:
        """Check if player is defeated."""
        return self.player_danger == DangerLevel.DEFEATED
    
    def next_turn(self) -> None:
        """Advance to next turn."""
        self.turn += 1
    
    def player_take_damage(self, amount: int = 1) -> DangerLevel:
        """Player takes damage."""
        current = self.player_danger.value
        new_level = max(0, current - amount)
        self.player_danger = DangerLevel(new_level)
        return self.player_danger
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "player_danger": self.player_danger.value,
            "enemies": [e.to_dict() for e in self.enemies],
            "turn": self.turn,
            "status": self.status.value,
            "log": self.log,
            "retreat_difficulty": self.retreat_difficulty,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CombatState":
        """Deserialize from dictionary."""
        return cls(
            player_danger=DangerLevel(data.get("player_danger", 3)),
            enemies=[Enemy.from_dict(e) for e in data.get("enemies", [])],
            turn=data.get("turn", 1),
            status=CombatStatus(data.get("status", "ongoing")),
            log=data.get("log", []),
            retreat_difficulty=data.get("retreat_difficulty", 10),
        )


@dataclass
class CombatResult:
    """Result of combat."""
    status: CombatStatus
    turns_taken: int
    enemies_defeated: int
    player_final_danger: DangerLevel
    log: list[str]


def create_enemy(
    name: str,
    damage: int = 1,
    special: Optional[str] = None,
) -> Enemy:
    """Create a new enemy."""
    return Enemy(
        id=str(uuid4()),
        name=name,
        damage=damage,
        special=special,
    )


def start_combat(
    enemies: list[Enemy],
    player_danger: DangerLevel = DangerLevel.FRESH,
    retreat_difficulty: int = 10,
) -> CombatState:
    """Start a new combat encounter.
    
    Args:
        enemies: List of enemies to fight
        player_danger: Starting player danger level
        retreat_difficulty: DC to successfully retreat
        
    Returns:
        Initial combat state
    """
    state = CombatState(
        player_danger=player_danger,
        enemies=enemies,
        retreat_difficulty=retreat_difficulty,
    )
    enemy_names = ", ".join(e.name for e in enemies)
    state.add_log(f"Combat begins! Facing: {enemy_names}")
    return state


def roll_d20() -> int:
    """Roll a d20."""
    return random.randint(1, 20)


def player_action(
    state: CombatState,
    action: str,
    stat_modifier: int = 0,
    target_index: int = 0,
) -> tuple[CombatState, str]:
    """Process a player action.
    
    Args:
        state: Current combat state
        action: What the player attempts (attack, defend, retreat, special)
        stat_modifier: Stat bonus to roll
        target_index: Which enemy to target (for attacks)
        
    Returns:
        (Updated state, narrative description)
    """
    if state.status != CombatStatus.ONGOING:
        return state, "Combat has already ended."
    
    roll = roll_d20()
    total = roll + stat_modifier
    
    action_lower = action.lower()
    
    if "attack" in action_lower or "strike" in action_lower or "hit" in action_lower:
        return _handle_attack(state, roll, total, target_index)
    elif "defend" in action_lower or "block" in action_lower or "parry" in action_lower:
        return _handle_defend(state, roll, total)
    elif "retreat" in action_lower or "flee" in action_lower or "run" in action_lower:
        return _handle_retreat(state, roll, total)
    else:
        # Generic action
        return _handle_generic_action(state, action, roll, total)


def _handle_attack(
    state: CombatState,
    roll: int,
    total: int,
    target_index: int,
) -> tuple[CombatState, str]:
    """Handle an attack action."""
    active_enemies = state.get_active_enemies()
    if not active_enemies:
        return state, "No enemies to attack!"
    
    target_index = min(target_index, len(active_enemies) - 1)
    target = active_enemies[target_index]
    
    if total >= 15:
        # Strong hit - deal extra damage
        target.take_damage(2)
        if target.is_defeated():
            narrative = f"Critical strike! {target.name} is defeated!"
        else:
            narrative = f"Powerful blow! {target.name} staggers (now {target.danger_level.name})."
    elif total >= 10:
        # Normal hit
        target.take_damage(1)
        if target.is_defeated():
            narrative = f"You strike true! {target.name} falls!"
        else:
            narrative = f"Your attack lands! {target.name} is now {target.danger_level.name}."
    elif total >= 5:
        # Glancing blow
        narrative = f"Your attack grazes {target.name} but deals no real damage."
    else:
        # Miss
        narrative = f"Your attack misses {target.name} completely."
    
    state.add_log(f"Player attacks {target.name} (roll: {roll}, total: {total})")
    
    # Check for combat end
    result = check_combat_end(state)
    if result:
        state.status = result.status
    
    return state, narrative


def _handle_defend(
    state: CombatState,
    roll: int,
    total: int,
) -> tuple[CombatState, str]:
    """Handle a defend action."""
    if total >= 15:
        narrative = "You take a strong defensive stance, ready for anything."
        # Defense reduces incoming damage (handled in enemy_turn)
        state.add_log(f"Player defends strongly (roll: {roll}, total: {total})")
    elif total >= 10:
        narrative = "You raise your guard, preparing for attacks."
        state.add_log(f"Player defends (roll: {roll}, total: {total})")
    else:
        narrative = "You try to defend but your stance is weak."
        state.add_log(f"Player defends poorly (roll: {roll}, total: {total})")
    
    return state, narrative


def _handle_retreat(
    state: CombatState,
    roll: int,
    total: int,
) -> tuple[CombatState, str]:
    """Handle a retreat action."""
    if total >= state.retreat_difficulty:
        state.status = CombatStatus.RETREAT
        narrative = "You successfully disengage and escape the fight!"
        state.add_log(f"Player retreats successfully (roll: {roll}, total: {total}, DC: {state.retreat_difficulty})")
    else:
        narrative = "You try to flee but the enemies block your escape!"
        state.add_log(f"Player retreat fails (roll: {roll}, total: {total}, DC: {state.retreat_difficulty})")
    
    return state, narrative


def _handle_generic_action(
    state: CombatState,
    action: str,
    roll: int,
    total: int,
) -> tuple[CombatState, str]:
    """Handle a generic/creative action."""
    if total >= 15:
        narrative = f"Your {action} succeeds brilliantly!"
    elif total >= 10:
        narrative = f"Your {action} partially succeeds."
    elif total >= 5:
        narrative = f"Your {action} has little effect."
    else:
        narrative = f"Your {action} fails completely."
    
    state.add_log(f"Player attempts '{action}' (roll: {roll}, total: {total})")
    return state, narrative


def enemy_turn(
    state: CombatState,
    player_defended: bool = False,
) -> tuple[CombatState, str]:
    """Process enemy turns.
    
    Args:
        state: Current combat state
        player_defended: Whether player defended this round
        
    Returns:
        (Updated state, narrative description)
    """
    if state.status != CombatStatus.ONGOING:
        return state, "Combat has already ended."
    
    active_enemies = state.get_active_enemies()
    if not active_enemies:
        return state, "No enemies remain."
    
    narratives = []
    
    for enemy in active_enemies:
        roll = roll_d20()
        
        if roll >= 10:
            # Enemy hits
            damage = enemy.damage
            if player_defended and roll < 15:
                # Defense reduces damage
                damage = max(0, damage - 1)
            
            if damage > 0:
                state.player_take_damage(damage)
                if state.player_defeated():
                    narratives.append(f"{enemy.name} lands a devastating blow! You fall!")
                else:
                    narratives.append(
                        f"{enemy.name} hits you! (Now {state.player_danger.name})"
                    )
            else:
                narratives.append(f"{enemy.name} attacks but your defense holds!")
        else:
            narratives.append(f"{enemy.name} misses!")
        
        state.add_log(f"{enemy.name} attacks (roll: {roll})")
    
    # Check for combat end
    result = check_combat_end(state)
    if result:
        state.status = result.status
    
    # Advance turn
    state.next_turn()
    
    return state, " ".join(narratives)


def check_combat_end(state: CombatState) -> Optional[CombatResult]:
    """Check if combat has ended.
    
    Returns CombatResult if ended, None if ongoing.
    """
    if state.status != CombatStatus.ONGOING:
        # Already ended
        return CombatResult(
            status=state.status,
            turns_taken=state.turn,
            enemies_defeated=len([e for e in state.enemies if e.is_defeated()]),
            player_final_danger=state.player_danger,
            log=state.log,
        )
    
    if state.all_enemies_defeated():
        return CombatResult(
            status=CombatStatus.VICTORY,
            turns_taken=state.turn,
            enemies_defeated=len(state.enemies),
            player_final_danger=state.player_danger,
            log=state.log,
        )
    
    if state.player_defeated():
        return CombatResult(
            status=CombatStatus.DEFEAT,
            turns_taken=state.turn,
            enemies_defeated=len([e for e in state.enemies if e.is_defeated()]),
            player_final_danger=state.player_danger,
            log=state.log,
        )
    
    return None


def narrate_action(
    action: str,
    roll: int,
    outcome: str,
    llm: Optional[Any] = None,
) -> str:
    """Generate narrative for an action.
    
    Args:
        action: What was attempted
        roll: The roll result
        outcome: success/failure/partial
        llm: Optional LLM for rich narration
        
    Returns:
        Narrative text
    """
    if llm is not None:
        # LLM would generate rich narration here
        pass
    
    # Default narration
    if outcome == "success":
        return f"Your {action} succeeds! (Roll: {roll})"
    elif outcome == "partial":
        return f"Your {action} partially succeeds. (Roll: {roll})"
    else:
        return f"Your {action} fails. (Roll: {roll})"

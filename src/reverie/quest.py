"""Quest system for Reverie.

Quest generation, progression, and completion tracking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
from uuid import uuid4


class QuestStatus(Enum):
    """Quest status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


@dataclass
class QuestStage:
    """A stage or objective within a quest."""
    description: str
    completed: bool = False
    
    def complete(self) -> None:
        """Mark this stage as completed."""
        self.completed = True
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "description": self.description,
            "completed": self.completed,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "QuestStage":
        """Deserialize from dictionary."""
        return cls(
            description=data["description"],
            completed=data.get("completed", False),
        )


@dataclass
class QuestReward:
    """Reward for completing a quest."""
    gold: int = 0
    items: list[str] = field(default_factory=list)
    reputation: int = 0
    description: str = ""
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "gold": self.gold,
            "items": self.items,
            "reputation": self.reputation,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "QuestReward":
        """Deserialize from dictionary."""
        return cls(
            gold=data.get("gold", 0),
            items=data.get("items", []),
            reputation=data.get("reputation", 0),
            description=data.get("description", ""),
        )


@dataclass
class Quest:
    """A quest with objectives and rewards."""
    id: str
    title: str
    hook: str  # How player learns of quest
    objective: str  # Main goal
    complications: list[str] = field(default_factory=list)  # 2-3 obstacles
    resolutions: list[str] = field(default_factory=list)  # Possible endings
    rewards: QuestReward = field(default_factory=QuestReward)
    stages: list[QuestStage] = field(default_factory=list)
    status: QuestStatus = QuestStatus.ACTIVE
    giver_id: Optional[str] = None  # NPC who gave quest
    failure_reason: Optional[str] = None
    chosen_resolution: Optional[int] = None
    
    def is_active(self) -> bool:
        """Check if quest is still active."""
        return self.status == QuestStatus.ACTIVE
    
    def get_current_stage(self) -> Optional[QuestStage]:
        """Get the first incomplete stage."""
        for stage in self.stages:
            if not stage.completed:
                return stage
        return None
    
    def get_completed_stages(self) -> list[QuestStage]:
        """Get all completed stages."""
        return [s for s in self.stages if s.completed]
    
    def get_progress(self) -> tuple[int, int]:
        """Get (completed, total) stage counts."""
        completed = len([s for s in self.stages if s.completed])
        return completed, len(self.stages)
    
    def advance_stage(self, stage_index: int) -> bool:
        """Mark a specific stage as completed.
        
        Returns True if successful.
        """
        if not self.is_active():
            return False
        if 0 <= stage_index < len(self.stages):
            self.stages[stage_index].complete()
            return True
        return False
    
    def complete(self, resolution_index: int = 0) -> bool:
        """Complete the quest with a specific resolution.
        
        Returns True if successful.
        """
        if not self.is_active():
            return False
        if 0 <= resolution_index < len(self.resolutions):
            self.chosen_resolution = resolution_index
        self.status = QuestStatus.COMPLETED
        return True
    
    def fail(self, reason: str) -> bool:
        """Fail the quest.
        
        Returns True if successful.
        """
        if not self.is_active():
            return False
        self.status = QuestStatus.FAILED
        self.failure_reason = reason
        return True
    
    def abandon(self) -> bool:
        """Abandon the quest.
        
        Returns True if successful.
        """
        if not self.is_active():
            return False
        self.status = QuestStatus.ABANDONED
        return True
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "hook": self.hook,
            "objective": self.objective,
            "complications": self.complications,
            "resolutions": self.resolutions,
            "rewards": self.rewards.to_dict(),
            "stages": [s.to_dict() for s in self.stages],
            "status": self.status.value,
            "giver_id": self.giver_id,
            "failure_reason": self.failure_reason,
            "chosen_resolution": self.chosen_resolution,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Quest":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            hook=data.get("hook", ""),
            objective=data.get("objective", ""),
            complications=data.get("complications", []),
            resolutions=data.get("resolutions", []),
            rewards=QuestReward.from_dict(data.get("rewards", {})),
            stages=[QuestStage.from_dict(s) for s in data.get("stages", [])],
            status=QuestStatus(data.get("status", "active")),
            giver_id=data.get("giver_id"),
            failure_reason=data.get("failure_reason"),
            chosen_resolution=data.get("chosen_resolution"),
        )


# Generation and helper functions

def generate_quest(
    npc: Optional[Any] = None,
    context: Optional[dict[str, Any]] = None,
    llm: Optional[Any] = None,
) -> Quest:
    """Generate a new quest.
    
    Args:
        npc: Optional NPC giving the quest
        context: Optional context (location, player info)
        llm: Optional LLM for generation
        
    Returns:
        A new Quest instance
    """
    context = context or {}
    
    title = context.get("title", "A Mysterious Task")
    hook = context.get("hook", "An opportunity presents itself.")
    objective = context.get("objective", "Complete the task.")
    complications = context.get("complications", [
        "An unexpected obstacle appears.",
        "Things are not as they seem.",
    ])
    resolutions = context.get("resolutions", [
        "Complete the objective as requested.",
        "Find an alternative solution.",
    ])
    
    # Build stages from objective and complications
    stages = [QuestStage(description=objective)]
    for complication in complications:
        stages.append(QuestStage(description=f"Overcome: {complication}"))
    
    rewards = QuestReward(
        gold=context.get("gold", 100),
        items=context.get("items", []),
        reputation=context.get("reputation", 5),
        description=context.get("reward_description", "A fair reward for your efforts."),
    )
    
    giver_id = None
    if npc is not None:
        giver_id = getattr(npc, "id", None)
    
    return Quest(
        id=str(uuid4()),
        title=title,
        hook=hook,
        objective=objective,
        complications=complications,
        resolutions=resolutions,
        rewards=rewards,
        stages=stages,
        giver_id=giver_id,
    )


def advance_quest(quest: Quest, stage_index: int) -> bool:
    """Advance a quest by completing a stage.
    
    Args:
        quest: The quest to advance
        stage_index: Index of stage to complete
        
    Returns:
        True if successful
    """
    return quest.advance_stage(stage_index)


def complete_quest(quest: Quest, resolution_index: int = 0) -> bool:
    """Complete a quest with a specific resolution.
    
    Args:
        quest: The quest to complete
        resolution_index: Index of chosen resolution
        
    Returns:
        True if successful
    """
    return quest.complete(resolution_index)


def fail_quest(quest: Quest, reason: str) -> bool:
    """Fail a quest.
    
    Args:
        quest: The quest to fail
        reason: Why it failed
        
    Returns:
        True if successful
    """
    return quest.fail(reason)


def get_active_quests(quests: list[Quest]) -> list[Quest]:
    """Get all active quests from a list.
    
    Args:
        quests: List of all quests
        
    Returns:
        List of active quests only
    """
    return [q for q in quests if q.is_active()]


def get_completed_quests(quests: list[Quest]) -> list[Quest]:
    """Get all completed quests from a list.
    
    Args:
        quests: List of all quests
        
    Returns:
        List of completed quests only
    """
    return [q for q in quests if q.status == QuestStatus.COMPLETED]


def get_failed_quests(quests: list[Quest]) -> list[Quest]:
    """Get all failed quests from a list.
    
    Args:
        quests: List of all quests
        
    Returns:
        List of failed quests only
    """
    return [q for q in quests if q.status == QuestStatus.FAILED]

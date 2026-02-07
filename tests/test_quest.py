"""Tests for quest system."""

import pytest

from reverie.quest import (
    QuestStatus,
    QuestStage,
    QuestReward,
    Quest,
    generate_quest,
    advance_quest,
    complete_quest,
    fail_quest,
    get_active_quests,
    get_completed_quests,
    get_failed_quests,
)


class TestQuestStage:
    """Tests for QuestStage class."""

    def test_create_stage(self):
        """Create a quest stage."""
        stage = QuestStage(description="Find the artifact")
        assert stage.description == "Find the artifact"
        assert not stage.completed

    def test_complete_stage(self):
        """Mark stage as completed."""
        stage = QuestStage(description="Test")
        stage.complete()
        assert stage.completed

    def test_stage_serialization(self):
        """Stage serializes and deserializes."""
        original = QuestStage(description="Test stage", completed=True)
        data = original.to_dict()
        restored = QuestStage.from_dict(data)
        assert restored.description == original.description
        assert restored.completed == original.completed


class TestQuestReward:
    """Tests for QuestReward class."""

    def test_create_reward(self):
        """Create a quest reward."""
        reward = QuestReward(
            gold=500,
            items=["Magic Sword", "Healing Potion"],
            reputation=10,
            description="The grateful king rewards you.",
        )
        assert reward.gold == 500
        assert len(reward.items) == 2
        assert reward.reputation == 10

    def test_reward_serialization(self):
        """Reward serializes and deserializes."""
        original = QuestReward(gold=100, items=["Item"], reputation=5)
        data = original.to_dict()
        restored = QuestReward.from_dict(data)
        assert restored.gold == original.gold
        assert restored.items == original.items


class TestQuest:
    """Tests for Quest class."""

    def test_create_quest(self):
        """Create a quest."""
        quest = Quest(
            id="quest-1",
            title="The Lost Artifact",
            hook="A mysterious stranger approaches you.",
            objective="Find the ancient artifact.",
            complications=["The dungeon is trapped.", "A rival seeks it too."],
            resolutions=["Return it to the stranger.", "Keep it for yourself."],
        )
        assert quest.title == "The Lost Artifact"
        assert quest.is_active()

    def test_get_current_stage(self):
        """Get the current incomplete stage."""
        quest = Quest(
            id="quest-1",
            title="Test",
            hook="Hook",
            objective="Objective",
            stages=[
                QuestStage("Stage 1", completed=True),
                QuestStage("Stage 2", completed=False),
                QuestStage("Stage 3", completed=False),
            ],
        )
        current = quest.get_current_stage()
        assert current.description == "Stage 2"

    def test_get_progress(self):
        """Get quest progress."""
        quest = Quest(
            id="quest-1",
            title="Test",
            hook="Hook",
            objective="Objective",
            stages=[
                QuestStage("Stage 1", completed=True),
                QuestStage("Stage 2", completed=True),
                QuestStage("Stage 3", completed=False),
            ],
        )
        completed, total = quest.get_progress()
        assert completed == 2
        assert total == 3

    def test_advance_stage(self):
        """Advance a quest stage."""
        quest = Quest(
            id="quest-1",
            title="Test",
            hook="Hook",
            objective="Objective",
            stages=[QuestStage("Stage 1"), QuestStage("Stage 2")],
        )
        assert quest.advance_stage(0)
        assert quest.stages[0].completed
        assert not quest.stages[1].completed

    def test_advance_invalid_stage(self):
        """Cannot advance invalid stage index."""
        quest = Quest(id="quest-1", title="Test", hook="Hook", objective="Obj")
        assert not quest.advance_stage(999)

    def test_complete_quest(self):
        """Complete a quest."""
        quest = Quest(
            id="quest-1",
            title="Test",
            hook="Hook",
            objective="Objective",
            resolutions=["Resolution A", "Resolution B"],
        )
        assert quest.complete(1)
        assert quest.status == QuestStatus.COMPLETED
        assert quest.chosen_resolution == 1

    def test_complete_already_completed(self):
        """Cannot complete already completed quest."""
        quest = Quest(id="quest-1", title="Test", hook="Hook", objective="Obj")
        quest.complete()
        assert not quest.complete()  # Already completed

    def test_fail_quest(self):
        """Fail a quest."""
        quest = Quest(id="quest-1", title="Test", hook="Hook", objective="Obj")
        assert quest.fail("The artifact was destroyed.")
        assert quest.status == QuestStatus.FAILED
        assert quest.failure_reason == "The artifact was destroyed."

    def test_fail_already_failed(self):
        """Cannot fail already failed quest."""
        quest = Quest(id="quest-1", title="Test", hook="Hook", objective="Obj")
        quest.fail("Reason 1")
        assert not quest.fail("Reason 2")

    def test_abandon_quest(self):
        """Abandon a quest."""
        quest = Quest(id="quest-1", title="Test", hook="Hook", objective="Obj")
        assert quest.abandon()
        assert quest.status == QuestStatus.ABANDONED

    def test_quest_serialization(self):
        """Quest serializes and deserializes."""
        original = Quest(
            id="quest-1",
            title="Test Quest",
            hook="Hook text",
            objective="Do the thing",
            complications=["Problem 1"],
            resolutions=["Solution 1"],
            rewards=QuestReward(gold=100),
            stages=[QuestStage("Stage 1")],
            giver_id="npc-1",
        )
        data = original.to_dict()
        restored = Quest.from_dict(data)
        
        assert restored.title == original.title
        assert restored.giver_id == original.giver_id
        assert len(restored.stages) == 1
        assert restored.rewards.gold == 100


class TestGeneration:
    """Tests for quest generation."""

    def test_generate_quest_defaults(self):
        """Generate quest with defaults."""
        quest = generate_quest()
        assert quest.id is not None
        assert quest.title == "A Mysterious Task"
        assert quest.is_active()
        assert len(quest.stages) > 0

    def test_generate_quest_with_context(self):
        """Generate quest with custom context."""
        quest = generate_quest(context={
            "title": "Dragon Slayer",
            "hook": "The village is under attack!",
            "objective": "Defeat the dragon.",
            "gold": 1000,
            "reputation": 20,
        })
        assert quest.title == "Dragon Slayer"
        assert quest.rewards.gold == 1000
        assert quest.rewards.reputation == 20

    def test_generate_quest_with_npc(self):
        """Generate quest with NPC giver."""
        class MockNPC:
            id = "npc-123"
        
        quest = generate_quest(npc=MockNPC())
        assert quest.giver_id == "npc-123"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_advance_quest_function(self):
        """advance_quest helper works."""
        quest = generate_quest()
        assert advance_quest(quest, 0)
        assert quest.stages[0].completed

    def test_complete_quest_function(self):
        """complete_quest helper works."""
        quest = generate_quest()
        assert complete_quest(quest, 0)
        assert quest.status == QuestStatus.COMPLETED

    def test_fail_quest_function(self):
        """fail_quest helper works."""
        quest = generate_quest()
        assert fail_quest(quest, "Time ran out")
        assert quest.status == QuestStatus.FAILED

    def test_get_active_quests(self):
        """Filter active quests."""
        quests = [
            generate_quest(context={"title": "Quest 1"}),
            generate_quest(context={"title": "Quest 2"}),
            generate_quest(context={"title": "Quest 3"}),
        ]
        quests[1].complete()
        quests[2].fail("Failed")
        
        active = get_active_quests(quests)
        assert len(active) == 1
        assert active[0].title == "Quest 1"

    def test_get_completed_quests(self):
        """Filter completed quests."""
        quests = [
            generate_quest(context={"title": "Quest 1"}),
            generate_quest(context={"title": "Quest 2"}),
        ]
        quests[0].complete()
        
        completed = get_completed_quests(quests)
        assert len(completed) == 1
        assert completed[0].title == "Quest 1"

    def test_get_failed_quests(self):
        """Filter failed quests."""
        quests = [
            generate_quest(context={"title": "Quest 1"}),
            generate_quest(context={"title": "Quest 2"}),
        ]
        quests[1].fail("Failed")
        
        failed = get_failed_quests(quests)
        assert len(failed) == 1
        assert failed[0].title == "Quest 2"

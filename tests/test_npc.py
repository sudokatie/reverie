"""Tests for NPC system."""

import pytest

from reverie.npc import (
    Disposition,
    Promise,
    Gift,
    ReputationChange,
    NPCMemory,
    NPC,
    generate_npc,
    update_disposition,
    add_conversation,
    add_promise,
    get_relationship_summary,
)


class TestNPCMemory:
    """Tests for NPCMemory class."""

    def test_add_conversation(self):
        """Add conversation summaries."""
        memory = NPCMemory()
        memory.add_conversation("Discussed the weather")
        memory.add_conversation("Talked about the tavern")
        assert len(memory.conversations) == 2

    def test_add_promise(self):
        """Add promises."""
        memory = NPCMemory()
        memory.add_promise("Bring medicine from town")
        assert len(memory.promises) == 1
        assert not memory.promises[0].fulfilled

    def test_fulfill_promise(self):
        """Fulfill a promise."""
        memory = NPCMemory()
        memory.add_promise("Defeat the bandits")
        assert memory.fulfill_promise(0)
        assert memory.promises[0].fulfilled

    def test_fulfill_invalid_promise(self):
        """Fulfill invalid index returns False."""
        memory = NPCMemory()
        assert not memory.fulfill_promise(0)
        assert not memory.fulfill_promise(-1)

    def test_get_unfulfilled_promises(self):
        """Get only unfulfilled promises."""
        memory = NPCMemory()
        memory.add_promise("Promise 1", fulfilled=True)
        memory.add_promise("Promise 2", fulfilled=False)
        memory.add_promise("Promise 3", fulfilled=False)
        
        unfulfilled = memory.get_unfulfilled_promises()
        assert len(unfulfilled) == 2

    def test_add_gift(self):
        """Record gifts."""
        memory = NPCMemory()
        memory.add_gift("Healing Potion", 50)
        memory.add_gift("Gold Ring", 100)
        assert len(memory.gifts) == 2
        assert memory.get_gift_value_total() == 150

    def test_add_reputation_change(self):
        """Track reputation changes."""
        memory = NPCMemory()
        memory.add_reputation_change(5, "Helped with quest")
        memory.add_reputation_change(-3, "Broke a promise")
        assert memory.get_total_reputation() == 2

    def test_memory_serialization(self):
        """Memory serializes and deserializes."""
        original = NPCMemory()
        original.add_conversation("Test conversation")
        original.add_promise("Test promise")
        original.add_gift("Test item", 25)
        original.add_reputation_change(10, "Good deed")
        
        data = original.to_dict()
        restored = NPCMemory.from_dict(data)
        
        assert restored.conversations == original.conversations
        assert len(restored.promises) == 1
        assert len(restored.gifts) == 1
        assert restored.get_total_reputation() == 10


class TestNPC:
    """Tests for NPC class."""

    def test_create_npc(self):
        """Create an NPC."""
        npc = NPC(
            id="npc-1",
            name="Bartender",
            race="dwarf",
            occupation="innkeeper",
            traits=["gruff", "honest"],
            motivation="keep the inn running",
        )
        assert npc.name == "Bartender"
        assert npc.race == "dwarf"
        assert len(npc.traits) == 2
        assert npc.disposition == Disposition.NEUTRAL

    def test_update_disposition_positive(self):
        """Positive changes improve disposition."""
        npc = NPC(id="npc-1", name="Test", race="human", occupation="guard")
        
        npc.update_disposition(5, "Helped with task")
        assert npc.disposition == Disposition.FRIENDLY
        
        npc.update_disposition(5, "Another good deed")
        assert npc.disposition == Disposition.ALLIED

    def test_update_disposition_negative(self):
        """Negative changes worsen disposition."""
        npc = NPC(id="npc-1", name="Test", race="human", occupation="guard")
        
        npc.update_disposition(-5, "Insulted them")
        assert npc.disposition == Disposition.UNFRIENDLY
        
        npc.update_disposition(-5, "Attacked them")
        assert npc.disposition == Disposition.HOSTILE

    def test_relationship_summary(self):
        """Get relationship summary."""
        npc = NPC(id="npc-1", name="Elara", race="elf", occupation="healer")
        npc.memory.add_conversation("Discussed herbs")
        npc.update_disposition(5, "Helped gather herbs")
        
        summary = npc.get_relationship_summary()
        assert "Elara" in summary
        assert "friendly" in summary
        assert "+5" in summary

    def test_npc_serialization(self):
        """NPC serializes and deserializes."""
        original = NPC(
            id="npc-1",
            name="Test NPC",
            race="elf",
            occupation="mage",
            traits=["wise", "aloof"],
            motivation="study magic",
            secret="Actually a dragon in disguise",
            disposition=Disposition.FRIENDLY,
        )
        original.memory.add_conversation("Test")
        
        data = original.to_dict()
        restored = NPC.from_dict(data)
        
        assert restored.name == original.name
        assert restored.secret == original.secret
        assert restored.disposition == Disposition.FRIENDLY
        assert len(restored.memory.conversations) == 1


class TestGeneration:
    """Tests for generation functions."""

    def test_generate_npc_defaults(self):
        """Generate NPC with defaults."""
        npc = generate_npc()
        assert npc.id is not None
        assert npc.name == "Unnamed Stranger"
        assert npc.disposition == Disposition.NEUTRAL

    def test_generate_npc_with_context(self):
        """Generate NPC with custom context."""
        npc = generate_npc(context={
            "name": "Captain Vex",
            "race": "half-orc",
            "occupation": "mercenary captain",
            "traits": ["brave", "ruthless"],
            "motivation": "gold and glory",
            "secret": "Wanted for war crimes",
            "disposition": "unfriendly",
        })
        assert npc.name == "Captain Vex"
        assert npc.race == "half-orc"
        assert npc.secret == "Wanted for war crimes"
        assert npc.disposition == Disposition.UNFRIENDLY

    def test_traits_limited_to_two(self):
        """Only first 2 traits are kept."""
        npc = generate_npc(context={
            "traits": ["a", "b", "c", "d"],
        })
        assert len(npc.traits) == 2


class TestHelperFunctions:
    """Tests for module-level helper functions."""

    def test_update_disposition_function(self):
        """update_disposition helper works."""
        npc = generate_npc()
        new_disp = update_disposition(npc, 10, "Major favor")
        assert new_disp == Disposition.ALLIED

    def test_add_conversation_function(self):
        """add_conversation helper works."""
        npc = generate_npc()
        add_conversation(npc, "Talked about the quest")
        assert len(npc.memory.conversations) == 1

    def test_add_promise_function(self):
        """add_promise helper works."""
        npc = generate_npc()
        add_promise(npc, "Will return with the artifact")
        assert len(npc.memory.promises) == 1

    def test_get_relationship_summary_function(self):
        """get_relationship_summary helper works."""
        npc = generate_npc(context={"name": "Test NPC"})
        summary = get_relationship_summary(npc)
        assert "Test NPC" in summary

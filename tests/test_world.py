"""Tests for world generation."""

import pytest

from reverie.world import (
    ElementType,
    WorldElement,
    Location,
    Region,
    generate_region,
    generate_settlement,
    generate_dungeon,
    generate_wilderness,
    get_connected_locations,
    filter_by_tag,
    filter_by_type,
)


class TestWorldElement:
    """Tests for WorldElement base class."""

    def test_create_element(self):
        """Create a basic world element."""
        element = WorldElement(
            id="test-1",
            element_type=ElementType.REGION,
            name="Test Region",
            description="A test region.",
        )
        assert element.id == "test-1"
        assert element.name == "Test Region"
        assert element.element_type == ElementType.REGION

    def test_has_tag_case_insensitive(self):
        """Tag matching is case-insensitive."""
        element = WorldElement(
            id="test-1",
            element_type=ElementType.REGION,
            name="Test",
            description="Test",
            tags=["Forest", "Dangerous"],
        )
        assert element.has_tag("forest")
        assert element.has_tag("DANGEROUS")
        assert not element.has_tag("mountain")

    def test_add_connection(self):
        """Add connections between elements."""
        element = WorldElement(
            id="test-1",
            element_type=ElementType.REGION,
            name="Test",
            description="Test",
        )
        element.add_connection("test-2")
        assert "test-2" in element.connections
        
        # Adding same connection twice is idempotent
        element.add_connection("test-2")
        assert element.connections.count("test-2") == 1

    def test_remove_connection(self):
        """Remove connections."""
        element = WorldElement(
            id="test-1",
            element_type=ElementType.REGION,
            name="Test",
            description="Test",
            connections=["test-2", "test-3"],
        )
        assert element.remove_connection("test-2")
        assert "test-2" not in element.connections
        assert not element.remove_connection("nonexistent")


class TestSecrets:
    """Tests for secret revelation."""

    def test_reveal_secret(self):
        """Reveal a secret by index."""
        element = WorldElement(
            id="test-1",
            element_type=ElementType.DUNGEON,
            name="Test Dungeon",
            description="Test",
            secrets=["Secret 1", "Secret 2", "Secret 3"],
        )
        secret = element.reveal_secret(0)
        assert secret == "Secret 1"
        assert 0 in element.revealed_secrets

    def test_reveal_same_secret_twice_returns_none(self):
        """Revealing same secret twice returns None."""
        element = WorldElement(
            id="test-1",
            element_type=ElementType.DUNGEON,
            name="Test",
            description="Test",
            secrets=["Secret 1"],
        )
        assert element.reveal_secret(0) == "Secret 1"
        assert element.reveal_secret(0) is None

    def test_reveal_invalid_index(self):
        """Revealing invalid index returns None."""
        element = WorldElement(
            id="test-1",
            element_type=ElementType.DUNGEON,
            name="Test",
            description="Test",
            secrets=["Secret 1"],
        )
        assert element.reveal_secret(10) is None
        assert element.reveal_secret(-1) is None

    def test_get_revealed_secrets(self):
        """Get all revealed secrets."""
        element = WorldElement(
            id="test-1",
            element_type=ElementType.DUNGEON,
            name="Test",
            description="Test",
            secrets=["Secret 1", "Secret 2", "Secret 3"],
        )
        element.reveal_secret(0)
        element.reveal_secret(2)
        
        revealed = element.get_revealed_secrets()
        assert len(revealed) == 2
        assert "Secret 1" in revealed
        assert "Secret 3" in revealed

    def test_hidden_secret_count(self):
        """Count unrevealed secrets."""
        element = WorldElement(
            id="test-1",
            element_type=ElementType.DUNGEON,
            name="Test",
            description="Test",
            secrets=["Secret 1", "Secret 2", "Secret 3"],
        )
        assert element.get_hidden_secret_count() == 3
        element.reveal_secret(0)
        assert element.get_hidden_secret_count() == 2


class TestLocation:
    """Tests for Location class."""

    def test_create_location_with_exits(self):
        """Create a location with exits."""
        loc = Location(
            id="loc-1",
            element_type=ElementType.SETTLEMENT,
            name="Village",
            description="A small village.",
            exits={"north": "loc-2", "east": "loc-3"},
        )
        assert len(loc.exits) == 2
        assert loc.exits["north"] == "loc-2"

    def test_add_exit(self):
        """Add an exit to a location."""
        loc = Location(
            id="loc-1",
            element_type=ElementType.SETTLEMENT,
            name="Village",
            description="A small village.",
        )
        loc.add_exit("North", "loc-2")
        assert loc.exits["north"] == "loc-2"  # Normalized to lowercase

    def test_remove_exit(self):
        """Remove an exit from a location."""
        loc = Location(
            id="loc-1",
            element_type=ElementType.SETTLEMENT,
            name="Village",
            description="A small village.",
            exits={"north": "loc-2"},
        )
        assert loc.remove_exit("north")
        assert "north" not in loc.exits
        assert not loc.remove_exit("south")

    def test_get_exit_directions(self):
        """Get all available exit directions."""
        loc = Location(
            id="loc-1",
            element_type=ElementType.SETTLEMENT,
            name="Village",
            description="A small village.",
            exits={"north": "loc-2", "east": "loc-3"},
        )
        directions = loc.get_exit_directions()
        assert "north" in directions
        assert "east" in directions


class TestRegion:
    """Tests for Region class."""

    def test_create_region(self):
        """Create a region with properties."""
        region = Region(
            id="reg-1",
            element_type=ElementType.REGION,
            name="The Northern Wastes",
            description="A frozen wasteland.",
            climate="arctic",
            terrain="tundra",
            culture="nomadic tribes",
        )
        assert region.climate == "arctic"
        assert region.terrain == "tundra"
        assert region.culture == "nomadic tribes"

    def test_add_settlement_to_region(self):
        """Add a settlement to a region."""
        region = Region(
            id="reg-1",
            element_type=ElementType.REGION,
            name="Test Region",
            description="Test",
        )
        region.add_settlement("set-1")
        assert "set-1" in region.settlements
        assert "set-1" in region.connections

    def test_add_dungeon_to_region(self):
        """Add a dungeon to a region."""
        region = Region(
            id="reg-1",
            element_type=ElementType.REGION,
            name="Test Region",
            description="Test",
        )
        region.add_dungeon("dun-1")
        assert "dun-1" in region.dungeons
        assert "dun-1" in region.connections


class TestGeneration:
    """Tests for generation functions."""

    def test_generate_region_defaults(self):
        """Generate region with default constraints."""
        region = generate_region()
        assert region.id is not None
        assert region.element_type == ElementType.REGION
        assert region.climate == "temperate"
        assert region.terrain == "plains"

    def test_generate_region_with_constraints(self):
        """Generate region with custom constraints."""
        region = generate_region(constraints={
            "climate": "tropical",
            "terrain": "jungle",
            "culture": "ancient empire",
            "name": "The Emerald Expanse",
        })
        assert region.climate == "tropical"
        assert region.terrain == "jungle"
        assert region.name == "The Emerald Expanse"

    def test_generate_settlement(self):
        """Generate a settlement in a region."""
        region = generate_region()
        settlement = generate_settlement(region, constraints={
            "size": "city",
            "government": "council",
        })
        assert settlement.element_type == ElementType.SETTLEMENT
        assert "city" in settlement.tags
        assert settlement.id in region.settlements

    def test_generate_dungeon(self):
        """Generate a dungeon in a region."""
        region = generate_region()
        dungeon = generate_dungeon(region, constraints={
            "theme": "undead",
            "difficulty": "hard",
        })
        assert dungeon.element_type == ElementType.DUNGEON
        assert "undead" in dungeon.tags
        assert dungeon.id in region.dungeons

    def test_generate_wilderness(self):
        """Generate wilderness in a region."""
        region = generate_region(constraints={"terrain": "forest"})
        wilderness = generate_wilderness(region)
        assert wilderness.element_type == ElementType.WILDERNESS
        assert "forest" in wilderness.tags
        assert wilderness.id in region.wilderness_areas


class TestConnections:
    """Tests for connection utilities."""

    def test_get_connected_locations(self):
        """Get all connected locations."""
        region = generate_region()
        settlement = generate_settlement(region)
        dungeon = generate_dungeon(region)
        
        elements = {
            region.id: region,
            settlement.id: settlement,
            dungeon.id: dungeon,
        }
        
        connected = get_connected_locations(region.id, elements)
        assert len(connected) == 2
        assert settlement in connected
        assert dungeon in connected

    def test_get_connected_locations_missing_element(self):
        """Handle missing element gracefully."""
        connected = get_connected_locations("nonexistent", {})
        assert connected == []


class TestFiltering:
    """Tests for filtering utilities."""

    def test_filter_by_tag(self):
        """Filter elements by tag."""
        elements = [
            WorldElement(id="1", element_type=ElementType.SETTLEMENT, name="A", description="", tags=["forest"]),
            WorldElement(id="2", element_type=ElementType.SETTLEMENT, name="B", description="", tags=["mountain"]),
            WorldElement(id="3", element_type=ElementType.DUNGEON, name="C", description="", tags=["forest", "dark"]),
        ]
        filtered = filter_by_tag(elements, "forest")
        assert len(filtered) == 2

    def test_filter_by_type(self):
        """Filter elements by type."""
        elements = [
            WorldElement(id="1", element_type=ElementType.SETTLEMENT, name="A", description=""),
            WorldElement(id="2", element_type=ElementType.DUNGEON, name="B", description=""),
            WorldElement(id="3", element_type=ElementType.SETTLEMENT, name="C", description=""),
        ]
        filtered = filter_by_type(elements, ElementType.SETTLEMENT)
        assert len(filtered) == 2


class TestSerialization:
    """Tests for serialization."""

    def test_world_element_roundtrip(self):
        """WorldElement serializes and deserializes."""
        original = WorldElement(
            id="test-1",
            element_type=ElementType.REGION,
            name="Test",
            description="Test desc",
            tags=["tag1", "tag2"],
            secrets=["secret1"],
            connections=["conn1"],
            revealed_secrets=[0],
        )
        data = original.to_dict()
        restored = WorldElement.from_dict(data)
        
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.tags == original.tags
        assert restored.revealed_secrets == original.revealed_secrets

    def test_location_roundtrip(self):
        """Location serializes and deserializes."""
        original = Location(
            id="loc-1",
            element_type=ElementType.SETTLEMENT,
            name="Village",
            description="A village",
            exits={"north": "loc-2"},
        )
        data = original.to_dict()
        restored = Location.from_dict(data)
        
        assert restored.exits == original.exits

    def test_region_roundtrip(self):
        """Region serializes and deserializes."""
        original = Region(
            id="reg-1",
            element_type=ElementType.REGION,
            name="Region",
            description="A region",
            climate="arctic",
            terrain="tundra",
            culture="nomads",
            settlements=["set-1"],
            dungeons=["dun-1"],
        )
        data = original.to_dict()
        restored = Region.from_dict(data)
        
        assert restored.climate == original.climate
        assert restored.settlements == original.settlements

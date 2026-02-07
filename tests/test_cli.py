"""Tests for the Reverie CLI."""

import json
import pytest
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from reverie.cli import app, get_database, create_default_character
from reverie.storage.database import Database
from reverie.storage.models import Campaign
from reverie.character import PlayerClass


runner = CliRunner()


@pytest.fixture
def mock_db(tmp_path):
    """Create a mock database."""
    db_path = tmp_path / "test.db"
    db = Database.open(db_path)
    return db


@pytest.fixture
def mock_db_with_campaign(mock_db):
    """Create a mock database with a campaign."""
    campaign = Campaign.create("Test Adventure")
    mock_db.save_campaign(campaign)
    return mock_db, campaign


class TestCreateDefaultCharacter:
    """Tests for create_default_character function."""
    
    def test_default_character_name(self):
        """Test default character has default name."""
        char = create_default_character()
        assert char.name == "Adventurer"
    
    def test_custom_character_name(self):
        """Test custom character name."""
        char = create_default_character("Hero")
        assert char.name == "Hero"
    
    def test_default_character_class(self):
        """Test default character class is Wanderer."""
        char = create_default_character()
        assert char.player_class == PlayerClass.WANDERER
    
    def test_default_character_stats(self):
        """Test default character has balanced stats."""
        char = create_default_character()
        assert char.stats.might == 4
        assert char.stats.wit == 4
        assert char.stats.spirit == 4


class TestListCommand:
    """Tests for the list command."""
    
    def test_list_empty(self, tmp_path):
        """Test list with no campaigns."""
        with patch("reverie.cli.get_db_path", return_value=tmp_path / "test.db"):
            result = runner.invoke(app, ["list"])
            assert result.exit_code == 0
            assert "No saved campaigns" in result.output
    
    def test_list_with_campaigns(self, tmp_path):
        """Test list with existing campaigns."""
        db_path = tmp_path / "test.db"
        db = Database.open(db_path)
        campaign = Campaign.create("My Adventure")
        db.save_campaign(campaign)
        db.close()
        
        with patch("reverie.cli.get_db_path", return_value=db_path):
            result = runner.invoke(app, ["list"])
            assert result.exit_code == 0
            assert "My Adventure" in result.output


class TestConfigCommand:
    """Tests for the config command."""
    
    def test_config_show(self, tmp_path):
        """Test showing config."""
        config_path = tmp_path / "config.toml"
        
        with patch("reverie.cli.get_config_path", return_value=config_path):
            result = runner.invoke(app, ["config", "--show"])
            assert result.exit_code == 0
            assert "Config file:" in result.output


class TestExportImport:
    """Tests for export and import commands."""
    
    def test_export_campaign(self, tmp_path):
        """Test exporting a campaign."""
        db_path = tmp_path / "test.db"
        db = Database.open(db_path)
        campaign = Campaign.create("Export Test")
        db.save_campaign(campaign)
        db.close()
        
        output_file = tmp_path / "export.json"
        
        with patch("reverie.cli.get_db_path", return_value=db_path):
            result = runner.invoke(app, ["export", "Export Test", "-o", str(output_file)])
            assert result.exit_code == 0
            assert output_file.exists()
    
    def test_import_campaign(self, tmp_path):
        """Test importing a campaign."""
        db_path = tmp_path / "test.db"
        
        # Create export file
        export_data = {
            "campaign": {
                "id": "test-123",
                "name": "Imported Campaign",
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
                "playtime_seconds": 0,
            }
        }
        import_file = tmp_path / "import.json"
        with open(import_file, "w") as f:
            json.dump(export_data, f)
        
        with patch("reverie.cli.get_db_path", return_value=db_path):
            result = runner.invoke(app, ["import", str(import_file)])
            assert result.exit_code == 0
            assert "Imported campaign" in result.output
    
    def test_import_nonexistent_file(self, tmp_path):
        """Test importing from nonexistent file."""
        result = runner.invoke(app, ["import", str(tmp_path / "nonexistent.json")])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestDeleteCommand:
    """Tests for the delete command."""
    
    def test_delete_with_force(self, tmp_path):
        """Test deleting a campaign with force flag."""
        db_path = tmp_path / "test.db"
        db = Database.open(db_path)
        campaign = Campaign.create("Delete Me")
        db.save_campaign(campaign)
        db.close()
        
        with patch("reverie.cli.get_db_path", return_value=db_path):
            result = runner.invoke(app, ["delete", "Delete Me", "--force"])
            assert result.exit_code == 0
            assert "Deleted" in result.output
    
    def test_delete_nonexistent(self, tmp_path):
        """Test deleting nonexistent campaign."""
        db_path = tmp_path / "test.db"
        Database.open(db_path).close()  # Create empty db
        
        with patch("reverie.cli.get_db_path", return_value=db_path):
            result = runner.invoke(app, ["delete", "Nonexistent", "--force"])
            assert result.exit_code == 1
            assert "not found" in result.output.lower()

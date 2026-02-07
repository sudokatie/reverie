"""Command-line interface for Reverie."""

import json
import sys
from pathlib import Path
from typing import Optional

import typer

from .config import load_config, get_config_path, ReverieConfig
from .character import Character, Stats, Equipment, PlayerClass
from .storage.database import Database
from .storage.models import Campaign
from .game import Game, GameState, create_game_state, save_state, load_state
from .ui.app import create_app


app = typer.Typer(
    name="reverie",
    help="AI-powered dungeon master for procedurally generated RPG adventures.",
    no_args_is_help=True,
)


def get_db_path() -> Path:
    """Get the database path from config or default."""
    config = load_config()
    return Path(config.data_dir) / "reverie.db"


def get_database() -> Database:
    """Get a database connection."""
    db_path = get_db_path()
    return Database.open(db_path)


def create_default_character(name: str = "Adventurer") -> Character:
    """Create a default character for new campaigns."""
    return Character(
        name=name,
        race="Human",
        player_class=PlayerClass.WANDERER,
        stats=Stats(might=4, wit=4, spirit=4),
        background="A wanderer seeking adventure.",
        equipment=Equipment(weapon="Walking Staff"),
        gold=50,
    )


@app.command()
def new(
    name: str = typer.Option(None, "--name", "-n", help="Campaign name"),
    character_name: str = typer.Option(None, "--character", "-c", help="Character name"),
) -> None:
    """Start a new campaign."""
    db = get_database()
    
    # Generate campaign name if not provided
    if not name:
        campaign_count = len(db.list_campaigns())
        name = f"Adventure {campaign_count + 1}"
    
    # Create campaign
    campaign = Campaign.create(name)
    db.save_campaign(campaign)
    
    # Create character
    char_name = character_name or "Adventurer"
    character = create_default_character(char_name)
    
    # Create game state
    state = create_game_state(campaign, character)
    
    # Create and save game
    game = Game(state=state, db=db, llm=None)
    save_state(state, db)
    
    typer.echo(f"Created new campaign: {name}")
    typer.echo(f"Character: {character.name} the {character.player_class.value}")
    typer.echo()
    typer.echo("Starting game...")
    
    # Run the TUI
    app_instance = create_app(game)
    app_instance.run()


@app.command("continue")
def continue_game() -> None:
    """Continue the last campaign."""
    db = get_database()
    campaigns = db.list_campaigns()
    
    if not campaigns:
        typer.echo("No saved campaigns found. Use 'reverie new' to start one.")
        raise typer.Exit(code=1)
    
    # Get most recently updated campaign
    latest = campaigns[0]  # Already sorted by updated_at DESC
    
    typer.echo(f"Loading campaign: {latest.name}")
    
    # Load game state
    state = load_state(db, latest.id)
    if not state:
        typer.echo("Error: Could not load campaign state.")
        raise typer.Exit(code=1)
    
    # Create game and run
    game = Game(state=state, db=db, llm=None)
    app_instance = create_app(game)
    app_instance.run()


@app.command()
def load(save: str) -> None:
    """Load a specific save by name or ID."""
    db = get_database()
    campaigns = db.list_campaigns()
    
    # Find campaign by name or ID
    campaign = None
    for c in campaigns:
        if c.name.lower() == save.lower() or c.id == save:
            campaign = c
            break
    
    if not campaign:
        typer.echo(f"Campaign not found: {save}")
        typer.echo("Use 'reverie list' to see available campaigns.")
        raise typer.Exit(code=1)
    
    typer.echo(f"Loading campaign: {campaign.name}")
    
    # Load game state
    state = load_state(db, campaign.id)
    if not state:
        typer.echo("Error: Could not load campaign state.")
        raise typer.Exit(code=1)
    
    # Create game and run
    game = Game(state=state, db=db, llm=None)
    app_instance = create_app(game)
    app_instance.run()


@app.command("list")
def list_saves() -> None:
    """List all saved campaigns."""
    db = get_database()
    campaigns = db.list_campaigns()
    
    if not campaigns:
        typer.echo("No saved campaigns found.")
        return
    
    typer.echo("Saved campaigns:")
    typer.echo()
    
    for c in campaigns:
        playtime_min = c.playtime_seconds // 60
        typer.echo(f"  {c.name}")
        typer.echo(f"    ID: {c.id[:8]}...")
        typer.echo(f"    Last played: {c.updated_at.strftime('%Y-%m-%d %H:%M')}")
        typer.echo(f"    Playtime: {playtime_min} minutes")
        typer.echo()


@app.command("export")
def export_save(
    save: str,
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export a campaign to JSON."""
    db = get_database()
    campaigns = db.list_campaigns()
    
    # Find campaign
    campaign = None
    for c in campaigns:
        if c.name.lower() == save.lower() or c.id == save:
            campaign = c
            break
    
    if not campaign:
        typer.echo(f"Campaign not found: {save}")
        raise typer.Exit(code=1)
    
    # Export data
    data = db.export_campaign(campaign.id)
    
    # Determine output path
    if output:
        out_path = Path(output)
    else:
        safe_name = campaign.name.replace(" ", "_").lower()
        out_path = Path(f"{safe_name}.json")
    
    # Write file
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    
    typer.echo(f"Exported campaign to: {out_path}")


@app.command("import")
def import_save(
    file: Path,
) -> None:
    """Import a campaign from JSON."""
    if not file.exists():
        typer.echo(f"File not found: {file}")
        raise typer.Exit(code=1)
    
    # Read file
    with open(file) as f:
        data = json.load(f)
    
    # Import to database
    db = get_database()
    campaign_id = db.import_campaign(data)
    
    if campaign_id:
        typer.echo(f"Imported campaign: {data.get('campaign', {}).get('name', 'Unknown')}")
        typer.echo(f"Campaign ID: {campaign_id}")
    else:
        typer.echo("Failed to import campaign.")
        raise typer.Exit(code=1)


@app.command()
def config(
    show: bool = typer.Option(True, "--show/--edit", help="Show or edit config"),
) -> None:
    """Show or edit configuration."""
    config_path = get_config_path()
    
    if show:
        typer.echo(f"Config file: {config_path}")
        typer.echo()
        
        cfg = load_config()
        typer.echo("Current configuration:")
        typer.echo()
        typer.echo(f"  LLM Provider: {cfg.llm.provider}")
        typer.echo(f"  LLM Model: {cfg.llm.model}")
        typer.echo(f"  LLM Endpoint: {cfg.llm.endpoint}")
        typer.echo(f"  Audio Enabled: {cfg.audio.enabled}")
        typer.echo(f"  Auto-save: {cfg.gameplay.auto_save}")
        typer.echo(f"  Difficulty: {cfg.gameplay.difficulty}")
    else:
        # Open config in editor
        import subprocess
        editor = "nano"  # Default
        if "EDITOR" in sys.environ:
            editor = sys.environ["EDITOR"]
        
        # Ensure config exists
        if not config_path.exists():
            cfg = ReverieConfig()
            cfg.save(config_path)
        
        subprocess.run([editor, str(config_path)])


@app.command()
def delete(
    save: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a saved campaign."""
    db = get_database()
    campaigns = db.list_campaigns()
    
    # Find campaign
    campaign = None
    for c in campaigns:
        if c.name.lower() == save.lower() or c.id == save:
            campaign = c
            break
    
    if not campaign:
        typer.echo(f"Campaign not found: {save}")
        raise typer.Exit(code=1)
    
    if not force:
        confirm = typer.confirm(f"Delete campaign '{campaign.name}'?")
        if not confirm:
            typer.echo("Cancelled.")
            return
    
    db.delete_campaign(campaign.id)
    typer.echo(f"Deleted campaign: {campaign.name}")


if __name__ == "__main__":
    app()

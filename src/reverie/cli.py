"""Command-line interface for Reverie."""

import typer

app = typer.Typer(
    name="reverie",
    help="AI-powered dungeon master for procedurally generated RPG adventures.",
    no_args_is_help=True,
)


@app.command()
def new(
    name: str = typer.Option(None, "--name", "-n", help="Campaign name"),
) -> None:
    """Start a new campaign."""
    typer.echo("Starting new campaign...")
    # TODO: Implement in Task 14


@app.command()
def continue_game() -> None:
    """Continue the last campaign."""
    typer.echo("Loading last campaign...")
    # TODO: Implement in Task 14


@app.command()
def load(save: str) -> None:
    """Load a specific save."""
    typer.echo(f"Loading save: {save}")
    # TODO: Implement in Task 14


@app.command()
def list_saves() -> None:
    """List all saved campaigns."""
    typer.echo("Saved campaigns:")
    # TODO: Implement in Task 14


@app.command()
def config() -> None:
    """Show or edit configuration."""
    typer.echo("Configuration:")
    # TODO: Implement in Task 14


if __name__ == "__main__":
    app()

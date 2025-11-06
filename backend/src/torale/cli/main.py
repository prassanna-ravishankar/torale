import json
from pathlib import Path

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from torale.cli.auth import auth_app
from torale.cli.tasks import task_app

console = Console()
app = typer.Typer(
    name="torale",
    help="Platform-agnostic background task manager for AI-powered automation",
    add_completion=False,
)

app.add_typer(auth_app, name="auth", help="Authentication commands")
app.add_typer(task_app, name="task", help="Task management commands")


@app.command()
def version():
    """Show version information"""
    from torale import __version__

    print(f"[bold cyan]Torale[/bold cyan] version {__version__}")


@app.command()
def config():
    """Show current configuration"""
    config_file = Path.home() / ".torale" / "config.json"

    if not config_file.exists():
        print(
            "[yellow]No configuration found. Please run 'torale auth set-api-key' first.[/yellow]"
        )
        raise typer.Exit(1)

    with open(config_file) as f:
        config_data = json.load(f)

    table = Table(title="Torale Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    for key, value in config_data.items():
        if key == "api_key":
            # Only show prefix of API key
            value = value[:15] + "..." if len(value) > 15 else value
        table.add_row(key, str(value))

    console.print(table)


if __name__ == "__main__":
    app()

import json
import os
from pathlib import Path

import typer
from rich import print

auth_app = typer.Typer()


def get_config_file() -> Path:
    config_dir = Path.home() / ".torale"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.json"


def save_config(data: dict):
    config_file = get_config_file()
    with open(config_file, "w") as f:
        json.dump(data, f, indent=2)


def load_config() -> dict:
    config_file = get_config_file()
    if not config_file.exists():
        return {}
    with open(config_file) as f:
        return json.load(f)


@auth_app.command("set-api-key")
def set_api_key(
    api_key: str = typer.Option(..., prompt=True, hide_input=True),
    api_url: str = typer.Option("http://localhost:8000", help="API URL"),
):
    """Set your API key for CLI authentication

    Generate an API key from the web dashboard at https://torale.ai
    then use this command to save it locally.
    """
    if not api_key.startswith("sk_"):
        print("[red]✗ Invalid API key format. API keys should start with 'sk_'[/red]")
        raise typer.Exit(1)

    config_data = {
        "api_key": api_key,
        "api_url": api_url,
    }
    save_config(config_data)
    print("[green]✓ API key saved successfully![/green]")
    print(f"[cyan]API URL: {api_url}[/cyan]")


@auth_app.command()
def logout():
    """Clear stored credentials"""
    config_file = get_config_file()
    if config_file.exists():
        config_file.unlink()
        print("[green]✓ Credentials cleared![/green]")
    else:
        print("[yellow]No credentials stored.[/yellow]")


@auth_app.command()
def status():
    """Check authentication status"""
    # Check for noauth mode
    if os.getenv("TORALE_NOAUTH") == "1":
        print("[yellow]⚠ Running in NOAUTH mode (TORALE_NOAUTH=1)[/yellow]")
        print("[yellow]Authentication is disabled for local development.[/yellow]")
        return

    config = load_config()
    if config.get("api_key"):
        print("[green]✓ Authenticated with API key[/green]")
        key_prefix = config["api_key"][:10] + "..."
        print(f"[cyan]API Key: {key_prefix}[/cyan]")
        print(f"[cyan]API URL: {config.get('api_url')}[/cyan]")
    else:
        print("[yellow]Not authenticated.[/yellow]")
        print("[cyan]To authenticate:[/cyan]")
        print("  1. Generate an API key at https://torale.ai")
        print("  2. Run: torale auth set-api-key")
        print()
        print("[cyan]For local development without auth:[/cyan]")
        print("  export TORALE_NOAUTH=1")

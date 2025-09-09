import json
from pathlib import Path

import httpx
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


@auth_app.command()
def login(
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
    api_url: str = typer.Option("http://localhost:8000", help="API URL"),
):
    """Login to Torale"""
    print(f"[cyan]Logging in to {api_url}...[/cyan]")
    
    # For now, we'll use Supabase auth directly
    # In production, this would go through our API
    from torale.core.config import settings
    from supabase import create_client
    
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        
        if response.session:
            config_data = {
                "email": email,
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "api_url": api_url,
            }
            save_config(config_data)
            print("[green]✓ Successfully logged in![/green]")
        else:
            print("[red]✗ Login failed. Please check your credentials.[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        print(f"[red]✗ Login failed: {str(e)}[/red]")
        raise typer.Exit(1)


@auth_app.command()
def logout():
    """Logout from Torale"""
    config_file = get_config_file()
    if config_file.exists():
        config_file.unlink()
        print("[green]✓ Successfully logged out![/green]")
    else:
        print("[yellow]Not logged in.[/yellow]")


@auth_app.command()
def status():
    """Check authentication status"""
    config = load_config()
    if config:
        print(f"[green]✓ Logged in as: {config.get('email')}[/green]")
        print(f"[cyan]API URL: {config.get('api_url')}[/cyan]")
    else:
        print("[yellow]Not logged in. Run 'torale auth login' to authenticate.[/yellow]")
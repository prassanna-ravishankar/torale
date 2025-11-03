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
def register(
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True),
    api_url: str = typer.Option("http://localhost:8000", help="API URL"),
):
    """Register a new account"""
    print(f"[cyan]Registering account at {api_url}...[/cyan]")

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{api_url}/auth/register",
                json={
                    "email": email,
                    "password": password,
                },
            )

            if response.status_code == 201:
                print("[green]✓ Account created successfully![/green]")
                print("[cyan]You can now login with: torale auth login[/cyan]")
            else:
                error_detail = response.json().get("detail", "Registration failed")
                print(f"[red]✗ Registration failed: {error_detail}[/red]")
                raise typer.Exit(1)

    except httpx.RequestError as e:
        print(f"[red]✗ Connection error: {str(e)}[/red]")
        print("[yellow]Make sure the API server is running.[/yellow]")
        raise typer.Exit(1)


@auth_app.command()
def login(
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
    api_url: str = typer.Option("http://localhost:8000", help="API URL"),
):
    """Login to Torale"""
    print(f"[cyan]Logging in to {api_url}...[/cyan]")

    try:
        with httpx.Client() as client:
            # FastAPI-Users login endpoint expects form data
            response = client.post(
                f"{api_url}/auth/jwt/login",
                data={
                    "username": email,  # FastAPI-Users uses 'username' field
                    "password": password,
                },
            )

            if response.status_code == 200:
                auth_data = response.json()
                config_data = {
                    "email": email,
                    "access_token": auth_data["access_token"],
                    "token_type": auth_data["token_type"],
                    "api_url": api_url,
                }
                save_config(config_data)
                print("[green]✓ Successfully logged in![/green]")
            else:
                error_detail = response.json().get("detail", "Login failed")
                print(f"[red]✗ Login failed: {error_detail}[/red]")
                raise typer.Exit(1)

    except httpx.RequestError as e:
        print(f"[red]✗ Connection error: {str(e)}[/red]")
        print("[yellow]Make sure the API server is running.[/yellow]")
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

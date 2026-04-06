"""CLI commands for podcast publishing."""

from pathlib import Path

import httpx
import typer
from rich.console import Console

publish_app = typer.Typer(
    name="publish",
    help="Podcast distribution and publishing commands.",
    no_args_is_help=True,
)

console = Console()


@publish_app.command("episode")
def publish_episode(
    episode_id: str = typer.Argument(help="Episode ID to publish"),
    show_id: str = typer.Option(..., "--show", "-s", help="Show ID"),
    audio_path: Path = typer.Option(..., "--audio", "-a", help="Path to audio file"),
    title: str = typer.Option("", "--title", "-t", help="Episode title"),
    description: str = typer.Option("", "--desc", "-d", help="Episode description"),
) -> None:
    """Publish an episode: upload to R2 and add to RSS feed."""
    if not audio_path.exists():
        console.print(f"[red]Audio file not found: {audio_path}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Publishing episode {episode_id}...[/bold]")
    response = httpx.post(
        "http://localhost:8200/publish",
        json={
            "show_id": show_id,
            "episode_id": episode_id,
            "audio_path": str(audio_path),
            "title": title or episode_id,
            "description": description,
        },
        timeout=120.0,
    )
    if response.status_code == 200:
        result = response.json()
        console.print("[green]Published![/green]")
        console.print(f"  Audio URL: {result.get('audio_url', 'N/A')}")
        console.print(f"  State: {result.get('state', 'N/A')}")
    else:
        console.print(f"[red]Failed: {response.text}[/red]")
        raise typer.Exit(1)


@publish_app.command("unpublish")
def unpublish_episode(
    episode_id: str = typer.Argument(help="Episode ID to unpublish"),
    show_id: str = typer.Option(..., "--show", "-s", help="Show ID"),
) -> None:
    """Remove an episode from the RSS feed."""
    response = httpx.post(
        f"http://localhost:8200/unpublish/{show_id}/{episode_id}",
        timeout=30.0,
    )
    if response.status_code == 200:
        console.print(f"[green]Unpublished {episode_id}[/green]")
    else:
        console.print(f"[red]Failed: {response.text}[/red]")


@publish_app.command("feed")
def show_feed(
    show_id: str = typer.Argument(help="Show ID"),
    validate: bool = typer.Option(False, "--validate", help="Validate the feed"),
) -> None:
    """Display or validate RSS feed for a show."""
    if validate:
        response = httpx.post(
            f"http://localhost:8200/feeds/{show_id}/validate",
            timeout=30.0,
        )
        result = response.json()
        if result.get("valid"):
            console.print("[green]Feed is valid[/green]")
        else:
            console.print("[red]Feed has errors:[/red]")
            for err in result.get("errors", []):
                console.print(f"  - {err}")
    else:
        response = httpx.get(
            f"http://localhost:8200/feeds/{show_id}.xml",
            timeout=30.0,
        )
        if response.status_code == 200:
            console.print(response.text)
        else:
            console.print(f"[red]Feed not found for {show_id}[/red]")


@publish_app.command("status")
def publication_status(
    show_id: str = typer.Argument(help="Show ID"),
) -> None:
    """Show publication status for all episodes."""
    console.print(f"[bold]Publication status for {show_id}[/bold]")
    console.print("[dim]Connect to distribution service for live status[/dim]")

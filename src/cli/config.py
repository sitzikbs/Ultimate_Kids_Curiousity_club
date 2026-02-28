"""Configuration inspection commands for the Kids Podcast Generator CLI.

Read-only view of runtime settings — mutation requires editing .env or
exporting environment variables.
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import get_settings

config_app = typer.Typer(help="Inspect and validate configuration")
console = Console()


@config_app.command("show")
def show_config():
    """Display current configuration settings."""
    settings = get_settings()

    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Group: mode
    mock_style = "green" if settings.USE_MOCK_SERVICES else "yellow"
    table.add_row(
        "USE_MOCK_SERVICES",
        f"[{mock_style}]{settings.USE_MOCK_SERVICES}[/{mock_style}]",
    )

    # Group: providers
    table.add_row("LLM_PROVIDER", settings.LLM_PROVIDER)
    table.add_row("TTS_PROVIDER", settings.TTS_PROVIDER)
    table.add_row("IMAGE_PROVIDER", settings.IMAGE_PROVIDER)

    # Group: API keys (masked)
    for key_name in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "ELEVENLABS_API_KEY",
    ):
        value = getattr(settings, key_name, None)
        if value:
            masked = value[:4] + "…" + value[-4:]
            table.add_row(key_name, f"[green]{masked}[/green]")
        else:
            table.add_row(key_name, "[dim]not set[/dim]")

    # Group: paths
    table.add_row("DATA_DIR", str(settings.DATA_DIR))
    table.add_row("SHOWS_DIR", str(settings.SHOWS_DIR))
    table.add_row("EPISODES_DIR", str(settings.EPISODES_DIR))
    table.add_row("ASSETS_DIR", str(settings.ASSETS_DIR))
    table.add_row("AUDIO_OUTPUT_DIR", str(settings.AUDIO_OUTPUT_DIR))

    console.print(table)


@config_app.command("validate")
def validate_config():
    """Validate that all required settings are present for the active mode."""
    try:
        settings = get_settings()
    except Exception as e:
        console.print(f"[red]✗ Configuration error: {e}[/red]")
        raise typer.Exit(1)

    issues: list[str] = []

    if not settings.USE_MOCK_SERVICES:
        # Check provider-specific key
        provider = settings.LLM_PROVIDER
        key_map = {
            "openai": settings.OPENAI_API_KEY,
            "anthropic": settings.ANTHROPIC_API_KEY,
            "gemini": settings.GEMINI_API_KEY,
        }
        if provider in key_map and not key_map[provider]:
            issues.append(
                f"LLM_PROVIDER={provider} requires "
                f"{provider.upper()}_API_KEY to be set"
            )

        tts = settings.TTS_PROVIDER
        if tts == "elevenlabs" and not settings.ELEVENLABS_API_KEY:
            issues.append("TTS_PROVIDER=elevenlabs requires ELEVENLABS_API_KEY")

    # Check paths exist
    for field in ("DATA_DIR", "SHOWS_DIR"):
        path = getattr(settings, field)
        if not path.exists():
            issues.append(f"{field} ({path}) does not exist")

    if issues:
        console.print("[red]✗ Configuration issues found:[/red]")
        for issue in issues:
            console.print(f"  • {issue}")
        raise typer.Exit(1)
    else:
        mode = "mock" if settings.USE_MOCK_SERVICES else "live"
        console.print(
            f"[green]✓ Configuration valid[/green] (mode: {mode})"
        )


@config_app.command("providers")
def list_providers():
    """List available provider options."""
    console.print(
        Panel(
            "[bold]LLM Providers:[/bold]\n"
            "  • [cyan]mock[/cyan]      — Fixture-based (no API key)\n"
            "  • [cyan]openai[/cyan]    — OpenAI GPT models\n"
            "  • [cyan]anthropic[/cyan] — Anthropic Claude models\n"
            "  • [cyan]gemini[/cyan]    — Google Gemini models\n\n"
            "[bold]TTS Providers:[/bold]\n"
            "  • [cyan]mock[/cyan]        — Silent WAV files (no API key)\n"
            "  • [cyan]elevenlabs[/cyan]  — ElevenLabs voices\n"
            "  • [cyan]google[/cyan]      — Google Cloud TTS\n"
            "  • [cyan]openai[/cyan]      — OpenAI TTS\n\n"
            "[bold]Image Providers:[/bold]\n"
            "  • [cyan]mock[/cyan]  — Placeholder images\n"
            "  • [cyan]flux[/cyan]  — Flux image generation\n"
            "  • [cyan]dalle[/cyan] — DALL·E image generation",
            title="Available Providers",
            border_style="blue",
        )
    )

    settings = get_settings()
    console.print(
        f"\n[dim]Active:[/dim] LLM={settings.LLM_PROVIDER} "
        f"TTS={settings.TTS_PROVIDER} IMAGE={settings.IMAGE_PROVIDER}"
    )
    console.print(
        "\n[dim]Change via .env or environment variables. "
        "Set USE_MOCK_SERVICES=false for live mode.[/dim]"
    )

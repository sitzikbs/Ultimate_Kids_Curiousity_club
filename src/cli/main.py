"""Main CLI application for Kids Podcast Generator."""

from pathlib import Path

import typer
from rich.console import Console

from cli.shows import shows_app

app = typer.Typer(
    name="kids-podcast",
    help="AI-powered kids podcast generator",
    no_args_is_help=True,
)

# Global console for rich output
console = Console()

# Global options
config_file_option = typer.Option(
    None,
    "--config-file",
    "-c",
    help="Path to configuration file",
    envvar="KIDS_PODCAST_CONFIG",
)

verbose_option = typer.Option(
    False,
    "--verbose",
    "-v",
    help="Enable verbose output",
)


# Add command groups
app.add_typer(shows_app, name="shows")


@app.command()
def version():
    """Show version information."""
    console.print("[bold blue]Kids Podcast Generator v0.1.0[/bold blue]")
    console.print("AI-powered educational podcast platform for kids")


@app.callback()
def main_callback(
    ctx: typer.Context,
    config_file: Path | None = config_file_option,
    verbose: bool = verbose_option,
):
    """Kids Podcast Generator - Create educational podcasts for curious kids.

    Use --help with any command to see detailed usage information.
    """
    # Store global options in context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config_file"] = config_file

    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")
        if config_file:
            console.print(f"[dim]Config file: {config_file}[/dim]")


if __name__ == "__main__":
    app()

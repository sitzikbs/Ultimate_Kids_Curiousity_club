"""Show management commands for the Kids Podcast Generator CLI."""

import os
import subprocess
from datetime import UTC, datetime

import typer
from rich.console import Console
from rich.table import Table

from models.show import (
    Character,
    ConceptsHistory,
    Protagonist,
    Show,
    ShowBlueprint,
    WorldDescription,
)
from modules.show_blueprint_manager import ShowBlueprintManager

shows_app = typer.Typer(help="Manage shows and Show Blueprints")
console = Console()


@shows_app.command("list")
def list_shows():
    """List all available shows."""
    try:
        blueprint_manager = ShowBlueprintManager()
        shows = blueprint_manager.list_shows()

        if not shows:
            console.print("[yellow]No shows found[/yellow]")
            console.print("\n[dim]Create a new show with:[/dim]")
            console.print("  [cyan]kids-podcast shows create <show-id>[/cyan]")
            console.print(
                "  [cyan]kids-podcast shows init <show-id> --template oliver[/cyan]"
            )
            return

        table = Table(title="Shows")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="white")
        table.add_column("Theme", style="dim")
        table.add_column("Episodes", justify="right")

        for show in shows:
            # Count episodes
            show_dir = blueprint_manager.shows_dir / show.show_id / "episodes"
            episode_count = 0
            if show_dir.exists():
                episode_count = len([d for d in show_dir.iterdir() if d.is_dir()])

            theme_display = (
                show.theme[:50] + "..." if len(show.theme) > 50 else show.theme
            )
            table.add_row(show.show_id, show.title, theme_display, str(episode_count))

        console.print(table)

    except FileNotFoundError:
        console.print("[red]Error: Shows directory not found[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error listing shows: {e}[/red]")
        raise typer.Exit(1)


@shows_app.command("create")
def create_show(
    show_id: str = typer.Argument(..., help="Unique show identifier (kebab-case)"),
    title: str = typer.Option(None, "--title", "-t", help="Show title"),
    theme: str = typer.Option(None, "--theme", help="Show theme/description"),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Interactive mode"
    ),
):
    """Create a new show with protagonist.

    Examples:
      kids-podcast shows create my-show
      kids-podcast shows create my-show --title "My Show" \\
        --theme "Educational" --no-interactive
    """
    blueprint_manager = ShowBlueprintManager()

    # Check if show already exists
    show_dir = blueprint_manager.shows_dir / show_id
    if show_dir.exists():
        console.print(f"[red]Error: Show '{show_id}' already exists[/red]")
        raise typer.Exit(1)

    # Get title and theme
    if title is None:
        if interactive:
            title = typer.prompt("Show title")
        else:
            console.print(
                "[red]Error: --title is required in non-interactive mode[/red]"
            )
            raise typer.Exit(1)

    if theme is None:
        if interactive:
            theme = typer.prompt("Show theme/description")
        else:
            console.print(
                "[red]Error: --theme is required in non-interactive mode[/red]"
            )
            raise typer.Exit(1)

    # Interactive protagonist setup
    if interactive:
        console.print("\n[bold]Protagonist Setup[/bold]")
        protagonist_name = typer.prompt("  Name")
        protagonist_age = typer.prompt("  Age", type=int)
        protagonist_description = typer.prompt("  Description")
        protagonist_values = typer.prompt(
            "  Core values (comma-separated)", default="curiosity,creativity"
        )
        protagonist_catchphrase = typer.prompt("  Catchphrase (optional)", default="")
        protagonist_backstory = typer.prompt("  Backstory (optional)", default="")

        values_list = [v.strip() for v in protagonist_values.split(",")]
        catchphrases_list = [protagonist_catchphrase] if protagonist_catchphrase else []
    else:
        # Minimal protagonist for non-interactive mode
        protagonist_name = "Protagonist"
        protagonist_age = 10
        protagonist_description = "Curious and enthusiastic character"
        values_list = ["curiosity", "creativity"]
        catchphrases_list = []
        protagonist_backstory = ""

    # Create show blueprint
    show = Show(
        show_id=show_id,
        title=title,
        description=theme,
        theme=theme,
        narrator_voice_config={"provider": "mock", "voice_id": "mock_narrator"},
    )

    protagonist = Protagonist(
        name=protagonist_name,
        age=protagonist_age,
        description=protagonist_description,
        values=values_list,
        catchphrases=catchphrases_list,
        backstory=protagonist_backstory,
        voice_config={
            "provider": "mock",
            "voice_id": f"mock_{protagonist_name.lower().replace(' ', '_')}",
        },
    )

    world = WorldDescription(
        setting="Default world setting",
        rules=["Rule 1: Be curious", "Rule 2: Learn together"],
        atmosphere="Friendly and educational",
        locations=[],
    )

    blueprint = ShowBlueprint(
        show=show,
        protagonist=protagonist,
        world=world,
        characters=[],
        concepts_history=ConceptsHistory(concepts=[], last_updated=datetime.now(UTC)),
        episodes=[],
    )

    try:
        blueprint_manager.save_show(blueprint)

        console.print(f"\n[green]✓[/green] Show created: [bold]{show.show_id}[/bold]")
        console.print(f"  Title: {show.title}")
        console.print(f"  Protagonist: {protagonist.name}")
        console.print(f"  Directory: {show_dir}")
        console.print("\n[dim]View show details with:[/dim]")
        console.print(f"  [cyan]kids-podcast shows info {show_id}[/cyan]")
    except Exception as e:
        console.print(f"\n[red]✗ Error creating show: {e}[/red]")
        raise typer.Exit(1)


@shows_app.command("init")
def init_show(
    show_id: str = typer.Argument(..., help="Unique show identifier"),
    template: str = typer.Option(
        ..., "--template", "-t", help="Template name (oliver or hannah)"
    ),
):
    """Initialize a new show from a template.

    Examples:
      kids-podcast shows init my-oliver --template oliver
      kids-podcast shows init my-hannah --template hannah
    """
    blueprint_manager = ShowBlueprintManager()

    # Check if show already exists
    show_dir = blueprint_manager.shows_dir / show_id
    if show_dir.exists():
        console.print(f"[red]Error: Show '{show_id}' already exists[/red]")
        raise typer.Exit(1)

    # Map template names to internal names
    template_map = {
        "oliver": "oliver_template",
        "hannah": "hannah_template",
    }

    if template not in template_map:
        console.print(f"[red]Error: Unknown template '{template}'[/red]")
        console.print("[yellow]Available templates: oliver, hannah[/yellow]")
        raise typer.Exit(1)

    try:
        blueprint = ShowBlueprintManager.create_from_template(
            template_map[template], show_id
        )
        blueprint_manager.save_show(blueprint)

        console.print(
            f"\n[green]✓[/green] Show initialized from template: "
            f"[bold]{template}[/bold]"
        )
        console.print(f"  Show ID: {show_id}")
        console.print(f"  Title: {blueprint.show.title}")
        console.print(f"  Protagonist: {blueprint.protagonist.name}")
        console.print(f"  Directory: {show_dir}")
        console.print("\n[dim]View show details with:[/dim]")
        console.print(f"  [cyan]kids-podcast shows info {show_id}[/cyan]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error initializing show: {e}[/red]")
        raise typer.Exit(1)


@shows_app.command("info")
def show_info(show_id: str = typer.Argument(..., help="Show identifier")):
    """Display complete Show Blueprint information.

    Examples:
      kids-podcast shows info my-show
    """
    blueprint_manager = ShowBlueprintManager()

    try:
        blueprint = blueprint_manager.load_show(show_id)
    except FileNotFoundError:
        console.print(f"[red]Error: Show '{show_id}' not found[/red]")
        console.print("\n[dim]List available shows with:[/dim]")
        console.print("  [cyan]kids-podcast shows list[/cyan]")
        raise typer.Exit(1)

    # Show metadata
    console.print(f"\n[bold cyan]{blueprint.show.title}[/bold cyan]")
    console.print(f"[dim]ID: {blueprint.show.show_id}[/dim]\n")
    console.print(f"[bold]Theme:[/bold] {blueprint.show.theme}")
    console.print(f"[bold]Description:[/bold] {blueprint.show.description}")

    # Protagonist
    console.print("\n[bold]Protagonist:[/bold]")
    console.print(f"  Name: {blueprint.protagonist.name}")
    console.print(f"  Age: {blueprint.protagonist.age}")
    console.print(f"  Description: {blueprint.protagonist.description}")
    if blueprint.protagonist.values:
        console.print(f"  Values: {', '.join(blueprint.protagonist.values)}")
    if blueprint.protagonist.catchphrases:
        for phrase in blueprint.protagonist.catchphrases:
            console.print(f'  Catchphrase: "{phrase}"')
    if blueprint.protagonist.backstory:
        console.print(f"  Backstory: {blueprint.protagonist.backstory}")

    # World
    console.print("\n[bold]World:[/bold]")
    console.print(f"  Setting: {blueprint.world.setting}")
    console.print(f"  Atmosphere: {blueprint.world.atmosphere}")
    if blueprint.world.rules:
        console.print("  Rules:")
        for rule in blueprint.world.rules:
            console.print(f"    • {rule}")
    if blueprint.world.locations:
        console.print(f"  Locations: {len(blueprint.world.locations)}")

    # Supporting characters
    if blueprint.characters:
        console.print(
            f"\n[bold]Supporting Characters:[/bold] {len(blueprint.characters)}"
        )
        for char in blueprint.characters[:5]:  # Show first 5
            console.print(f"  • {char.name} ({char.role})")
        if len(blueprint.characters) > 5:
            console.print(f"  ... and {len(blueprint.characters) - 5} more")

    # Concepts
    concepts = blueprint_manager.get_covered_concepts(show_id)
    if concepts:
        console.print(f"\n[bold]Concepts Covered:[/bold] {len(concepts)}")
        for concept in concepts[:10]:  # Show first 10
            console.print(f"  • {concept}")
        if len(concepts) > 10:
            console.print(f"  ... and {len(concepts) - 10} more")

    # Episodes
    episode_count = len(blueprint.episodes)
    console.print(f"\n[bold]Episodes:[/bold] {episode_count}")


@shows_app.command("edit-protagonist")
def edit_protagonist(show_id: str = typer.Argument(..., help="Show identifier")):
    """Edit protagonist interactively.

    Examples:
      kids-podcast shows edit-protagonist my-show
    """
    blueprint_manager = ShowBlueprintManager()

    try:
        blueprint = blueprint_manager.load_show(show_id)
    except FileNotFoundError:
        console.print(f"[red]Error: Show '{show_id}' not found[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Edit Protagonist for {blueprint.show.title}[/bold]\n")
    console.print("[dim]Press Enter to keep current value[/dim]\n")

    # Edit protagonist fields
    name = typer.prompt("Name", default=blueprint.protagonist.name)
    age = typer.prompt("Age", default=str(blueprint.protagonist.age), type=int)
    description = typer.prompt("Description", default=blueprint.protagonist.description)

    values_str = ", ".join(blueprint.protagonist.values)
    new_values = typer.prompt("Core values (comma-separated)", default=values_str)
    values_list = [v.strip() for v in new_values.split(",")]

    catchphrases_str = ", ".join(blueprint.protagonist.catchphrases)
    new_catchphrases = typer.prompt(
        "Catchphrases (comma-separated)", default=catchphrases_str
    )
    catchphrases_list = [c.strip() for c in new_catchphrases.split(",") if c.strip()]

    backstory = typer.prompt("Backstory", default=blueprint.protagonist.backstory or "")

    # Update protagonist
    updated_protagonist = Protagonist(
        name=name,
        age=age,
        description=description,
        values=values_list,
        catchphrases=catchphrases_list,
        backstory=backstory,
        image_path=blueprint.protagonist.image_path,
        voice_config=blueprint.protagonist.voice_config,
    )

    try:
        blueprint_manager.update_protagonist(show_id, updated_protagonist)
        console.print("\n[green]✓[/green] Protagonist updated successfully")
    except Exception as e:
        console.print(f"\n[red]✗ Error updating protagonist: {e}[/red]")
        raise typer.Exit(1)


@shows_app.command("edit-world")
def edit_world(show_id: str = typer.Argument(..., help="Show identifier")):
    """Open world.yaml in $EDITOR for editing.

    Examples:
      kids-podcast shows edit-world my-show
    """
    blueprint_manager = ShowBlueprintManager()

    # Check if show exists
    show_dir = blueprint_manager.shows_dir / show_id
    if not show_dir.exists():
        console.print(f"[red]Error: Show '{show_id}' not found[/red]")
        raise typer.Exit(1)

    world_file = show_dir / "world.yaml"
    if not world_file.exists():
        console.print(f"[red]Error: world.yaml not found for show '{show_id}'[/red]")
        raise typer.Exit(1)

    # Get editor from environment
    editor = os.environ.get("EDITOR", "nano")

    console.print(f"[dim]Opening {world_file} in {editor}...[/dim]")

    try:
        # Open editor
        result = subprocess.run([editor, str(world_file)])
        if result.returncode == 0:
            console.print("[green]✓[/green] World file edited successfully")
        else:
            console.print(
                f"[yellow]Editor exited with code {result.returncode}[/yellow]"
            )
    except FileNotFoundError:
        console.print(f"[red]Error: Editor '{editor}' not found[/red]")
        console.print(
            "[yellow]Set EDITOR environment variable to your preferred editor[/yellow]"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error opening editor: {e}[/red]")
        raise typer.Exit(1)


@shows_app.command("characters")
def list_characters(show_id: str = typer.Argument(..., help="Show identifier")):
    """List supporting characters for a show.

    Examples:
      kids-podcast shows characters my-show
    """
    blueprint_manager = ShowBlueprintManager()

    try:
        blueprint = blueprint_manager.load_show(show_id)
    except FileNotFoundError:
        console.print(f"[red]Error: Show '{show_id}' not found[/red]")
        raise typer.Exit(1)

    if not blueprint.characters:
        console.print("[yellow]No supporting characters found[/yellow]")
        console.print("\n[dim]Add a character with:[/dim]")
        console.print(f"  [cyan]kids-podcast shows add-character {show_id}[/cyan]")
        return

    table = Table(title=f"Characters - {blueprint.show.title}")
    table.add_column("Name", style="cyan")
    table.add_column("Role", style="white")
    table.add_column("Description", style="dim")

    for char in blueprint.characters:
        desc = (
            char.description[:60] + "..."
            if len(char.description) > 60
            else char.description
        )
        table.add_row(char.name, char.role, desc)

    console.print(table)


@shows_app.command("add-character")
def add_character(
    show_id: str = typer.Argument(..., help="Show identifier"),
    name: str = typer.Option(None, "--name", "-n", help="Character name"),
    role: str = typer.Option(None, "--role", "-r", help="Character role"),
    description: str = typer.Option(
        None, "--description", "-d", help="Character description"
    ),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Interactive mode"
    ),
):
    """Add a supporting character to a show.

    Examples:
      kids-podcast shows add-character my-show
      kids-podcast shows add-character my-show --name "Bob" \\
        --role "Friend" --description "Helpful friend" --no-interactive
    """
    blueprint_manager = ShowBlueprintManager()

    try:
        blueprint = blueprint_manager.load_show(show_id)
    except FileNotFoundError:
        console.print(f"[red]Error: Show '{show_id}' not found[/red]")
        raise typer.Exit(1)

    # Get character details
    if interactive:
        console.print(f"\n[bold]Add Character to {blueprint.show.title}[/bold]\n")
        name = name or typer.prompt("Character name")
        role = role or typer.prompt("Character role")
        description = description or typer.prompt("Character description")
        personality = typer.prompt("Personality traits", default="Friendly and helpful")
    else:
        if not name or not role or not description:
            console.print(
                "[red]Error: --name, --role, and --description are required "
                "in non-interactive mode[/red]"
            )
            raise typer.Exit(1)
        personality = "Friendly and helpful"

    # Create character
    character = Character(
        name=name,
        role=role,
        description=description,
        personality=personality,
        voice_config={
            "provider": "mock",
            "voice_id": f"mock_{name.lower().replace(' ', '_')}",
        },
    )

    try:
        blueprint_manager.add_character(show_id, character)

        console.print(
            f"\n[green]✓[/green] Character added: [bold]{character.name}[/bold]"
        )
        console.print(f"  Role: {character.role}")
        console.print(f"  Description: {character.description}")
    except Exception as e:
        console.print(f"\n[red]✗ Error adding character: {e}[/red]")
        raise typer.Exit(1)


@shows_app.command("concepts")
def list_concepts(show_id: str = typer.Argument(..., help="Show identifier")):
    """List concepts covered in a show.

    Examples:
      kids-podcast shows concepts my-show
    """
    blueprint_manager = ShowBlueprintManager()

    try:
        blueprint = blueprint_manager.load_show(show_id)
    except FileNotFoundError:
        console.print(f"[red]Error: Show '{show_id}' not found[/red]")
        raise typer.Exit(1)

    concepts = blueprint_manager.get_covered_concepts(show_id)

    if not concepts:
        console.print("[yellow]No concepts covered yet[/yellow]")
        return

    console.print(f"\n[bold]Concepts Covered - {blueprint.show.title}[/bold]\n")
    for i, concept in enumerate(concepts, 1):
        console.print(f"  {i}. {concept}")

    console.print(f"\n[dim]Total: {len(concepts)} concept(s)[/dim]")


@shows_app.command("suggest-topics")
def suggest_topics(show_id: str = typer.Argument(..., help="Show identifier")):
    """Suggest topics based on uncovered concepts (placeholder).

    Examples:
      kids-podcast shows suggest-topics my-show
    """
    blueprint_manager = ShowBlueprintManager()

    try:
        blueprint = blueprint_manager.load_show(show_id)
    except FileNotFoundError:
        console.print(f"[red]Error: Show '{show_id}' not found[/red]")
        raise typer.Exit(1)

    concepts = blueprint_manager.get_covered_concepts(show_id)

    console.print(f"\n[bold]Topic Suggestions for {blueprint.show.title}[/bold]\n")

    if (
        blueprint.show.theme.lower().find("stem") >= 0
        or blueprint.show.show_id.find("oliver") >= 0
    ):
        # STEM suggestions
        suggestions = [
            "How do magnets work?",
            "What makes airplanes fly?",
            "Why do things sink or float?",
            "How do computers think?",
            "What is electricity?",
        ]
    elif (
        blueprint.show.theme.lower().find("history") >= 0
        or blueprint.show.show_id.find("hannah") >= 0
    ):
        # History suggestions
        suggestions = [
            "Ancient civilizations",
            "Famous inventors through history",
            "How did people live 100 years ago?",
            "The story of writing and books",
            "Great explorers and their journeys",
        ]
    else:
        # General suggestions
        suggestions = [
            "The water cycle",
            "Why do seasons change?",
            "How do plants grow?",
            "What are ecosystems?",
            "The solar system",
        ]

    console.print("[dim]Suggested topics (based on show theme):[/dim]\n")
    for i, suggestion in enumerate(suggestions, 1):
        console.print(f"  {i}. {suggestion}")

    console.print(f"\n[dim]Already covered: {len(concepts)} concept(s)[/dim]")
    console.print("\n[yellow]Note: This is a placeholder implementation.[/yellow]")
    console.print("[yellow]Full topic suggestion requires LLM integration.[/yellow]")

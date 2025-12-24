# WP7a: Show Commands

**Status**: ⏳ Not Started  
**Parent WP**: [WP7: CLI Interface](WP7_CLI.md)  
**Dependencies**: WP1 (Foundation), WP1c (Blueprint Manager)  
**Estimated Effort**: 1-2 days  
**Owner**: TBD  
**Subsystem:** User Interface

## 📋 Overview

Show Commands provide CLI interface for **show management**, **Show Blueprint viewing**, and **character management**. Built with Typer for intuitive commands and rich for beautiful terminal output. Enables creating shows, initializing from templates, editing protagonists/worlds, and managing characters/concepts.

**Key Deliverables**:
- Show management commands (list, create, init, info)
- Show Blueprint commands (characters, concepts, suggest-topics)
- Character management within shows (add, list)
- Interactive prompts for show creation
- Formatted terminal output with rich

**System Context**:
- **Subsystem:** User Interface
- **Depends on:** WP1 (Foundation), WP1c (Blueprint Manager)
- **Used by:** End users, developers
- **Related WPs:** WP7b (Episode Commands)

## 🎯 High-Level Tasks

### Task 7.1: CLI Framework Setup
Establish Typer-based CLI structure.

**Subtasks**:
- [ ] 7.1.1: Create main CLI app with Typer
- [ ] 7.1.2: Define command groups (shows, episodes, config)
- [ ] 7.1.3: Add global options (--verbose, --config-file)
- [ ] 7.1.4: Implement version command
- [ ] 7.1.5: Add help text for all commands

**Expected Outputs**:
- `src/cli/main.py`
- CLI entry point

### Task 7.2: Show Management Commands
Manage shows and Show Blueprints.

**Subtasks**:
- [ ] 7.2.1: Implement `shows list` command (list all shows with metadata)
- [ ] 7.2.2: Implement `shows create <show-id>` command (interactive: title, theme, protagonist)
- [ ] 7.2.3: Implement `shows init <show-id> --template <oliver|hannah>` command (initialize from template)
- [ ] 7.2.4: Implement `shows info <show-id>` command (display complete Show Blueprint)
- [ ] 7.2.5: Implement `shows edit-protagonist <show-id>` command (interactive editor)
- [ ] 7.2.6: Implement `shows edit-world <show-id>` command (open world.md in $EDITOR)
- [ ] 7.2.7: Display show info in formatted tables with rich

**Expected Outputs**:
- `src/cli/shows.py`
- Show management commands

### Task 7.3: Show Blueprint Commands
Manage characters and concepts within shows.

**Subtasks**:
- [ ] 7.3.1: Implement `shows characters <show-id>` command (list supporting characters)
- [ ] 7.3.2: Implement `shows add-character <show-id>` command (interactive: name, role, description)
- [ ] 7.3.3: Implement `shows concepts <show-id>` command (list covered concepts)
- [ ] 7.3.4: Implement `shows suggest-topics <show-id>` command (suggest topics based on uncovered concepts)
- [ ] 7.3.5: Display character/concept lists in formatted tables

**Expected Outputs**:
- `src/cli/show_blueprint.py`
- Show Blueprint management commands

## 🔧 Technical Specifications

### CLI Structure
```python
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="kids-podcast",
    help="AI-powered kids podcast generator"
)

# Command groups
shows_app = typer.Typer(help="Manage shows")
episodes_app = typer.Typer(help="Manage episodes")
config_app = typer.Typer(help="Manage configuration")

app.add_typer(shows_app, name="shows")
app.add_typer(episodes_app, name="episodes")
app.add_typer(config_app, name="config")

console = Console()

@app.command()
def version():
    """Show version information."""
    console.print("[bold blue]Kids Podcast Generator v0.1.0[/bold blue]")

if __name__ == "__main__":
    app()
```

### Show List Command
```python
@shows_app.command("list")
def list_shows():
    """List all available shows."""
    
    blueprint_manager = BlueprintManager()
    shows = blueprint_manager.list_shows()
    
    if not shows:
        console.print("[yellow]No shows found[/yellow]")
        return
    
    table = Table(title="Shows")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Theme", style="dim")
    table.add_column("Episodes", justify="right")
    
    for show in shows:
        table.add_row(
            show.id,
            show.title,
            show.theme[:50] + "..." if len(show.theme) > 50 else show.theme,
            str(show.episode_count)
        )
    
    console.print(table)
```

### Show Create Command
```python
@shows_app.command("create")
def create_show(
    show_id: str = typer.Argument(..., help="Unique show identifier (kebab-case)"),
    title: str = typer.Option(..., "--title", "-t", prompt=True, help="Show title"),
    theme: str = typer.Option(..., "--theme", prompt=True, help="Show theme/description"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="Interactive mode")
):
    """Create a new show with protagonist."""
    
    blueprint_manager = BlueprintManager()
    
    # Check if show already exists
    if blueprint_manager.show_exists(show_id):
        console.print(f"[red]Error: Show '{show_id}' already exists[/red]")
        raise typer.Exit(1)
    
    # Interactive protagonist setup
    if interactive:
        console.print("\n[bold]Protagonist Setup[/bold]")
        protagonist_name = typer.prompt("  Name")
        protagonist_age = typer.prompt("  Age", type=int)
        protagonist_personality = typer.prompt("  Personality")
        protagonist_catchphrase = typer.prompt("  Catchphrase (optional)", default="")
    else:
        # Minimal protagonist for non-interactive mode
        protagonist_name = "Protagonist"
        protagonist_age = 10
        protagonist_personality = "Curious and enthusiastic"
        protagonist_catchphrase = ""
    
    # Create show
    try:
        show = blueprint_manager.create_show(
            show_id=show_id,
            title=title,
            theme=theme,
            protagonist={
                "name": protagonist_name,
                "age": protagonist_age,
                "personality": protagonist_personality,
                "catchphrase": protagonist_catchphrase
            }
        )
        
        console.print(f"\n[green]✓[/green] Show created: {show.id}")
        console.print(f"  Title: {show.title}")
        console.print(f"  Protagonist: {protagonist_name}")
        console.print(f"  Directory: {show.data_dir}")
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)
```

### Show Info Command
```python
@shows_app.command("info")
def show_info(
    show_id: str = typer.Argument(..., help="Show identifier")
):
    """Display complete Show Blueprint information."""
    
    blueprint_manager = BlueprintManager()
    
    try:
        show = blueprint_manager.load_show(show_id)
    except ShowNotFoundError:
        console.print(f"[red]Error: Show '{show_id}' not found[/red]")
        raise typer.Exit(1)
    
    # Show metadata
    console.print(f"\n[bold cyan]{show.title}[/bold cyan]")
    console.print(f"[dim]ID: {show.id}[/dim]\n")
    console.print(f"[bold]Theme:[/bold] {show.theme}")
    
    # Protagonist
    console.print(f"\n[bold]Protagonist:[/bold]")
    console.print(f"  Name: {show.protagonist.name}")
    console.print(f"  Age: {show.protagonist.age}")
    console.print(f"  Personality: {show.protagonist.personality}")
    if show.protagonist.catchphrase:
        console.print(f"  Catchphrase: \"{show.protagonist.catchphrase}\"")
    
    # Supporting characters
    if show.characters:
        console.print(f"\n[bold]Supporting Characters:[/bold] {len(show.characters)}")
        for char in show.characters[:5]:  # Show first 5
            console.print(f"  • {char.name} ({char.role})")
        if len(show.characters) > 5:
            console.print(f"  ... and {len(show.characters) - 5} more")
    
    # Concepts
    if show.concepts_covered:
        console.print(f"\n[bold]Concepts Covered:[/bold] {len(show.concepts_covered)}")
        for concept in show.concepts_covered[:10]:  # Show first 10
            console.print(f"  • {concept}")
        if len(show.concepts_covered) > 10:
            console.print(f"  ... and {len(show.concepts_covered) - 10} more")
    
    # Episodes
    console.print(f"\n[bold]Episodes:[/bold] {show.episode_count}")
```

### Character List Command
```python
@shows_app.command("characters")
def list_characters(
    show_id: str = typer.Argument(..., help="Show identifier")
):
    """List supporting characters for a show."""
    
    blueprint_manager = BlueprintManager()
    
    try:
        show = blueprint_manager.load_show(show_id)
    except ShowNotFoundError:
        console.print(f"[red]Error: Show '{show_id}' not found[/red]")
        raise typer.Exit(1)
    
    if not show.characters:
        console.print("[yellow]No supporting characters found[/yellow]")
        return
    
    table = Table(title=f"Characters - {show.title}")
    table.add_column("Name", style="cyan")
    table.add_column("Role", style="white")
    table.add_column("Description", style="dim")
    
    for char in show.characters:
        desc = char.description[:60] + "..." if len(char.description) > 60 else char.description
        table.add_row(char.name, char.role, desc)
    
    console.print(table)
```

### Add Character Command
```python
@shows_app.command("add-character")
def add_character(
    show_id: str = typer.Argument(..., help="Show identifier"),
    name: str = typer.Option(..., "--name", "-n", prompt=True, help="Character name"),
    role: str = typer.Option(..., "--role", "-r", prompt=True, help="Character role"),
    description: str = typer.Option(..., "--description", "-d", prompt=True, help="Character description")
):
    """Add a supporting character to a show."""
    
    blueprint_manager = BlueprintManager()
    
    try:
        show = blueprint_manager.load_show(show_id)
    except ShowNotFoundError:
        console.print(f"[red]Error: Show '{show_id}' not found[/red]")
        raise typer.Exit(1)
    
    try:
        char = blueprint_manager.add_character(
            show_id=show_id,
            name=name,
            role=role,
            description=description
        )
        
        console.print(f"\n[green]✓[/green] Character added: {char.name}")
        console.print(f"  Role: {char.role}")
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)
```

### Concepts List Command
```python
@shows_app.command("concepts")
def list_concepts(
    show_id: str = typer.Argument(..., help="Show identifier")
):
    """List concepts covered in a show."""
    
    blueprint_manager = BlueprintManager()
    
    try:
        show = blueprint_manager.load_show(show_id)
    except ShowNotFoundError:
        console.print(f"[red]Error: Show '{show_id}' not found[/red]")
        raise typer.Exit(1)
    
    if not show.concepts_covered:
        console.print("[yellow]No concepts covered yet[/yellow]")
        return
    
    console.print(f"\n[bold]Concepts Covered - {show.title}[/bold]\n")
    for i, concept in enumerate(show.concepts_covered, 1):
        console.print(f"  {i}. {concept}")
```

## 🧪 Testing Requirements

### Unit Tests
- **Show Commands Tests**:
  - List shows (empty and with shows)
  - Create show with valid inputs
  - Create show with duplicate ID (should fail)
  - Show info for existing and non-existing show
  - Edit protagonist
  
- **Character Commands Tests**:
  - List characters for show
  - Add character with valid inputs
  - List concepts for show
  
- **Validation Tests**:
  - Show ID format validation (kebab-case)
  - Character name validation (non-empty)

### Integration Tests
- **CLI Workflow Tests**:
  - Create show → List shows → Show info
  - Create show → Add character → List characters
  - Create show → List concepts

### Fixtures
```python
from typer.testing import CliRunner

@pytest.fixture
def cli_runner():
    return CliRunner()

@pytest.fixture
def test_show(tmp_path):
    """Create a test show for testing."""
    blueprint_manager = BlueprintManager(data_dir=tmp_path)
    return blueprint_manager.create_show(
        show_id="test-show",
        title="Test Show",
        theme="Testing theme",
        protagonist={"name": "Test", "age": 10}
    )

def test_show_list(cli_runner, test_show):
    result = cli_runner.invoke(app, ["shows", "list"])
    assert result.exit_code == 0
    assert "test-show" in result.stdout

def test_show_create(cli_runner):
    result = cli_runner.invoke(app, [
        "shows", "create", "new-show",
        "--title", "New Show",
        "--theme", "New theme",
        "--no-interactive"
    ])
    assert result.exit_code == 0
    assert "Show created" in result.stdout
```

## 📝 Implementation Notes

### Dependencies
```toml
[project]
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0"
]
```

### Key Design Decisions
1. **Typer Framework**: Type-safe CLI with automatic help generation
2. **Rich for UI**: Beautiful terminal output with tables, colors
3. **Interactive Mode**: Default to interactive prompts for better UX
4. **Validation**: Validate show IDs, character names at CLI level
5. **Error Handling**: Clear error messages with suggestions

### CLI Conventions
- **Naming**: Kebab-case for commands (`shows list`, not `shows_list`)
- **Options**: Both short and long forms (`-t` / `--title`)
- **Colors**: Green for success, red for errors, yellow for warnings, cyan for info
- **Tables**: Use for listing commands (shows, characters, concepts)
- **Prompts**: Use rich.prompt for interactive input

## 📂 File Structure
```
src/cli/
├── __init__.py
├── main.py                # CLI app entry point
├── shows.py               # Show commands
└── show_blueprint.py      # Show Blueprint commands

tests/cli/
├── test_shows.py
├── test_show_blueprint.py
└── test_show_integration.py
```

## ✅ Definition of Done
- [ ] CLI framework with shows command group
- [ ] Show management commands: list, create, init, info, edit-protagonist, edit-world
- [ ] Show Blueprint commands: characters, add-character, concepts, suggest-topics
- [ ] Interactive prompts for show/character creation
- [ ] Formatted output with rich (tables, colors)
- [ ] Test coverage ≥ 75% for show CLI modules
- [ ] CLI integration tests for show workflows
- [ ] Help text for all commands with examples

# WP7: CLI Interface

**Status**: ⏳ Not Started  
**Dependencies**: WP1 (Foundation), WP6 (Orchestrator)  
**Estimated Effort**: 2-3 days  
**Owner**: TBD  
**Subsystem:** User Interface

## 📋 Overview

CLI provides command-line interface for **show management**, **episode generation**, and system utilities. Built with Typer for intuitive commands and rich for beautiful terminal output. Supports show creation, Show Blueprint editing, episode creation with approval workflow, and configuration.

**Key Deliverables**:
- Show management commands (list, create, init, info)
- Show Blueprint commands (characters, concepts, suggest-topics)
- Episode management commands (create, resume, list, approve)
- Configuration commands (show, set-provider)
- Progress visualization with rich
- Interactive prompts for show and episode creation

**System Context**:
- **Subsystem:** User Interface
- **Depends on:** WP1 (Foundation), WP6 (Orchestrator)
- **Used by:** End users, developers
- **Parallel Development:** ✅ Can develop in parallel with WP9 after WP6 complete

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

### Task 7.4: Episode Commands
Manage episode generation and lifecycle with approval workflow.

**Subtasks**:
- [ ] 7.4.1: Implement `episodes create <show-id> <topic>` command
- [ ] 7.4.2: Implement `episodes resume <episode-id>` command
- [ ] 7.4.3: Implement `episodes list [--show <show-id>] [--status <status>]` command
- [ ] 7.4.4: Implement `episodes show <episode-id>` command (detailed info)
- [ ] 7.4.5: Implement `episodes approve <episode-id>` command (approve outline, optionally edit)
- [ ] 7.4.6: Implement `episodes reject <episode-id> --feedback <text>` command
- [ ] 7.4.7: Implement `episodes delete <episode-id>` command
- [ ] 7.4.8: Display real-time progress during generation (pause at AWAITING_APPROVAL)
- [ ] 7.4.9: Show outline for review when episode reaches AWAITING_APPROVAL

**Expected Outputs**:
- `src/cli/episodes.py`
- Episode management commands with approval workflow

### Task 7.5: Configuration Commands
Manage system settings.

**Subtasks**:
- [ ] 7.5.1: Implement `config show` command (display all settings)
- [ ] 7.5.2: Implement `config set-provider <service> <provider>` command
- [ ] 7.5.3: Implement `config toggle-mock` command (enable/disable mock services)
- [ ] 7.5.4: Implement `config api-keys` command (show/set API keys)
- [ ] 7.5.5: Add validation for configuration changes

**Expected Outputs**:
- `src/cli/config.py`
- Configuration commands

### Task 7.6: Progress Visualization
Beautiful terminal output for pipeline execution.

**Subtasks**:
- [ ] 7.5.1: Implement progress bars with rich.progress
- [ ] 7.5.2: Show current stage and percentage complete
- [ ] 7.5.3: Display estimated time remaining
- [ ] 7.5.4: Color-code status messages (success, error, warning)
- [ ] 7.5.5: Add spinner for long-running operations
- [ ] 7.5.6: Display cost tracking during execution

**Expected Outputs**:
- `src/cli/progress.py`
- Progress visualization utilities

### Task 7.6: Interactive Prompts
User-friendly interactive mode.

**Subtasks**:
- [ ] 7.6.1: Implement topic input prompt with validation
- [ ] 7.6.2: Implement character selection (multi-select from available)
- [ ] 7.6.3: Implement duration selection with constraints (5-20 min)
- [ ] 7.6.4: Add confirmation before expensive operations
- [ ] 7.6.5: Provide helpful error messages for invalid inputs

**Expected Outputs**:
- Interactive prompts using rich.prompt

### Task 7.7: Integration Testing
Validate CLI commands end-to-end.

**Subtasks**:
- [ ] 7.7.1: Test episode create command with mock services
- [ ] 7.7.2: Test episode resume command
- [ ] 7.7.3: Test character list and show commands
- [ ] 7.7.4: Test config commands
- [ ] 7.7.5: Test error handling for invalid inputs

**Expected Outputs**:
- CLI integration tests in `tests/test_cli_integration.py`

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
episodes_app = typer.Typer(help="Manage episodes")
characters_app = typer.Typer(help="Manage characters")
config_app = typer.Typer(help="Manage configuration")

app.add_typer(episodes_app, name="episodes")
app.add_typer(characters_app, name="characters")
app.add_typer(config_app, name="config")

console = Console()

@app.command()
def version():
    """Show version information."""
    console.print("[bold blue]Kids Podcast Generator v0.1.0[/bold blue]")

if __name__ == "__main__":
    app()
```

### Episode Create Command
```python
@episodes_app.command("create")
def create_episode(
    topic: str = typer.Option(..., "--topic", "-t", prompt=True, help="Episode topic"),
    characters: list[str] = typer.Option(["oliver", "hannah"], "--characters", "-c", help="Character IDs"),
    duration: int = typer.Option(15, "--duration", "-d", help="Duration in minutes (5-20)"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode")
):
    """Create a new podcast episode."""
    
    # Validate duration
    if not 5 <= duration <= 20:
        console.print("[red]Error: Duration must be between 5 and 20 minutes[/red]")
        raise typer.Exit(1)
    
    # Load characters
    char_manager = CharacterManager()
    try:
        chars = [char_manager.load_character(c) for c in characters]
    except CharacterNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    
    # Create orchestrator
    orchestrator = create_orchestrator()
    
    # Show summary
    console.print(f"\n[bold]Creating episode:[/bold]")
    console.print(f"  Topic: {topic}")
    console.print(f"  Characters: {', '.join([c.name for c in chars])}")
    console.print(f"  Duration: {duration} minutes")
    console.print(f"  Using {'MOCK' if get_settings().USE_MOCK_SERVICES else 'REAL'} services\n")
    
    # Confirm
    if not interactive:
        confirm = typer.confirm("Generate episode?")
        if not confirm:
            raise typer.Abort()
    
    # Generate with progress bar
    with Progress() as progress:
        task = progress.add_task("[cyan]Generating episode...", total=100)
        
        try:
            episode = orchestrator.generate_episode(
                topic=topic,
                characters=chars,
                duration=duration
            )
            progress.update(task, completed=100)
            
            console.print(f"\n[green]✓[/green] Episode created: {episode.id}")
            console.print(f"  Output: {episode.audio_path}")
            console.print(f"  Cost: ${episode.total_cost:.2f}")
        except Exception as e:
            console.print(f"\n[red]✗ Error: {e}[/red]")
            raise typer.Exit(1)
```

### Episode List Command
```python
@episodes_app.command("list")
def list_episodes(
    status: str | None = typer.Option(None, "--status", "-s", help="Filter by status")
):
    """List all episodes."""
    
    storage = EpisodeStorage()
    episodes = storage.list_episodes()
    
    if status:
        episodes = [e for e in episodes if e.status.value == status.upper()]
    
    if not episodes:
        console.print("[yellow]No episodes found[/yellow]")
        return
    
    # Create table
    table = Table(title="Episodes")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Status", style="green")
    table.add_column("Duration", justify="right")
    table.add_column("Created", style="dim")
    
    for episode in episodes:
        status_color = {
            "COMPLETE": "green",
            "ERROR": "red",
            "IDEATION": "yellow",
            "SCRIPTING": "yellow",
            "AUDIO_SYNTHESIS": "yellow",
            "AUDIO_MIXING": "yellow"
        }.get(episode.status.value, "white")
        
        table.add_row(
            episode.id,
            episode.title,
            f"[{status_color}]{episode.status.value}[/{status_color}]",
            f"{episode.duration_minutes} min",
            episode.created_at.strftime("%Y-%m-%d")
        )
    
    console.print(table)
```

### Character List Command
```python
@characters_app.command("list")
def list_characters():
    """List all available characters."""
    
    char_manager = CharacterManager()
    characters = char_manager.list_characters()
    
    if not characters:
        console.print("[yellow]No characters found[/yellow]")
        return
    
    table = Table(title="Characters")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Age", justify="right")
    table.add_column("Personality", style="dim")
    
    for char in characters:
        table.add_row(
            char.id,
            char.name,
            str(char.age),
            char.personality[:50] + "..." if len(char.personality) > 50 else char.personality
        )
    
    console.print(table)
```

### Config Show Command
```python
@config_app.command("show")
def show_config():
    """Show current configuration."""
    
    settings = get_settings()
    
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Mock Services", "✓ Enabled" if settings.USE_MOCK_SERVICES else "✗ Disabled")
    table.add_row("LLM Provider", settings.LLM_PROVIDER)
    table.add_row("TTS Provider", settings.TTS_PROVIDER)
    table.add_row("Image Provider", settings.IMAGE_PROVIDER)
    table.add_row("Data Directory", str(settings.DATA_DIR))
    
    # API Keys (mask values)
    if settings.OPENAI_API_KEY:
        table.add_row("OpenAI API Key", "sk-..." + settings.OPENAI_API_KEY[-4:])
    if settings.ANTHROPIC_API_KEY:
        table.add_row("Anthropic API Key", "sk-ant-..." + settings.ANTHROPIC_API_KEY[-4:])
    if settings.ELEVENLABS_API_KEY:
        table.add_row("ElevenLabs API Key", "..." + settings.ELEVENLABS_API_KEY[-4:])
    
    console.print(table)
```

## 🧪 Testing Requirements

### Unit Tests
- **Command Tests**:
  - Episode create with valid inputs
  - Episode create with invalid inputs (duration out of range)
  - Episode list with no episodes
  - Episode list with filter
  - Character list
  - Config show
  
- **Validation Tests**:
  - Duration constraint (5-20 minutes)
  - Character ID validation
  - Topic validation (non-empty)

### Integration Tests
- **CLI Workflow Tests**:
  - Create episode → List episodes → Show episode
  - Resume episode after interruption
  - Character create → Validate → Show
  - Config toggle-mock → Create episode (verify mock used)

### Fixtures
```python
from typer.testing import CliRunner

@pytest.fixture
def cli_runner():
    return CliRunner()

def test_episode_create(cli_runner):
    result = cli_runner.invoke(app, [
        "episodes", "create",
        "--topic", "How rockets work",
        "--characters", "oliver",
        "--characters", "hannah",
        "--duration", "15"
    ])
    assert result.exit_code == 0
    assert "Episode created" in result.stdout
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
2. **Rich for UI**: Beautiful terminal output with tables, progress bars, colors
3. **Command Groups**: Logical organization (episodes, characters, config)
4. **Interactive Mode**: Prompts for missing arguments
5. **Confirmation Prompts**: Prevent accidental expensive operations

### CLI Conventions
- **Naming**: Kebab-case for commands (`episodes create`, not `episodes_create`)
- **Options**: Both short and long forms (`-t` / `--topic`)
- **Colors**: Green for success, red for errors, yellow for warnings, cyan for info
- **Tables**: Use for listing commands (episodes, characters)
- **Progress**: Show for long-running operations

## 📂 File Structure
```
src/cli/
├── __init__.py
├── main.py                # CLI app entry point
├── episodes.py            # Episode commands
├── characters.py          # Character commands
├── config.py              # Config commands
└── progress.py            # Progress visualization

tests/cli/
├── test_episodes.py
├── test_characters.py
├── test_config.py
└── test_cli_integration.py
```

## ✅ Definition of Done
- [ ] CLI app with 3 command groups (episodes, characters, config)
- [ ] Episode commands: create, resume, list, show, delete
- [ ] Character commands: list, show, create, validate
- [ ] Config commands: show, set-provider, toggle-mock
- [ ] Progress visualization with rich (progress bars, spinners, colors)
- [ ] Interactive prompts for episode creation
- [ ] Test coverage ≥ 75% for CLI modules
- [ ] CLI integration tests for common workflows
- [ ] Documentation includes CLI usage guide with examples

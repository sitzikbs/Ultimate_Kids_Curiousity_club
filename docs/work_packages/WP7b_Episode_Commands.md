# WP7b: Episode Commands

**Status**: ✅ Complete  
**Parent WP**: [WP7: CLI Interface](WP7_CLI.md)  
**Dependencies**: WP1 (Foundation), WP6 (Orchestrator), WP7a (Show Commands)  
**Estimated Effort**: 1-2 days  
**Owner**: TBD  
**Subsystem:** User Interface

## 📋 Overview

Episode Commands provide CLI interface for **episode creation**, **approval workflow**, **progress monitoring**, and **testing**. Built with Typer for intuitive commands and rich for beautiful terminal output. Supports episode generation with real-time progress, approval workflow (pause at AWAITING_APPROVAL), resume functionality, and configuration management.

**Key Deliverables**:
- Episode management commands (create, resume, list, approve)
- Approval workflow integration (pause, review, approve/reject)
- Configuration commands (show, set-provider, toggle-mock)
- Progress visualization with rich (progress bars, spinners, cost tracking)
- Interactive prompts for episode creation

**System Context**:
- **Subsystem:** User Interface
- **Depends on:** WP1 (Foundation), WP6 (Orchestrator), WP7a (Show Commands)
- **Used by:** End users, developers
- **Related WPs:** WP7a (Show Commands)

## 🎯 High-Level Tasks

### Task 7.4: Episode Commands
Manage episode generation and lifecycle with approval workflow.

**Subtasks**:
- [x] 7.4.1: Implement `episodes create <show-id> <topic>` command
- [x] 7.4.2: Implement `episodes resume <episode-id>` command
- [x] 7.4.3: Implement `episodes list [--show <show-id>] [--status <status>]` command
- [x] 7.4.4: Implement `episodes show <episode-id>` command (detailed info)
- [x] 7.4.5: Implement `episodes approve <episode-id>` command (approve outline, optionally edit)
- [x] 7.4.6: Implement `episodes reject <episode-id> --feedback <text>` command
- [x] 7.4.7: Implement `episodes delete <episode-id>` command
- [x] 7.4.8: Display real-time progress during generation (pause at AWAITING_APPROVAL)
- [x] 7.4.9: Show outline for review when episode reaches AWAITING_APPROVAL

**Expected Outputs**:
- `src/cli/episodes.py`
- Episode management commands with approval workflow

### Task 7.5: Configuration Commands
Manage system settings.

**Subtasks**:
- [x] 7.5.1: Implement `config show` command (display all settings)
- [ ] 7.5.2: Implement `config set-provider <service> <provider>` command (deferred — runtime-only config)
- [ ] 7.5.3: Implement `config toggle-mock` command (deferred — runtime-only config)
- [ ] 7.5.4: Implement `config api-keys` command (deferred — runtime-only config)
- [x] 7.5.5: Add validation for configuration changes

**Expected Outputs**:
- `src/cli/config.py`
- Configuration commands

### Task 7.6: Progress Visualization
Beautiful terminal output for pipeline execution.

**Subtasks**:
- [x] 7.6.1: Implement progress bars with rich.progress
- [x] 7.6.2: Show current stage and percentage complete
- [x] 7.6.3: Display estimated time remaining
- [x] 7.6.4: Color-code status messages (success, error, warning)
- [x] 7.6.5: Add spinner for long-running operations
- [x] 7.6.6: Display cost tracking during execution

**Expected Outputs**:
- `src/cli/progress.py`
- Progress visualization utilities

### Task 7.7: Integration Testing
Validate CLI commands end-to-end.

**Subtasks**:
- [x] 7.7.1: Test episode create command with mock services
- [x] 7.7.2: Test episode resume command
- [x] 7.7.3: Test approval workflow (approve/reject)
- [x] 7.7.4: Test config commands
- [x] 7.7.5: Test error handling for invalid inputs

**Expected Outputs**:
- CLI integration tests in `tests/test_cli_integration.py`

## 🔧 Technical Specifications

### Episode Create Command
```python
@episodes_app.command("create")
def create_episode(
    show_id: str = typer.Argument(..., help="Show identifier"),
    topic: str = typer.Option(..., "--topic", "-t", prompt=True, help="Episode topic"),
    characters: list[str] = typer.Option(None, "--characters", "-c", help="Character IDs (defaults to protagonist)"),
    duration: int = typer.Option(15, "--duration", "-d", help="Duration in minutes (5-20)"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode")
):
    """Create a new podcast episode."""
    
    # Validate duration
    if not 5 <= duration <= 20:
        console.print("[red]Error: Duration must be between 5 and 20 minutes[/red]")
        raise typer.Exit(1)
    
    # Load show
    blueprint_manager = BlueprintManager()
    try:
        show = blueprint_manager.load_show(show_id)
    except ShowNotFoundError:
        console.print(f"[red]Error: Show '{show_id}' not found[/red]")
        raise typer.Exit(1)
    
    # Default to protagonist if no characters specified
    if not characters:
        characters = [show.protagonist.id]
    
    # Load characters
    try:
        chars = [blueprint_manager.load_character(show_id, c) for c in characters]
    except CharacterNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    
    # Create orchestrator
    orchestrator = create_orchestrator()
    
    # Show summary
    console.print(f"\n[bold]Creating episode:[/bold]")
    console.print(f"  Show: {show.title}")
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
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Generating episode...", total=100)
        
        try:
            episode = orchestrator.generate_episode(
                show_id=show_id,
                topic=topic,
                characters=chars,
                duration=duration,
                progress_callback=lambda pct, stage: progress.update(
                    task, 
                    completed=pct,
                    description=f"[cyan]{stage}..."
                )
            )
            
            # Check if episode is awaiting approval
            if episode.status == EpisodeStatus.AWAITING_APPROVAL:
                progress.stop()
                console.print("\n[yellow]⏸ Episode generation paused for approval[/yellow]")
                console.print(f"\n[bold]Episode Outline:[/bold]")
                console.print(episode.outline)
                console.print(f"\nReview with: [cyan]episodes show {episode.id}[/cyan]")
                console.print(f"Approve with: [cyan]episodes approve {episode.id}[/cyan]")
                console.print(f"Reject with: [cyan]episodes reject {episode.id} --feedback \"reason\"[/cyan]")
            elif episode.status == EpisodeStatus.COMPLETE:
                progress.update(task, completed=100)
                console.print(f"\n[green]✓[/green] Episode completed: {episode.id}")
                console.print(f"  Title: {episode.title}")
                console.print(f"  Output: {episode.audio_path}")
                console.print(f"  Cost: ${episode.total_cost:.2f}")
            
        except Exception as e:
            console.print(f"\n[red]✗ Error: {e}[/red]")
            raise typer.Exit(1)
```

### Episode Resume Command
```python
@episodes_app.command("resume")
def resume_episode(
    episode_id: str = typer.Argument(..., help="Episode identifier")
):
    """Resume episode generation from current state."""
    
    storage = EpisodeStorage()
    
    try:
        episode = storage.load_episode(episode_id)
    except EpisodeNotFoundError:
        console.print(f"[red]Error: Episode '{episode_id}' not found[/red]")
        raise typer.Exit(1)
    
    # Check if episode can be resumed
    if episode.status == EpisodeStatus.COMPLETE:
        console.print(f"[yellow]Episode '{episode_id}' is already complete[/yellow]")
        return
    
    if episode.status == EpisodeStatus.AWAITING_APPROVAL:
        console.print(f"[yellow]Episode '{episode_id}' is awaiting approval[/yellow]")
        console.print(f"Approve with: [cyan]episodes approve {episode_id}[/cyan]")
        return
    
    if episode.status == EpisodeStatus.ERROR:
        console.print(f"[yellow]Episode '{episode_id}' has errors. Retrying from last successful stage...[/yellow]")
    
    # Resume generation
    orchestrator = create_orchestrator()
    
    console.print(f"\n[bold]Resuming episode:[/bold] {episode.title}")
    console.print(f"  Current stage: {episode.status.value}\n")
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Resuming...", total=100)
        
        try:
            episode = orchestrator.resume_episode(
                episode_id=episode_id,
                progress_callback=lambda pct, stage: progress.update(
                    task,
                    completed=pct,
                    description=f"[cyan]{stage}..."
                )
            )
            
            if episode.status == EpisodeStatus.AWAITING_APPROVAL:
                progress.stop()
                console.print("\n[yellow]⏸ Episode generation paused for approval[/yellow]")
                console.print(f"Approve with: [cyan]episodes approve {episode_id}[/cyan]")
            elif episode.status == EpisodeStatus.COMPLETE:
                progress.update(task, completed=100)
                console.print(f"\n[green]✓[/green] Episode completed: {episode.id}")
                console.print(f"  Output: {episode.audio_path}")
                console.print(f"  Total cost: ${episode.total_cost:.2f}")
        except Exception as e:
            console.print(f"\n[red]✗ Error: {e}[/red]")
            raise typer.Exit(1)
```

### Episode List Command
```python
@episodes_app.command("list")
def list_episodes(
    show_id: str | None = typer.Option(None, "--show", "-s", help="Filter by show"),
    status: str | None = typer.Option(None, "--status", help="Filter by status")
):
    """List all episodes."""
    
    storage = EpisodeStorage()
    episodes = storage.list_episodes(show_id=show_id)
    
    if status:
        episodes = [e for e in episodes if e.status.value == status.upper()]
    
    if not episodes:
        console.print("[yellow]No episodes found[/yellow]")
        return
    
    # Create table
    table = Table(title="Episodes")
    table.add_column("ID", style="cyan")
    table.add_column("Show", style="white")
    table.add_column("Title", style="white")
    table.add_column("Status", style="green")
    table.add_column("Duration", justify="right")
    table.add_column("Created", style="dim")
    
    for episode in episodes:
        status_color = {
            "COMPLETE": "green",
            "ERROR": "red",
            "AWAITING_APPROVAL": "yellow",
            "IDEATION": "cyan",
            "SCRIPTING": "cyan",
            "AUDIO_SYNTHESIS": "cyan",
            "AUDIO_MIXING": "cyan"
        }.get(episode.status.value, "white")
        
        table.add_row(
            episode.id,
            episode.show_id,
            episode.title,
            f"[{status_color}]{episode.status.value}[/{status_color}]",
            f"{episode.duration_minutes} min",
            episode.created_at.strftime("%Y-%m-%d")
        )
    
    console.print(table)
```

### Episode Approve Command
```python
@episodes_app.command("approve")
def approve_episode(
    episode_id: str = typer.Argument(..., help="Episode identifier"),
    edit: bool = typer.Option(False, "--edit", "-e", help="Edit outline before approving")
):
    """Approve episode outline and continue generation."""
    
    storage = EpisodeStorage()
    
    try:
        episode = storage.load_episode(episode_id)
    except EpisodeNotFoundError:
        console.print(f"[red]Error: Episode '{episode_id}' not found[/red]")
        raise typer.Exit(1)
    
    if episode.status != EpisodeStatus.AWAITING_APPROVAL:
        console.print(f"[yellow]Episode '{episode_id}' is not awaiting approval[/yellow]")
        console.print(f"Current status: {episode.status.value}")
        return
    
    # Show outline
    console.print(f"\n[bold]Episode Outline:[/bold]")
    console.print(episode.outline)
    
    # Edit if requested
    if edit:
        console.print("\n[dim]Opening outline in $EDITOR...[/dim]")
        # Open in editor and save changes
        edited_outline = edit_in_editor(episode.outline)
        episode.outline = edited_outline
        storage.save_episode(episode)
    
    # Confirm approval
    confirm = typer.confirm("\nApprove this outline and continue generation?")
    if not confirm:
        console.print("[yellow]Approval cancelled[/yellow]")
        return
    
    # Approve and resume
    orchestrator = create_orchestrator()
    
    try:
        orchestrator.approve_episode(episode_id)
        console.print(f"\n[green]✓[/green] Episode approved")
        console.print(f"Resuming generation with: [cyan]episodes resume {episode_id}[/cyan]")
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)
```

### Episode Reject Command
```python
@episodes_app.command("reject")
def reject_episode(
    episode_id: str = typer.Argument(..., help="Episode identifier"),
    feedback: str = typer.Option(..., "--feedback", "-f", prompt=True, help="Rejection feedback")
):
    """Reject episode outline and provide feedback."""
    
    storage = EpisodeStorage()
    
    try:
        episode = storage.load_episode(episode_id)
    except EpisodeNotFoundError:
        console.print(f"[red]Error: Episode '{episode_id}' not found[/red]")
        raise typer.Exit(1)
    
    if episode.status != EpisodeStatus.AWAITING_APPROVAL:
        console.print(f"[yellow]Episode '{episode_id}' is not awaiting approval[/yellow]")
        return
    
    # Reject with feedback
    orchestrator = create_orchestrator()
    
    try:
        orchestrator.reject_episode(episode_id, feedback=feedback)
        console.print(f"\n[green]✓[/green] Episode rejected")
        console.print(f"  Feedback: {feedback}")
        console.print(f"\nRegenerate outline with: [cyan]episodes resume {episode_id}[/cyan]")
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)
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

### Config Set Provider Command
```python
@config_app.command("set-provider")
def set_provider(
    service: str = typer.Argument(..., help="Service (llm, tts, image)"),
    provider: str = typer.Argument(..., help="Provider name")
):
    """Set provider for a service."""
    
    valid_services = ["llm", "tts", "image"]
    if service not in valid_services:
        console.print(f"[red]Error: Invalid service. Must be one of: {', '.join(valid_services)}[/red]")
        raise typer.Exit(1)
    
    # Validate provider
    valid_providers = {
        "llm": ["openai", "anthropic"],
        "tts": ["elevenlabs", "openai"],
        "image": ["dall-e", "stable-diffusion"]
    }
    
    if provider not in valid_providers[service]:
        console.print(f"[red]Error: Invalid provider for {service}. Must be one of: {', '.join(valid_providers[service])}[/red]")
        raise typer.Exit(1)
    
    # Update config
    config_manager = ConfigManager()
    config_manager.set_provider(service, provider)
    
    console.print(f"[green]✓[/green] Set {service} provider to: {provider}")
```

## 🧪 Testing Requirements

### Unit Tests
- **Episode Commands Tests**:
  - Create episode with valid inputs
  - Create episode with invalid duration (should fail)
  - Resume episode in different states
  - List episodes with filters
  - Approve/reject episode workflow
  
- **Config Commands Tests**:
  - Show config
  - Set provider with valid/invalid values
  - Toggle mock services
  
- **Validation Tests**:
  - Duration constraint (5-20 minutes)
  - Episode ID validation
  - Topic validation (non-empty)

### Integration Tests
- **CLI Workflow Tests**:
  - Create episode → Pause at approval → Approve → Resume → Complete
  - Create episode → Reject → Regenerate
  - Episode create → List episodes → Show episode
  - Config toggle-mock → Create episode (verify mock used)

### Fixtures
```python
from typer.testing import CliRunner

@pytest.fixture
def cli_runner():
    return CliRunner()

@pytest.fixture
def test_episode(tmp_path):
    """Create a test episode."""
    storage = EpisodeStorage(data_dir=tmp_path)
    return storage.create_episode(
        show_id="test-show",
        topic="Test Topic",
        duration=15
    )

def test_episode_create(cli_runner):
    result = cli_runner.invoke(app, [
        "episodes", "create", "test-show",
        "--topic", "How rockets work",
        "--duration", "15"
    ])
    assert result.exit_code == 0
    assert "Episode created" in result.stdout or "paused for approval" in result.stdout

def test_episode_approve(cli_runner, test_episode):
    # Set episode to awaiting approval
    test_episode.status = EpisodeStatus.AWAITING_APPROVAL
    storage = EpisodeStorage()
    storage.save_episode(test_episode)
    
    result = cli_runner.invoke(app, [
        "episodes", "approve", test_episode.id
    ], input="y\n")
    assert result.exit_code == 0
    assert "approved" in result.stdout
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
1. **Approval Workflow**: Pause episode generation at outline stage for review
2. **Resume Functionality**: Support resuming from any stage (error recovery)
3. **Progress Visualization**: Real-time progress bars with stage indicators
4. **Cost Tracking**: Display costs during and after generation
5. **Interactive Editing**: Option to edit outline before approval

### CLI Conventions
- **Naming**: Kebab-case for commands (`episodes create`, not `episodes_create`)
- **Options**: Both short and long forms (`-t` / `--topic`)
- **Colors**: Green for success, red for errors, yellow for warnings/paused, cyan for in-progress
- **Progress**: Show spinner and progress bar for long operations
- **Confirmation**: Required for expensive operations (approve, create)

## 📂 File Structure
```
src/cli/
├── __init__.py
├── main.py                # CLI app entry point
├── episodes.py            # Episode commands
├── config.py              # Config commands
└── progress.py            # Progress visualization

tests/cli/
├── test_episodes.py
├── test_config.py
└── test_cli_integration.py
```

## ✅ Definition of Done
- [ ] Episode commands: create, resume, list, show, approve, reject, delete
- [ ] Approval workflow with outline review
- [ ] Progress visualization with rich (progress bars, spinners, colors, cost tracking)
- [ ] Config commands: show, set-provider, toggle-mock, api-keys
- [ ] Interactive prompts for episode creation
- [ ] Test coverage ≥ 75% for episode CLI modules
- [ ] CLI integration tests for episode workflows (create→approve→resume)
- [ ] Documentation includes CLI usage guide with approval workflow examples

"""Episode management commands for the Kids Podcast Generator CLI.

Covers the full episode lifecycle: create → approve/reject → resume → complete.
"""

import asyncio
import logging

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cli.factory import create_approval_workflow, create_pipeline, create_storage
from models.episode import PipelineStage

logger = logging.getLogger(__name__)

episodes_app = typer.Typer(help="Manage episodes (create, approve, resume, …)")
console = Console()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _run_async(coro):
    """Bridge async orchestrator calls into sync Typer commands."""
    return asyncio.run(coro)


def _stage_style(stage: PipelineStage) -> str:
    """Return a Rich colour tag for the given pipeline stage."""
    styles: dict[PipelineStage, str] = {
        PipelineStage.PENDING: "dim",
        PipelineStage.IDEATION: "blue",
        PipelineStage.OUTLINING: "blue",
        PipelineStage.AWAITING_APPROVAL: "yellow",
        PipelineStage.APPROVED: "green",
        PipelineStage.REJECTED: "red",
        PipelineStage.SEGMENT_GENERATION: "cyan",
        PipelineStage.SCRIPT_GENERATION: "cyan",
        PipelineStage.AUDIO_SYNTHESIS: "magenta",
        PipelineStage.AUDIO_MIXING: "magenta",
        PipelineStage.COMPLETE: "bold green",
        PipelineStage.FAILED: "bold red",
    }
    return styles.get(stage, "white")


def _format_stage(stage: PipelineStage) -> str:
    """Return a Rich-formatted stage label."""
    style = _stage_style(stage)
    return f"[{style}]{stage.value}[/{style}]"


# ------------------------------------------------------------------
# Commands
# ------------------------------------------------------------------


@episodes_app.command("list")
def list_episodes(
    show_id: str = typer.Argument(..., help="Show identifier"),
):
    """List all episodes for a show."""
    try:
        storage = create_storage()
        episode_ids = storage.list_episodes(show_id)

        if not episode_ids:
            console.print(f"[yellow]No episodes found for show '{show_id}'[/yellow]")
            console.print("\n[dim]Create one with:[/dim]")
            console.print(
                f"  [cyan]kids-podcast episodes create {show_id} \"My Topic\"[/cyan]"
            )
            return

        table = Table(title=f"Episodes for '{show_id}'")
        table.add_column("Episode ID", style="cyan", no_wrap=True)
        table.add_column("Topic", style="white")
        table.add_column("Stage", no_wrap=True)
        table.add_column("Title", style="dim")

        for ep_id in episode_ids:
            try:
                ep = storage.load_episode(show_id, ep_id)
                table.add_row(
                    ep.episode_id,
                    ep.topic[:40] + ("…" if len(ep.topic) > 40 else ""),
                    _format_stage(ep.current_stage),
                    (ep.title or "")[:30],
                )
            except Exception:
                table.add_row(ep_id, "[red]<load error>[/red]", "", "")

        console.print(table)

    except FileNotFoundError:
        console.print(f"[red]Show '{show_id}' not found[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error listing episodes: {e}[/red]")
        raise typer.Exit(1)


@episodes_app.command("create")
def create_episode(
    show_id: str = typer.Argument(..., help="Show identifier"),
    topic: str = typer.Argument(..., help="Episode topic / educational concept"),
    title: str | None = typer.Option(None, "--title", "-t", help="Explicit title"),
):
    """Create a new episode and run through IDEATION → OUTLINING → AWAITING_APPROVAL.

    The pipeline pauses at the approval gate. Use 'approve' or 'reject' next.
    """
    try:
        pipeline = create_pipeline()

        with console.status("[bold blue]Generating episode…[/bold blue]"):
            result = _run_async(
                pipeline.generate_episode(
                    show_id=show_id,
                    topic=topic,
                    title=title,
                )
            )

        episode = result.episode
        console.print(
            Panel(
                f"[bold]Episode created:[/bold] {episode.episode_id}\n"
                f"[bold]Topic:[/bold]  {episode.topic}\n"
                f"[bold]Title:[/bold]  {episode.title}\n"
                f"[bold]Stage:[/bold]  {_format_stage(episode.current_stage)}",
                title="[yellow]Approval Required[/yellow]",
                border_style="yellow",
            )
        )
        console.print(
            f"\n[dim]Next steps:[/dim]\n"
            f"  Review outline:  [cyan]kids-podcast episodes show "
            f"{show_id} {episode.episode_id}[/cyan]\n"
            f"  Approve:         [cyan]kids-podcast episodes approve "
            f"{show_id} {episode.episode_id}[/cyan]\n"
            f"  Reject:          [cyan]kids-podcast episodes reject "
            f"{show_id} {episode.episode_id}[/cyan]"
        )

    except FileNotFoundError:
        console.print(f"[red]Show '{show_id}' not found[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error creating episode: {e}[/red]")
        logger.exception("Episode creation failed")
        raise typer.Exit(1)


@episodes_app.command("show")
def show_episode(
    show_id: str = typer.Argument(..., help="Show identifier"),
    episode_id: str = typer.Argument(..., help="Episode identifier"),
):
    """Display detailed information about an episode."""
    try:
        storage = create_storage()
        episode = storage.load_episode(show_id, episode_id)

        # Header
        console.print(
            Panel(
                f"[bold]ID:[/bold]    {episode.episode_id}\n"
                f"[bold]Show:[/bold]  {episode.show_id}\n"
                f"[bold]Topic:[/bold] {episode.topic}\n"
                f"[bold]Title:[/bold] {episode.title}\n"
                f"[bold]Stage:[/bold] {_format_stage(episode.current_stage)}",
                title="Episode Details",
                border_style="blue",
            )
        )

        # Approval info
        if episode.approval_status:
            console.print(
                f"\n[bold]Approval status:[/bold] {episode.approval_status}"
            )
        if episode.approval_feedback:
            console.print(
                f"[bold]Feedback:[/bold] {episode.approval_feedback}"
            )

        # Outline summary
        if episode.outline:
            console.print("\n[bold]Outline:[/bold]")
            console.print(f"  Title: {episode.outline.title}")
            console.print(f"  Story beats: {len(episode.outline.story_beats)}")
            for i, beat in enumerate(episode.outline.story_beats, 1):
                console.print(f"    {i}. {beat}")

        # Checkpoints
        if episode.checkpoints:
            table = Table(title="Checkpoints")
            table.add_column("Stage", style="cyan")
            table.add_column("Completed", style="dim")
            table.add_column("Cost", justify="right")

            for stage_name, cp in episode.checkpoints.items():
                table.add_row(
                    stage_name,
                    cp.get("completed_at", "?"),
                    f"${cp.get('cost', 0.0):.4f}",
                )
            console.print(table)
            console.print(f"[bold]Total cost:[/bold] ${episode.total_cost:.4f}")

        # Error info
        if episode.last_error:
            console.print(
                Panel(
                    str(episode.last_error),
                    title="[red]Last Error[/red]",
                    border_style="red",
                )
            )

    except FileNotFoundError:
        console.print(
            f"[red]Episode '{episode_id}' not found in show '{show_id}'[/red]"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@episodes_app.command("approve")
def approve_episode(
    show_id: str = typer.Argument(..., help="Show identifier"),
    episode_id: str = typer.Argument(..., help="Episode identifier"),
    feedback: str | None = typer.Option(None, "--feedback", "-f", help="Feedback text"),
    auto_resume: bool = typer.Option(
        False,
        "--resume/--no-resume",
        help="Immediately resume pipeline after approval",
    ),
):
    """Approve an episode outline and optionally resume the pipeline."""
    try:
        workflow = create_approval_workflow()
        episode = workflow.submit_approval(
            show_id=show_id,
            episode_id=episode_id,
            approved=True,
            feedback=feedback,
        )
        console.print(f"[green]✓ Episode {episode_id} approved[/green]")

        if auto_resume:
            pipeline = create_pipeline()
            with console.status("[bold cyan]Resuming pipeline…[/bold cyan]"):
                episode = _run_async(
                    pipeline.resume_episode(show_id, episode_id)
                )
            console.print(
                f"[bold green]✓ Episode complete![/bold green]  "
                f"Stage: {_format_stage(episode.current_stage)}"
            )
            if episode.audio_path:
                console.print(f"  Audio: [cyan]{episode.audio_path}[/cyan]")
        else:
            console.print(
                f"\n[dim]Resume with:[/dim]  "
                f"[cyan]kids-podcast episodes resume {show_id} {episode_id}[/cyan]"
            )

    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error approving episode: {e}[/red]")
        logger.exception("Approval failed")
        raise typer.Exit(1)


@episodes_app.command("reject")
def reject_episode(
    show_id: str = typer.Argument(..., help="Show identifier"),
    episode_id: str = typer.Argument(..., help="Episode identifier"),
    feedback: str | None = typer.Option(None, "--feedback", "-f", help="Feedback text"),
):
    """Reject an episode outline."""
    try:
        workflow = create_approval_workflow()
        episode = workflow.submit_approval(
            show_id=show_id,
            episode_id=episode_id,
            approved=False,
            feedback=feedback,
        )
        console.print(f"[yellow]✗ Episode {episode_id} rejected[/yellow]")
        console.print(
            f"\n[dim]Retry with:[/dim]  "
            f"[cyan]kids-podcast episodes retry {show_id} {episode_id}[/cyan]"
        )

    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error rejecting episode: {e}[/red]")
        raise typer.Exit(1)


@episodes_app.command("resume")
def resume_episode(
    show_id: str = typer.Argument(..., help="Show identifier"),
    episode_id: str = typer.Argument(..., help="Episode identifier"),
):
    """Resume an approved episode through remaining pipeline stages."""
    try:
        pipeline = create_pipeline()

        with console.status("[bold cyan]Running pipeline…[/bold cyan]"):
            episode = _run_async(
                pipeline.resume_episode(show_id, episode_id)
            )

        console.print(
            f"[bold green]✓ Episode complete![/bold green]  "
            f"Stage: {_format_stage(episode.current_stage)}"
        )
        if episode.audio_path:
            console.print(f"  Audio: [cyan]{episode.audio_path}[/cyan]")
        console.print(f"  Total cost: ${episode.total_cost:.4f}")

    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error resuming episode: {e}[/red]")
        logger.exception("Resume failed")
        raise typer.Exit(1)


@episodes_app.command("retry")
def retry_episode(
    show_id: str = typer.Argument(..., help="Show identifier"),
    episode_id: str = typer.Argument(..., help="Episode identifier"),
):
    """Retry a failed or rejected episode from the beginning.

    FAILED episodes are reset to PENDING and re-run through all stages.
    REJECTED episodes are re-run from IDEATION with fresh content.
    """
    try:
        storage = create_storage()
        episode = storage.load_episode(show_id, episode_id)
        pipeline = create_pipeline()

        with console.status("[bold blue]Retrying episode…[/bold blue]"):
            if episode.current_stage == PipelineStage.FAILED:
                result = _run_async(
                    pipeline.retry_failed_episode(show_id, episode_id)
                )
            elif episode.current_stage == PipelineStage.REJECTED:
                result = _run_async(
                    pipeline.retry_rejected_episode(show_id, episode_id)
                )
            else:
                console.print(
                    f"[red]Episode is in stage '{episode.current_stage.value}' "
                    f"— only FAILED or REJECTED episodes can be retried[/red]"
                )
                raise typer.Exit(1)

        ep = result.episode
        console.print(
            f"[green]✓ Episode retried[/green]  "
            f"Stage: {_format_stage(ep.current_stage)}"
        )
        console.print(
            f"\n[dim]Next:[/dim]  "
            f"[cyan]kids-podcast episodes approve {show_id} {ep.episode_id}[/cyan]"
        )

    except FileNotFoundError:
        console.print(
            f"[red]Episode '{episode_id}' not found in show '{show_id}'[/red]"
        )
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error retrying episode: {e}[/red]")
        logger.exception("Retry failed")
        raise typer.Exit(1)


@episodes_app.command("reset")
def reset_episode(
    show_id: str = typer.Argument(..., help="Show identifier"),
    episode_id: str = typer.Argument(..., help="Episode identifier"),
    stage: str = typer.Argument(
        ..., help="Target stage (ideation, outlining, segment_generation, …)"
    ),
    confirm: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
):
    """Reset an episode to a previous stage for manual recovery."""
    if not confirm:
        typer.confirm(
            f"Reset episode '{episode_id}' to stage '{stage}'?", abort=True
        )

    try:
        pipeline = create_pipeline()
        episode = _run_async(
            pipeline.reset_to_stage(show_id, episode_id, stage)
        )

        console.print(
            f"[green]✓ Episode reset to {_format_stage(episode.current_stage)}[/green]"
        )

    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error resetting episode: {e}[/red]")
        raise typer.Exit(1)


@episodes_app.command("pending")
def pending_approvals(
    show_id: str = typer.Argument(..., help="Show identifier"),
):
    """List episodes awaiting approval for a show."""
    try:
        workflow = create_approval_workflow()
        pending = workflow.list_pending_approvals(show_id)

        if not pending:
            console.print(
                f"[green]No episodes awaiting approval for '{show_id}'[/green]"
            )
            return

        table = Table(title=f"Pending Approvals — {show_id}")
        table.add_column("Episode ID", style="cyan")
        table.add_column("Topic", style="white")
        table.add_column("Updated", style="dim")

        for ep in pending:
            table.add_row(
                ep.episode_id,
                ep.topic[:40],
                ep.updated_at.strftime("%Y-%m-%d %H:%M"),
            )
        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

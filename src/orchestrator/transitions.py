"""Pipeline state transitions — single source of truth.

Extracted from ``pipeline.py`` so that both ``PipelineOrchestrator`` and
``ApprovalWorkflow`` can reference valid transitions without circular imports.
"""

from models.episode import PipelineStage

# Valid state transitions map
VALID_TRANSITIONS: dict[PipelineStage, set[PipelineStage]] = {
    PipelineStage.PENDING: {PipelineStage.IDEATION},
    PipelineStage.IDEATION: {PipelineStage.OUTLINING, PipelineStage.FAILED},
    PipelineStage.OUTLINING: {PipelineStage.AWAITING_APPROVAL, PipelineStage.FAILED},
    PipelineStage.AWAITING_APPROVAL: {
        PipelineStage.APPROVED,
        PipelineStage.REJECTED,
        PipelineStage.FAILED,
    },
    PipelineStage.APPROVED: {
        PipelineStage.SEGMENT_GENERATION,
        PipelineStage.FAILED,
    },
    PipelineStage.SEGMENT_GENERATION: {
        PipelineStage.SCRIPT_GENERATION,
        PipelineStage.FAILED,
    },
    PipelineStage.SCRIPT_GENERATION: {
        PipelineStage.AUDIO_SYNTHESIS,
        PipelineStage.FAILED,
    },
    PipelineStage.AUDIO_SYNTHESIS: {
        PipelineStage.AUDIO_MIXING,
        PipelineStage.FAILED,
    },
    PipelineStage.AUDIO_MIXING: {PipelineStage.COMPLETE, PipelineStage.FAILED},
    PipelineStage.REJECTED: {PipelineStage.IDEATION},
    PipelineStage.COMPLETE: set(),
    PipelineStage.FAILED: {PipelineStage.PENDING},
}


def can_transition_to(
    current: PipelineStage,
    target: PipelineStage,
) -> bool:
    """Check whether a state transition is valid.

    Args:
        current: Current pipeline stage.
        target: Desired target stage.

    Returns:
        True if the transition is allowed.
    """
    return target in VALID_TRANSITIONS.get(current, set())

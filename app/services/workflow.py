from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import TransitionLog, WorkflowDefinition, WorkflowInstance


class WorkflowError(Exception):
    pass


def get_available_transitions(definition: WorkflowDefinition, current_state: str) -> list[dict]:
    """Return transitions available from the current state."""
    transitions = definition.transitions
    if isinstance(transitions, list):
        return [t for t in transitions if t.get("from") == current_state]
    return []


async def transition_instance(
    db: AsyncSession,
    instance: WorkflowInstance,
    definition: WorkflowDefinition,
    to_state: str,
    triggered_by: int | None = None,
    note: str = "",
) -> WorkflowInstance:
    """Execute a state transition on a workflow instance."""
    available = get_available_transitions(definition, instance.current_state)
    valid_targets = [t.get("to") for t in available]

    if to_state not in valid_targets:
        raise WorkflowError(
            f"Cannot transition from '{instance.current_state}' to '{to_state}'. "
            f"Valid targets: {', '.join(valid_targets)}"
        )

    from_state = instance.current_state
    instance.current_state = to_state

    log = TransitionLog(
        workflow_instance_id=instance.id,
        from_state=from_state,
        to_state=to_state,
        triggered_by=triggered_by,
        note=note,
    )
    db.add(log)
    await db.commit()
    await db.refresh(instance)

    return instance

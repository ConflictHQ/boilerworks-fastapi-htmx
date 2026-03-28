import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import WorkflowDefinition, WorkflowInstance
from app.services.workflow import WorkflowError, get_available_transitions, transition_instance


@pytest.mark.asyncio
async def test_workflows_list_requires_auth(client: AsyncClient):
    resp = await client.get("/workflows")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_workflow(client: AsyncClient, admin_session_token: str, db: AsyncSession):
    import json

    resp = await client.post(
        "/workflows",
        data={
            "name": "Approval",
            "description": "Approval workflow",
            "states": json.dumps(["draft", "review", "approved"]),
            "transitions": json.dumps([{"from": "draft", "to": "review"}, {"from": "review", "to": "approved"}]),
            "csrf_token": "",
        },
        cookies={"session_token": admin_session_token},
        follow_redirects=False,
    )
    assert resp.status_code == 302

    result = await db.execute(select(WorkflowDefinition).where(WorkflowDefinition.name == "Approval"))
    wf = result.scalar_one_or_none()
    assert wf is not None
    assert isinstance(wf.id, uuid.UUID)
    assert len(wf.states) == 3


@pytest.mark.asyncio
async def test_workflow_transition_service(db: AsyncSession):
    wf = WorkflowDefinition(
        name="Test WF",
        description="",
        states=["open", "closed"],
        transitions=[{"from": "open", "to": "closed"}],
    )
    db.add(wf)
    await db.flush()

    instance = WorkflowInstance(workflow_definition_id=wf.id, current_state="open", data={}, created_by=None)
    db.add(instance)
    await db.commit()
    await db.refresh(instance)

    # Valid transition
    result = await transition_instance(db, instance, wf, "closed")
    assert result.current_state == "closed"


@pytest.mark.asyncio
async def test_workflow_invalid_transition(db: AsyncSession):
    wf = WorkflowDefinition(
        name="Test WF 2",
        description="",
        states=["open", "closed"],
        transitions=[{"from": "open", "to": "closed"}],
    )
    db.add(wf)
    await db.flush()

    instance = WorkflowInstance(workflow_definition_id=wf.id, current_state="closed", data={}, created_by=None)
    db.add(instance)
    await db.commit()
    await db.refresh(instance)

    with pytest.raises(WorkflowError):
        await transition_instance(db, instance, wf, "open")


@pytest.mark.asyncio
async def test_get_available_transitions():
    wf = WorkflowDefinition(
        name="t",
        description="",
        states=["a", "b", "c"],
        transitions=[{"from": "a", "to": "b"}, {"from": "b", "to": "c"}],
    )
    available = get_available_transitions(wf, "a")
    assert len(available) == 1
    assert available[0]["to"] == "b"

    available = get_available_transitions(wf, "c")
    assert len(available) == 0

import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.dependencies import require_permission
from app.models.user import User
from app.models.workflow import WorkflowDefinition, WorkflowInstance
from app.services.workflow import WorkflowError, transition_instance

router = APIRouter(prefix="/workflows", tags=["workflows"])


def _templates(request: Request):
    return request.app.state.templates


@router.get("", response_class=HTMLResponse)
async def list_workflows(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("workflows.view")),
):
    workflows = (
        (
            await db.execute(
                select(WorkflowDefinition)
                .where(WorkflowDefinition.deleted_at.is_(None))
                .order_by(WorkflowDefinition.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return _templates(request).TemplateResponse(
        request, "pages/workflows/index.html", context={"user": user, "workflows": workflows}
    )


@router.get("/create", response_class=HTMLResponse)
async def create_workflow_page(
    request: Request,
    user: User = Depends(require_permission("workflows.create")),
):
    return _templates(request).TemplateResponse(request, "pages/workflows/create.html", context={"user": user})


@router.post("", response_class=HTMLResponse)
async def create_workflow(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("workflows.create")),
):
    form_data = await request.form()
    try:
        states = json.loads(form_data.get("states", "[]"))
    except json.JSONDecodeError:
        states = []
    try:
        transitions = json.loads(form_data.get("transitions", "[]"))
    except json.JSONDecodeError:
        transitions = []

    wf = WorkflowDefinition(
        name=form_data.get("name", ""),
        description=form_data.get("description", ""),
        states=states,
        transitions=transitions,
    )
    db.add(wf)
    await db.commit()
    return RedirectResponse("/workflows", status_code=302)


@router.get("/{workflow_id}", response_class=HTMLResponse)
async def show_workflow(
    request: Request,
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("workflows.view")),
):
    wf = (
        await db.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.id == workflow_id, WorkflowDefinition.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if not wf:
        return HTMLResponse("Not found", status_code=404)
    return _templates(request).TemplateResponse(
        request, "pages/workflows/show.html", context={"user": user, "workflow": wf}
    )


@router.get("/{workflow_id}/edit", response_class=HTMLResponse)
async def edit_workflow_page(
    request: Request,
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("workflows.edit")),
):
    wf = (
        await db.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.id == workflow_id, WorkflowDefinition.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if not wf:
        return HTMLResponse("Not found", status_code=404)
    return _templates(request).TemplateResponse(
        request, "pages/workflows/edit.html", context={"user": user, "workflow": wf}
    )


@router.post("/{workflow_id}", response_class=HTMLResponse)
async def update_workflow(
    request: Request,
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("workflows.edit")),
):
    wf = (
        await db.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.id == workflow_id, WorkflowDefinition.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if not wf:
        return HTMLResponse("Not found", status_code=404)

    form_data = await request.form()
    wf.name = form_data.get("name", wf.name)
    wf.description = form_data.get("description", wf.description)
    try:
        wf.states = json.loads(form_data.get("states", "[]"))
    except json.JSONDecodeError:
        pass
    try:
        wf.transitions = json.loads(form_data.get("transitions", "[]"))
    except json.JSONDecodeError:
        pass
    await db.commit()
    return RedirectResponse("/workflows", status_code=302)


@router.get("/{workflow_id}/instances", response_class=HTMLResponse)
async def list_instances(
    request: Request,
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("workflows.view")),
):
    wf = (
        await db.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.id == workflow_id, WorkflowDefinition.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if not wf:
        return HTMLResponse("Not found", status_code=404)

    instances = (
        (
            await db.execute(
                select(WorkflowInstance)
                .where(
                    WorkflowInstance.workflow_definition_id == workflow_id,
                    WorkflowInstance.deleted_at.is_(None),
                )
                .order_by(WorkflowInstance.created_at.desc())
            )
        )
        .scalars()
        .all()
    )

    return _templates(request).TemplateResponse(
        request,
        "pages/workflows/instances.html",
        context={"user": user, "workflow": wf, "instances": instances},
    )


@router.post("/{workflow_id}/instances", response_class=HTMLResponse)
async def create_instance(
    request: Request,
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("workflows.create")),
):
    wf = (
        await db.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.id == workflow_id, WorkflowDefinition.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if not wf:
        return HTMLResponse("Not found", status_code=404)

    states = wf.states if isinstance(wf.states, list) else []
    initial_state = states[0] if states else "draft"

    instance = WorkflowInstance(
        workflow_definition_id=workflow_id,
        current_state=initial_state,
        data={},
        created_by=user.id,
    )
    db.add(instance)
    await db.commit()
    return RedirectResponse(f"/workflows/{workflow_id}/instances", status_code=302)


@router.post("/{workflow_id}/instances/{instance_id}/transition", response_class=HTMLResponse)
async def do_transition(
    request: Request,
    workflow_id: uuid.UUID,
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("workflows.edit")),
):
    wf = (
        await db.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.id == workflow_id, WorkflowDefinition.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    instance = (
        await db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == instance_id, WorkflowInstance.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if not wf or not instance:
        return HTMLResponse("Not found", status_code=404)

    form_data = await request.form()
    to_state = form_data.get("to_state", "")

    try:
        await transition_instance(db, instance, wf, to_state, triggered_by=user.id)
    except WorkflowError as e:
        return HTMLResponse(str(e), status_code=400)

    return RedirectResponse(f"/workflows/{workflow_id}/instances", status_code=302)


@router.delete("/{workflow_id}", response_class=HTMLResponse)
async def delete_workflow(
    request: Request,
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("workflows.delete")),
):
    wf = (
        await db.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.id == workflow_id, WorkflowDefinition.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if not wf:
        return HTMLResponse("Not found", status_code=404)
    wf.deleted_at = datetime.now(UTC)
    await db.commit()
    if request.headers.get("HX-Request"):
        return HTMLResponse("", status_code=200)
    return RedirectResponse("/workflows", status_code=302)

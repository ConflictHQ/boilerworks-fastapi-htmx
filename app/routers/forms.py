import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.dependencies import require_permission
from app.models.form import FormDefinition, FormSubmission
from app.models.user import User
from app.services.forms import validate_submission

router = APIRouter(prefix="/forms", tags=["forms"])


def _templates(request: Request):
    return request.app.state.templates


@router.get("", response_class=HTMLResponse)
async def list_forms(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("forms.view")),
):
    forms = (
        (
            await db.execute(
                select(FormDefinition)
                .where(FormDefinition.deleted_at.is_(None))
                .order_by(FormDefinition.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return _templates(request).TemplateResponse(
        request, "pages/forms/index.html", context={"user": user, "forms": forms}
    )


@router.get("/create", response_class=HTMLResponse)
async def create_form_page(
    request: Request,
    user: User = Depends(require_permission("forms.create")),
):
    return _templates(request).TemplateResponse(request, "pages/forms/create.html", context={"user": user})


@router.post("", response_class=HTMLResponse)
async def create_form(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("forms.create")),
):
    form_data = await request.form()
    schema_str = form_data.get("schema", "{}")
    try:
        schema = json.loads(schema_str)
    except json.JSONDecodeError:
        schema = {"fields": []}

    form_def = FormDefinition(
        name=form_data.get("name", ""),
        description=form_data.get("description", ""),
        schema=schema,
    )
    db.add(form_def)
    await db.commit()
    return RedirectResponse("/forms", status_code=302)


@router.get("/{form_id}", response_class=HTMLResponse)
async def show_form(
    request: Request,
    form_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("forms.view")),
):
    form_def = (
        await db.execute(
            select(FormDefinition).where(FormDefinition.id == form_id, FormDefinition.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if not form_def:
        return HTMLResponse("Not found", status_code=404)

    submissions = (
        (
            await db.execute(
                select(FormSubmission)
                .where(FormSubmission.form_definition_id == form_id, FormSubmission.deleted_at.is_(None))
                .order_by(FormSubmission.created_at.desc())
            )
        )
        .scalars()
        .all()
    )

    return _templates(request).TemplateResponse(
        request,
        "pages/forms/show.html",
        context={"user": user, "form_def": form_def, "submissions": submissions},
    )


@router.get("/{form_id}/edit", response_class=HTMLResponse)
async def edit_form_page(
    request: Request,
    form_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("forms.edit")),
):
    form_def = (
        await db.execute(
            select(FormDefinition).where(FormDefinition.id == form_id, FormDefinition.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if not form_def:
        return HTMLResponse("Not found", status_code=404)
    return _templates(request).TemplateResponse(
        request, "pages/forms/edit.html", context={"user": user, "form_def": form_def}
    )


@router.post("/{form_id}", response_class=HTMLResponse)
async def update_form(
    request: Request,
    form_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("forms.edit")),
):
    form_def = (
        await db.execute(
            select(FormDefinition).where(FormDefinition.id == form_id, FormDefinition.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if not form_def:
        return HTMLResponse("Not found", status_code=404)

    form_data = await request.form()
    form_def.name = form_data.get("name", form_def.name)
    form_def.description = form_data.get("description", form_def.description)
    schema_str = form_data.get("schema", "")
    if schema_str:
        try:
            form_def.schema = json.loads(schema_str)
        except json.JSONDecodeError:
            pass
    await db.commit()
    return RedirectResponse("/forms", status_code=302)


@router.get("/{form_id}/submit", response_class=HTMLResponse)
async def submit_form_page(
    request: Request,
    form_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("forms.submit")),
):
    form_def = (
        await db.execute(
            select(FormDefinition).where(FormDefinition.id == form_id, FormDefinition.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if not form_def:
        return HTMLResponse("Not found", status_code=404)
    return _templates(request).TemplateResponse(
        request, "pages/forms/submit.html", context={"user": user, "form_def": form_def}
    )


@router.post("/{form_id}/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    form_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("forms.submit")),
):
    form_def = (
        await db.execute(
            select(FormDefinition).where(FormDefinition.id == form_id, FormDefinition.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if not form_def:
        return HTMLResponse("Not found", status_code=404)

    form_data = await request.form()
    data = {key: value for key, value in form_data.items() if key != "csrf_token"}

    errors = validate_submission(form_def.schema, data)
    if errors:
        return _templates(request).TemplateResponse(
            request,
            "pages/forms/submit.html",
            context={"user": user, "form_def": form_def, "errors": errors, "data": data},
            status_code=400,
        )

    submission = FormSubmission(
        form_definition_id=form_id,
        submitted_by=user.id,
        data=data,
    )
    db.add(submission)
    await db.commit()
    return RedirectResponse(f"/forms/{form_id}", status_code=302)


@router.delete("/{form_id}", response_class=HTMLResponse)
async def delete_form(
    request: Request,
    form_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("forms.delete")),
):
    form_def = (
        await db.execute(
            select(FormDefinition).where(FormDefinition.id == form_id, FormDefinition.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if not form_def:
        return HTMLResponse("Not found", status_code=404)
    form_def.deleted_at = datetime.now(UTC)
    await db.commit()
    if request.headers.get("HX-Request"):
        return HTMLResponse("", status_code=200)
    return RedirectResponse("/forms", status_code=302)

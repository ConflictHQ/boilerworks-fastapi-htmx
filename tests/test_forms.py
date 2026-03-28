import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.form import FormDefinition


@pytest.mark.asyncio
async def test_forms_list_requires_auth(client: AsyncClient):
    resp = await client.get("/forms")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_form(client: AsyncClient, admin_session_token: str, db: AsyncSession):
    import json

    schema = json.dumps({"fields": [{"name": "email", "type": "email", "label": "Email", "required": True}]})
    resp = await client.post(
        "/forms",
        data={"name": "Contact Form", "description": "Contact us", "schema": schema, "csrf_token": ""},
        cookies={"session_token": admin_session_token},
        follow_redirects=False,
    )
    assert resp.status_code == 302

    result = await db.execute(select(FormDefinition).where(FormDefinition.name == "Contact Form"))
    form_def = result.scalar_one_or_none()
    assert form_def is not None
    assert isinstance(form_def.id, uuid.UUID)
    assert form_def.schema["fields"][0]["type"] == "email"


@pytest.mark.asyncio
async def test_submit_form(client: AsyncClient, admin_session_token: str, db: AsyncSession):
    form_def = FormDefinition(
        name="Test Form",
        description="",
        schema={"fields": [{"name": "name", "type": "text", "label": "Name", "required": True}]},
    )
    db.add(form_def)
    await db.commit()
    await db.refresh(form_def)

    resp = await client.post(
        f"/forms/{form_def.id}/submit",
        data={"name": "John", "csrf_token": ""},
        cookies={"session_token": admin_session_token},
        follow_redirects=False,
    )
    assert resp.status_code == 302


@pytest.mark.asyncio
async def test_submit_form_validation(client: AsyncClient, admin_session_token: str, db: AsyncSession):
    form_def = FormDefinition(
        name="Required Form",
        description="",
        schema={"fields": [{"name": "email", "type": "email", "label": "Email", "required": True}]},
    )
    db.add(form_def)
    await db.commit()
    await db.refresh(form_def)

    # Submit without required field
    resp = await client.post(
        f"/forms/{form_def.id}/submit",
        data={"csrf_token": ""},
        cookies={"session_token": admin_session_token},
    )
    assert resp.status_code == 400
    assert "required" in resp.text.lower()

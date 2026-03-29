import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Category


@pytest.mark.asyncio
async def test_categories_list_requires_permission(client: AsyncClient):
    resp = await client.get("/categories")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_categories_list_with_admin(client: AsyncClient, admin_session_token: str):
    resp = await client.get("/categories", cookies={"session_token": admin_session_token})
    assert resp.status_code == 200
    assert "Categories" in resp.text


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient, admin_session_token: str, db: AsyncSession):
    resp = await client.post(
        "/categories",
        data={"name": "Electronics", "description": "Electronic goods", "csrf_token": ""},
        cookies={"session_token": admin_session_token},
        follow_redirects=False,
    )
    assert resp.status_code == 302

    result = await db.execute(select(Category).where(Category.name == "Electronics"))
    category = result.scalar_one_or_none()
    assert category is not None
    assert isinstance(category.id, uuid.UUID)
    assert category.description == "Electronic goods"


@pytest.mark.asyncio
async def test_get_category(client: AsyncClient, admin_session_token: str, db: AsyncSession):
    category = Category(name="Books", description="Paper and digital books")
    db.add(category)
    await db.commit()
    await db.refresh(category)

    resp = await client.get(
        f"/categories/{category.id}",
        cookies={"session_token": admin_session_token},
    )
    assert resp.status_code == 200
    assert "Books" in resp.text


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient, admin_session_token: str, db: AsyncSession):
    category = Category(name="Old Name", description="Old desc")
    db.add(category)
    await db.commit()
    await db.refresh(category)

    cat_id = category.id

    resp = await client.post(
        f"/categories/{cat_id}",
        data={"name": "New Name", "description": "New desc", "csrf_token": ""},
        cookies={"session_token": admin_session_token},
        follow_redirects=False,
    )
    assert resp.status_code == 302

    db.expire_all()
    result = await db.execute(select(Category).where(Category.id == cat_id))
    updated = result.scalar_one()
    assert updated.name == "New Name"
    assert updated.description == "New desc"


@pytest.mark.asyncio
async def test_delete_category_soft_deletes(client: AsyncClient, admin_session_token: str, db: AsyncSession):
    category = Category(name="Temp", description="Will be deleted")
    db.add(category)
    await db.commit()
    await db.refresh(category)
    cat_id = category.id

    resp = await client.delete(
        f"/categories/{cat_id}",
        cookies={"session_token": admin_session_token},
    )
    assert resp.status_code in (200, 302)

    # Record still exists in DB with deleted_at set
    db.expire_all()
    result = await db.execute(select(Category).where(Category.id == cat_id))
    deleted = result.scalar_one_or_none()
    assert deleted is not None
    assert deleted.deleted_at is not None

    # Does not show in list
    resp = await client.get("/categories", cookies={"session_token": admin_session_token})
    assert "Temp" not in resp.text


@pytest.mark.asyncio
async def test_viewer_cannot_create_category(client: AsyncClient, viewer_session_token: str):
    resp = await client.post(
        "/categories",
        data={"name": "Blocked", "description": "", "csrf_token": ""},
        cookies={"session_token": viewer_session_token},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_viewer_cannot_edit_category(client: AsyncClient, viewer_session_token: str, db: AsyncSession):
    category = Category(name="Locked", description="")
    db.add(category)
    await db.commit()
    await db.refresh(category)

    resp = await client.post(
        f"/categories/{category.id}",
        data={"name": "Hacked", "description": "", "csrf_token": ""},
        cookies={"session_token": viewer_session_token},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_viewer_cannot_delete_category(client: AsyncClient, viewer_session_token: str, db: AsyncSession):
    category = Category(name="Protected", description="")
    db.add(category)
    await db.commit()
    await db.refresh(category)

    resp = await client.delete(
        f"/categories/{category.id}",
        cookies={"session_token": viewer_session_token},
    )
    assert resp.status_code == 403

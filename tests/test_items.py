import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item


@pytest.mark.asyncio
async def test_items_list_requires_permission(client: AsyncClient):
    resp = await client.get("/items")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_items_list_with_admin(client: AsyncClient, admin_session_token: str):
    resp = await client.get("/items", cookies={"session_token": admin_session_token})
    assert resp.status_code == 200
    assert "Items" in resp.text


@pytest.mark.asyncio
async def test_create_item(client: AsyncClient, admin_session_token: str, db: AsyncSession):
    resp = await client.post(
        "/items",
        data={
            "name": "Widget",
            "sku": "WDG-001",
            "price": "9.99",
            "description": "A widget",
            "csrf_token": "",
        },
        cookies={"session_token": admin_session_token},
        follow_redirects=False,
    )
    assert resp.status_code == 302

    result = await db.execute(select(Item).where(Item.sku == "WDG-001"))
    item = result.scalar_one_or_none()
    assert item is not None
    assert item.name == "Widget"
    assert isinstance(item.id, uuid.UUID)


@pytest.mark.asyncio
async def test_viewer_cannot_create_item(client: AsyncClient, viewer_session_token: str):
    resp = await client.post(
        "/items",
        data={"name": "Widget", "sku": "WDG-002", "price": "9.99", "description": "", "csrf_token": ""},
        cookies={"session_token": viewer_session_token},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_item_soft_deletes(client: AsyncClient, admin_session_token: str, db: AsyncSession):
    item = Item(name="Delete Me", sku="DEL-001", price=1.00, description="")
    db.add(item)
    await db.commit()
    await db.refresh(item)
    prod_id = item.id

    resp = await client.delete(
        f"/items/{prod_id}",
        cookies={"session_token": admin_session_token},
    )
    assert resp.status_code in (200, 302)

    # Verify soft delete -- record still in DB with deleted_at set
    db.expire_all()
    result = await db.execute(select(Item).where(Item.id == prod_id))
    deleted = result.scalar_one_or_none()
    assert deleted is not None
    assert deleted.deleted_at is not None

    # Verify it does not appear in the list endpoint
    resp = await client.get("/items", cookies={"session_token": admin_session_token})
    assert resp.status_code == 200
    assert "Delete Me" not in resp.text

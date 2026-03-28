import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


@pytest.mark.asyncio
async def test_products_list_requires_permission(client: AsyncClient):
    resp = await client.get("/products")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_products_list_with_admin(client: AsyncClient, admin_session_token: str):
    resp = await client.get("/products", cookies={"session_token": admin_session_token})
    assert resp.status_code == 200
    assert "Products" in resp.text


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, admin_session_token: str, db: AsyncSession):
    resp = await client.post(
        "/products",
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

    # Verify in DB
    from sqlalchemy import select

    result = await db.execute(select(Product).where(Product.sku == "WDG-001"))
    product = result.scalar_one_or_none()
    assert product is not None
    assert product.name == "Widget"


@pytest.mark.asyncio
async def test_viewer_cannot_create_product(client: AsyncClient, viewer_session_token: str):
    resp = await client.post(
        "/products",
        data={"name": "Widget", "sku": "WDG-002", "price": "9.99", "description": "", "csrf_token": ""},
        cookies={"session_token": viewer_session_token},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_product(client: AsyncClient, admin_session_token: str, db: AsyncSession):
    product = Product(name="Delete Me", sku="DEL-001", price=1.00, description="")
    db.add(product)
    await db.commit()
    await db.refresh(product)

    resp = await client.delete(
        f"/products/{product.id}",
        cookies={"session_token": admin_session_token},
    )
    assert resp.status_code in (200, 302)

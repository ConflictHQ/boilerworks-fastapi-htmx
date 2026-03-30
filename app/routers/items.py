import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_async_session
from app.dependencies import require_permission
from app.models.item import Category, Item
from app.models.user import User

router = APIRouter(prefix="/items", tags=["items"])


def _templates(request: Request):
    return request.app.state.templates


@router.get("", response_class=HTMLResponse)
async def list_items(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("items.view")),
):
    result = await db.execute(
        select(Item)
        .where(Item.deleted_at.is_(None))
        .options(selectinload(Item.category))
        .order_by(Item.created_at.desc())
    )
    items = result.scalars().all()

    ctx = {"user": user, "items": items}
    if request.headers.get("HX-Request"):
        return _templates(request).TemplateResponse(request, "pages/items/_list.html", context=ctx)
    return _templates(request).TemplateResponse(request, "pages/items/index.html", context=ctx)


@router.get("/create", response_class=HTMLResponse)
async def create_item_page(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("items.create")),
):
    categories = (
        (await db.execute(select(Category).where(Category.deleted_at.is_(None)).order_by(Category.name)))
        .scalars()
        .all()
    )
    return _templates(request).TemplateResponse(
        request, "pages/items/create.html", context={"user": user, "categories": categories}
    )


@router.post("", response_class=HTMLResponse)
async def create_item(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("items.create")),
):
    form = await request.form()
    category_id = form.get("category_id")
    item = Item(
        name=form.get("name", ""),
        description=form.get("description", ""),
        price=float(form.get("price", 0)),
        sku=form.get("sku", ""),
        category_id=uuid.UUID(category_id) if category_id else None,
    )
    db.add(item)
    await db.commit()
    return RedirectResponse("/items", status_code=302)


@router.get("/{item_id}", response_class=HTMLResponse)
async def show_item(
    request: Request,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("items.view")),
):
    result = await db.execute(
        select(Item).where(Item.id == item_id, Item.deleted_at.is_(None)).options(selectinload(Item.category))
    )
    item = result.scalar_one_or_none()
    if not item:
        return HTMLResponse("Not found", status_code=404)
    return _templates(request).TemplateResponse(request, "pages/items/show.html", context={"user": user, "item": item})


@router.get("/{item_id}/edit", response_class=HTMLResponse)
async def edit_item_page(
    request: Request,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("items.edit")),
):
    item = (await db.execute(select(Item).where(Item.id == item_id, Item.deleted_at.is_(None)))).scalar_one_or_none()
    if not item:
        return HTMLResponse("Not found", status_code=404)
    categories = (
        (await db.execute(select(Category).where(Category.deleted_at.is_(None)).order_by(Category.name)))
        .scalars()
        .all()
    )
    return _templates(request).TemplateResponse(
        request,
        "pages/items/edit.html",
        context={"user": user, "item": item, "categories": categories},
    )


@router.post("/{item_id}", response_class=HTMLResponse)
async def update_item(
    request: Request,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("items.edit")),
):
    item = (await db.execute(select(Item).where(Item.id == item_id, Item.deleted_at.is_(None)))).scalar_one_or_none()
    if not item:
        return HTMLResponse("Not found", status_code=404)

    form = await request.form()
    item.name = form.get("name", item.name)
    item.description = form.get("description", item.description)
    item.price = float(form.get("price", item.price))
    item.sku = form.get("sku", item.sku)
    category_id = form.get("category_id")
    item.category_id = uuid.UUID(category_id) if category_id else None
    await db.commit()
    return RedirectResponse("/items", status_code=302)


@router.delete("/{item_id}", response_class=HTMLResponse)
async def delete_item(
    request: Request,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("items.delete")),
):
    item = (await db.execute(select(Item).where(Item.id == item_id, Item.deleted_at.is_(None)))).scalar_one_or_none()
    if not item:
        return HTMLResponse("Not found", status_code=404)
    item.deleted_at = datetime.now(UTC)
    await db.commit()
    if request.headers.get("HX-Request"):
        return HTMLResponse("", status_code=200, headers={"HX-Trigger": "itemDeleted"})
    return RedirectResponse("/items", status_code=302)

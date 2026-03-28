from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.dependencies import require_permission
from app.models.product import Category
from app.models.user import User

router = APIRouter(prefix="/categories", tags=["categories"])


def _templates(request: Request):
    return request.app.state.templates


@router.get("", response_class=HTMLResponse)
async def list_categories(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("categories.view")),
):
    categories = (await db.execute(select(Category).order_by(Category.id.desc()))).scalars().all()
    return _templates(request).TemplateResponse(
        request, "pages/categories/index.html", context={"user": user, "categories": categories}
    )


@router.get("/create", response_class=HTMLResponse)
async def create_category_page(
    request: Request,
    user: User = Depends(require_permission("categories.create")),
):
    return _templates(request).TemplateResponse(request, "pages/categories/create.html", context={"user": user})


@router.post("", response_class=HTMLResponse)
async def create_category(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("categories.create")),
):
    form = await request.form()
    category = Category(name=form.get("name", ""), description=form.get("description", ""))
    db.add(category)
    await db.commit()
    return RedirectResponse("/categories", status_code=302)


@router.get("/{category_id}", response_class=HTMLResponse)
async def show_category(
    request: Request,
    category_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("categories.view")),
):
    category = (await db.execute(select(Category).where(Category.id == category_id))).scalar_one_or_none()
    if not category:
        return HTMLResponse("Not found", status_code=404)
    return _templates(request).TemplateResponse(
        request, "pages/categories/show.html", context={"user": user, "category": category}
    )


@router.get("/{category_id}/edit", response_class=HTMLResponse)
async def edit_category_page(
    request: Request,
    category_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("categories.edit")),
):
    category = (await db.execute(select(Category).where(Category.id == category_id))).scalar_one_or_none()
    if not category:
        return HTMLResponse("Not found", status_code=404)
    return _templates(request).TemplateResponse(
        request, "pages/categories/edit.html", context={"user": user, "category": category}
    )


@router.post("/{category_id}", response_class=HTMLResponse)
async def update_category(
    request: Request,
    category_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("categories.edit")),
):
    category = (await db.execute(select(Category).where(Category.id == category_id))).scalar_one_or_none()
    if not category:
        return HTMLResponse("Not found", status_code=404)
    form = await request.form()
    category.name = form.get("name", category.name)
    category.description = form.get("description", category.description)
    await db.commit()
    return RedirectResponse("/categories", status_code=302)


@router.delete("/{category_id}", response_class=HTMLResponse)
async def delete_category(
    request: Request,
    category_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("categories.delete")),
):
    category = (await db.execute(select(Category).where(Category.id == category_id))).scalar_one_or_none()
    if not category:
        return HTMLResponse("Not found", status_code=404)
    await db.delete(category)
    await db.commit()
    if request.headers.get("HX-Request"):
        return HTMLResponse("", status_code=200)
    return RedirectResponse("/categories", status_code=302)

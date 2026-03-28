from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_async_session
from app.dependencies import require_permission
from app.models.product import Category, Product
from app.models.user import User

router = APIRouter(prefix="/products", tags=["products"])


def _templates(request: Request):
    return request.app.state.templates


@router.get("", response_class=HTMLResponse)
async def list_products(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("products.view")),
):
    result = await db.execute(select(Product).options(selectinload(Product.category)).order_by(Product.id.desc()))
    products = result.scalars().all()

    ctx = {"user": user, "products": products}
    if request.headers.get("HX-Request"):
        return _templates(request).TemplateResponse(request, "pages/products/_list.html", context=ctx)
    return _templates(request).TemplateResponse(request, "pages/products/index.html", context=ctx)


@router.get("/create", response_class=HTMLResponse)
async def create_product_page(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("products.create")),
):
    categories = (await db.execute(select(Category).order_by(Category.name))).scalars().all()
    return _templates(request).TemplateResponse(
        request, "pages/products/create.html", context={"user": user, "categories": categories}
    )


@router.post("", response_class=HTMLResponse)
async def create_product(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("products.create")),
):
    form = await request.form()
    category_id = form.get("category_id")
    product = Product(
        name=form.get("name", ""),
        description=form.get("description", ""),
        price=float(form.get("price", 0)),
        sku=form.get("sku", ""),
        category_id=int(category_id) if category_id else None,
    )
    db.add(product)
    await db.commit()
    return RedirectResponse("/products", status_code=302)


@router.get("/{product_id}", response_class=HTMLResponse)
async def show_product(
    request: Request,
    product_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("products.view")),
):
    result = await db.execute(select(Product).where(Product.id == product_id).options(selectinload(Product.category)))
    product = result.scalar_one_or_none()
    if not product:
        return HTMLResponse("Not found", status_code=404)
    return _templates(request).TemplateResponse(
        request, "pages/products/show.html", context={"user": user, "product": product}
    )


@router.get("/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_page(
    request: Request,
    product_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("products.edit")),
):
    product = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not product:
        return HTMLResponse("Not found", status_code=404)
    categories = (await db.execute(select(Category).order_by(Category.name))).scalars().all()
    return _templates(request).TemplateResponse(
        request,
        "pages/products/edit.html",
        context={"user": user, "product": product, "categories": categories},
    )


@router.post("/{product_id}", response_class=HTMLResponse)
async def update_product(
    request: Request,
    product_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("products.edit")),
):
    product = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not product:
        return HTMLResponse("Not found", status_code=404)

    form = await request.form()
    product.name = form.get("name", product.name)
    product.description = form.get("description", product.description)
    product.price = float(form.get("price", product.price))
    product.sku = form.get("sku", product.sku)
    category_id = form.get("category_id")
    product.category_id = int(category_id) if category_id else None
    await db.commit()
    return RedirectResponse("/products", status_code=302)


@router.delete("/{product_id}", response_class=HTMLResponse)
async def delete_product(
    request: Request,
    product_id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(require_permission("products.delete")),
):
    product = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not product:
        return HTMLResponse("Not found", status_code=404)
    await db.delete(product)
    await db.commit()
    if request.headers.get("HX-Request"):
        return HTMLResponse("", status_code=200, headers={"HX-Trigger": "productDeleted"})
    return RedirectResponse("/products", status_code=302)

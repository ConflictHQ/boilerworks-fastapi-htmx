from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.form import FormDefinition, FormSubmission
from app.models.product import Category, Product
from app.models.workflow import WorkflowInstance

router = APIRouter(tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    if getattr(request.state, "user", None):
        return RedirectResponse("/dashboard", status_code=302)
    return RedirectResponse("/login", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_async_session)):
    user = getattr(request.state, "user", None)
    if not user:
        return RedirectResponse("/login", status_code=302)

    products_count = (await db.execute(select(func.count(Product.id)))).scalar() or 0
    categories_count = (await db.execute(select(func.count(Category.id)))).scalar() or 0
    forms_count = (await db.execute(select(func.count(FormDefinition.id)))).scalar() or 0
    submissions_count = (await db.execute(select(func.count(FormSubmission.id)))).scalar() or 0
    workflows_count = (await db.execute(select(func.count(WorkflowInstance.id)))).scalar() or 0

    stats = {
        "products": products_count,
        "categories": categories_count,
        "forms": forms_count,
        "submissions": submissions_count,
        "workflows": workflows_count,
    }

    return request.app.state.templates.TemplateResponse(
        request,
        "pages/dashboard.html",
        context={"user": user, "stats": stats},
    )

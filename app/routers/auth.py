from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_async_session
from app.models.user import Group, User, UserGroup
from app.services.auth import create_session, delete_session, hash_password, verify_password

router = APIRouter(tags=["auth"])


def _templates(request: Request):
    return request.app.state.templates


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if getattr(request.state, "user", None):
        return RedirectResponse("/dashboard", status_code=302)
    return _templates(request).TemplateResponse(request, "pages/auth/login.html")


@router.post("/login")
async def login(request: Request, db: AsyncSession = Depends(get_async_session)):
    form = await request.form()
    email = form.get("email", "")
    password = form.get("password", "")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return _templates(request).TemplateResponse(
            request,
            "pages/auth/login.html",
            context={"error": "Invalid email or password"},
            status_code=400,
        )

    token = await create_session(db, user.id)
    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_max_age,
        httponly=True,
        samesite="strict",
    )
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    if getattr(request.state, "user", None):
        return RedirectResponse("/dashboard", status_code=302)
    return _templates(request).TemplateResponse(request, "pages/auth/register.html")


@router.post("/register")
async def register(request: Request, db: AsyncSession = Depends(get_async_session)):
    form = await request.form()
    email = form.get("email", "").strip()
    password = form.get("password", "").strip()
    display_name = form.get("display_name", "").strip()

    if not email or not password or not display_name:
        return _templates(request).TemplateResponse(
            request,
            "pages/auth/register.html",
            context={"error": "All fields are required"},
            status_code=400,
        )

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        return _templates(request).TemplateResponse(
            request,
            "pages/auth/register.html",
            context={"error": "Email already registered"},
            status_code=400,
        )

    user = User(email=email, password_hash=hash_password(password), display_name=display_name)
    db.add(user)
    await db.flush()

    # Assign to viewer group by default
    viewer_result = await db.execute(select(Group).where(Group.name == "viewer"))
    viewer = viewer_result.scalar_one_or_none()
    if viewer:
        db.add(UserGroup(user_id=user.id, group_id=viewer.id))

    await db.commit()

    token = await create_session(db, user.id)
    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_max_age,
        httponly=True,
        samesite="strict",
    )
    return response


@router.post("/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_async_session)):
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        await delete_session(db, token)
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie(settings.session_cookie_name)
    return response

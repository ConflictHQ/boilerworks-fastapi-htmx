import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.middleware.auth import SessionAuthMiddleware
from app.routers import auth, categories, dashboard, forms, health, products, workflows

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Boilerworks FastAPI + HTMX", lifespan=lifespan)

    # Static files and templates
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
    app.state.templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

    # Middleware (order matters: outermost first)
    app.add_middleware(SessionAuthMiddleware)

    # Routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(products.router)
    app.include_router(categories.router)
    app.include_router(forms.router)
    app.include_router(workflows.router)

    return app


app = create_app()

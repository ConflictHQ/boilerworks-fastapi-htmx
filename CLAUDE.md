# Claude -- Boilerworks FastAPI + HTMX

Primary conventions doc: [`bootstrap.md`](bootstrap.md)

Read it before writing any code.

## Stack

- **Backend**: FastAPI + Uvicorn (async)
- **Frontend**: HTMX + Jinja2 + Tailwind CSS (CDN)
- **ORM**: SQLAlchemy 2 (async) + asyncpg
- **Migrations**: Alembic
- **Auth**: Session-based (bcrypt + SHA-256 token hash + httpOnly cookie)
- **Tests**: pytest + httpx AsyncClient with aiosqlite

## Status

Complete. All tests passing (`.venv/bin/pytest -v`). Docker verified.

## Key Conventions

- Starlette 1.0 TemplateResponse API: `TemplateResponse(request, "name.html", context={...})`
- Dependencies for auth: `require_permission("resource.action")` as FastAPI Depends
- HTMX pattern: check `request.headers.get("HX-Request")` to return fragments vs full pages
- All DB operations use async SQLAlchemy sessions
- Tests use in-memory SQLite via StaticPool (no Postgres needed for test runs)

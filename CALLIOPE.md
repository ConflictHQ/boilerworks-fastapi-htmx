# Calliope — Boilerworks FastAPI + HTMX
<!-- Agent shim for https://github.com/calliopeai/calliope-cli -->

Primary conventions doc: [`bootstrap.md`](bootstrap.md)
Context seed: [`memory.md`](memory.md)

Read both before writing any code.

---

## Project-specific notes

- FastAPI + Uvicorn (async); HTMX + Jinja2 + Tailwind (CDN).
- SQLAlchemy 2 (async) + asyncpg; Alembic migrations; session auth (bcrypt + SHA-256 token hash + httpOnly cookie).
- Starlette 1.0 TemplateResponse API: `TemplateResponse(request, "name.html", context={...})`.
- Auth dependencies: `require_permission("resource.action")` as a FastAPI `Depends`.
- HTMX pattern keyed on `request.headers.get("HX-Request")` (fragments vs full pages); all DB operations use async SQLAlchemy sessions.
- Tests: pytest + httpx `AsyncClient` with in-memory SQLite via StaticPool (no Postgres needed). Run `.venv/bin/pytest -v`.

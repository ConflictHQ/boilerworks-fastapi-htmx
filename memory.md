# Boilerworks Memory

This file is the **AI context seed** for the Boilerworks FastAPI + HTMX template. It captures decisions, constraints, and non-obvious facts that are not derivable from reading a single file.

For conventions and patterns, see [`bootstrap.md`](bootstrap.md).

---

## Template purpose

Full-stack async Python starter: FastAPI backend, server-rendered Jinja2 + HTMX frontend, Tailwind CSS (CDN) dark theme. Ships with session auth, group-based RBAC, Items/Categories CRUD, a JSON-schema forms engine, and a JSON-defined workflow (state machine) engine.

## Key architectural decisions

| Decision | Why |
|---|---|
| HTMX fragments over a JS framework | Routers check the `HX-Request` header and return fragments for HTMX, full pages otherwise |
| Session auth, not JWT | bcrypt password hashing; session tokens stored SHA-256-hashed; httpOnly + `samesite=strict` cookie |
| Group-based RBAC | Users -> groups -> permissions; routes guard with `require_permission("resource.action")` as a FastAPI dependency |
| UUID primary keys everywhere | Never auto-incrementing integers; migrations use PostgreSQL-native UUID types |
| Soft deletes | Business models use `SoftDeleteMixin` (`deleted_at`) plus `TimestampMixin` |
| Starlette 1.0 TemplateResponse API | `TemplateResponse(request, "name.html", context={...})` -- request first |

## Things that bite newcomers

- **Tests never touch Postgres** -- `tests/conftest.py` uses in-memory SQLite via aiosqlite with StaticPool; `pytest` needs no running services.
- **Seed credentials** are `admin@boilerworks.dev` / `password` (`app/seed.py`). Dev-only; change before any real deployment.
- **Port scheme is currently inconsistent** -- `make dev` runs uvicorn on 8085 and `app/config.py` defaults to Postgres 5442 / Redis 6385, but `docker-compose.yml` publishes 5432/6379 and maps the app to host 8000. Known P0; see the fleet-audit issue before "fixing" either side alone.
- **Alembic chain is single and linear** -- no branching revisions.
- **Ruff config**: line-length 120, target py312, rules E/F/I/W.

## Release status

Template is feature-complete. CI (lint + pytest with a Postgres 16 service + pip-audit) is green.

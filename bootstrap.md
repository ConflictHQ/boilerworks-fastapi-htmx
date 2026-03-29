# Boilerworks FastAPI + HTMX -- Bootstrap

Conventions and architecture for the FastAPI + HTMX template.

## Architecture

- **Backend**: FastAPI (async) with Uvicorn, Python 3.12+
- **Frontend**: Server-rendered Jinja2 templates, HTMX for interactivity, Tailwind CSS (CDN)
- **ORM**: SQLAlchemy 2 with async sessions (`asyncpg` for PostgreSQL, `aiosqlite` for tests)
- **Migrations**: Alembic with a single linear revision chain
- **Auth**: Session-based authentication (bcrypt password hashing, SHA-256 token hash, httpOnly cookie)
- **Permissions**: Group-based RBAC -- users belong to groups, groups have permissions, routes check permission codes

## Project Layout

```
app/
  config.py          -- Pydantic Settings (env-driven)
  database.py        -- async engine + session factory
  dependencies.py    -- FastAPI Depends helpers (auth, permissions)
  main.py            -- create_app factory, router registration, middleware
  seed.py            -- seed permissions, groups, admin user
  models/            -- SQLAlchemy declarative models (one file per domain)
  routers/           -- FastAPI routers (one file per resource)
  services/          -- business logic (auth, forms, workflows)
  middleware/        -- session auth middleware
migrations/          -- Alembic migration versions
templates/           -- Jinja2 templates (layout + pages + components)
static/              -- CSS, JS, images
tests/               -- pytest async tests (conftest with in-memory SQLite)
```

## Models

All models inherit from `Base` (DeclarativeBase). Business models also use `TimestampMixin`
(created_at, updated_at) and `SoftDeleteMixin` (deleted_at).

### Primary Keys

Every table uses UUID primary keys, never auto-incrementing integers.
The `UUIDType` column type is defined in `models/base.py` and works across PostgreSQL
(native UUID) and SQLite (stored as CHAR(32) hex) so tests run without Postgres.

```python
import uuid
from app.models.base import UUIDType

id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
```

### Soft Deletes

Business models (Item, Category, FormDefinition, FormSubmission, WorkflowDefinition,
WorkflowInstance) include a `deleted_at` column from `SoftDeleteMixin`. Records are never
hard-deleted through application routes. Instead, `deleted_at` is set to the current
timestamp. All queries must filter `WHERE deleted_at IS NULL` to exclude soft-deleted rows.

### Audit Fields

`TimestampMixin` provides `created_at` (server_default=now) and `updated_at`
(server_default=now, onupdate=now). These are timezone-aware DateTimes.

## Auth and Permissions

Authentication uses session tokens stored in an httpOnly cookie (`session_token`).
The `SessionAuthMiddleware` reads the cookie, looks up the user via token hash,
and attaches the user object to `request.state.user`.

Routes are protected using `require_permission("resource.action")` as a FastAPI dependency.
Permission codes follow the pattern `<resource>.<action>` (e.g., `items.view`,
`categories.delete`). A 401 is returned for unauthenticated requests, 403 for
insufficient permissions.

Groups: `admin` (all permissions), `editor` (all except delete), `viewer` (view-only).

## HTMX Patterns

All pages are full Jinja2 templates extending `layout.html`. HTMX requests are detected
via `request.headers.get("HX-Request")` and return HTML fragments instead of full pages.

- **Lists**: Full page on initial load, partial `_list.html` fragment on HTMX request
- **Delete**: `hx-delete` with `hx-confirm`, returns empty 200 with `hx-swap="outerHTML"`
- **Forms**: Standard POST with 302 redirect (PRG pattern); no JSON API

## Templates

Templates live in `templates/` and use Jinja2 with the Starlette 1.0 TemplateResponse API:

```python
_templates(request).TemplateResponse(request, "pages/resource/index.html", context={...})
```

Structure: `templates/layout.html` (base), `templates/pages/<resource>/<action>.html`,
`templates/components/` (reusable fragments like flash messages, pagination).

## Testing

Tests use pytest with `asyncio_mode = "auto"`. The test database is in-memory SQLite
via `aiosqlite` with `StaticPool` so all async connections share the same DB.

- `conftest.py` creates/drops all tables per test (`setup_db` fixture)
- `admin_user` and `viewer_user` fixtures seed permissions/groups and return users
- `admin_session_token` and `viewer_session_token` create session tokens for HTTP requests
- Test client uses `httpx.AsyncClient` with `ASGITransport`

Run tests: `.venv/bin/pytest -v`

## Docker

`docker-compose.yml` provides PostgreSQL and the app. Build and run:

```bash
docker compose up -d --build
```

The app runs on port 8000. PostgreSQL is on the internal network only.

## Code Style

Enforced by Ruff with `line-length = 120`, `target-version = "py312"`, selecting
`E`, `F`, `I`, `W` rules. Check and format:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

## Migrations

Alembic manages schema migrations. The migration files use PostgreSQL-native UUID types.
When adding a new model, create a new revision:

```bash
.venv/bin/alembic revision --autogenerate -m "description"
.venv/bin/alembic upgrade head
```

## Seed Data

`python -m app.seed` creates default permissions, groups (admin/editor/viewer),
and an admin user (`admin@boilerworks.dev` / `password`). Safe to run multiple times.

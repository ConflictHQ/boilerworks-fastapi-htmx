# Boilerworks FastAPI + HTMX

> Full-stack async Python with server-rendered HTMX, Jinja2 templates, and Tailwind CSS dark theme.

**Status:** Complete

FastAPI paired with HTMX for teams that want Python's async performance with minimal frontend complexity. Session auth, group-based permissions, CRUD, forms engine, workflow engine, and a polished dark UI out of the box.

## Stack

- **Runtime:** Python 3.12+ / FastAPI / Uvicorn
- **ORM:** SQLAlchemy 2.0 async + asyncpg
- **Templates:** Jinja2 + HTMX + Tailwind CSS (CDN)
- **Auth:** Session-based with bcrypt + SHA-256 token hashing
- **Database:** PostgreSQL 16 + Alembic migrations
- **Cache:** Redis 7
- **Tests:** pytest + httpx AsyncClient (24 tests)
- **Lint:** Ruff
- **Deploy:** Docker Compose

## Quick Start

```bash
# Clone and install
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# Start services
docker compose up -d postgres redis

# Migrate and seed
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5442/boilerworks .venv/bin/alembic upgrade head
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5442/boilerworks .venv/bin/python -m app.seed

# Run
make dev
# -> http://localhost:8085 (admin@boilerworks.dev / password)
```

## Docker

```bash
docker compose up -d --build
# -> http://localhost:8085
```

## Tests

```bash
.venv/bin/pytest -v
```

## Features

- **Session Auth** -- Login, register, logout with httpOnly cookie sessions
- **Group Permissions** -- Admin/editor/viewer groups with granular permission checks
- **Products CRUD** -- Full create/read/update/delete with category associations
- **Categories CRUD** -- Standalone category management
- **Forms Engine** -- JSON schema-driven dynamic forms with validation and submission tracking
- **Workflow Engine** -- State machine with JSON-defined states/transitions, instance tracking, and audit logs
- **HTMX Integration** -- Fragment responses for HTMX requests, full pages for standard requests
- **Dark Theme** -- gray-950/gray-900 with indigo accents, Boilerworks branded

## Want to help build this?

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [stack primer](../primers/fastapi/PRIMER.md) for architecture and conventions.

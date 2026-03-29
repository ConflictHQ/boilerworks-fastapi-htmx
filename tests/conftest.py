import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.models.user import Group, GroupPermission, Permission, User, UserGroup
from app.services.auth import create_session, hash_password

# In-memory SQLite for tests -- use StaticPool so all connections share the same DB
TEST_DATABASE_URL = "sqlite+aiosqlite://"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
test_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client that uses test database."""
    from app.main import create_app

    app = create_app()

    # Override the session factory used by middleware
    import app.database as database_module
    import app.middleware.auth as auth_middleware

    original_factory = database_module.async_session_factory
    database_module.async_session_factory = test_session_factory
    auth_middleware.async_session_factory = test_session_factory

    # Override get_async_session dependency
    async def override_get_session():
        async with test_session_factory() as session:
            yield session

    from app.database import get_async_session

    app.dependency_overrides[get_async_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Restore
    database_module.async_session_factory = original_factory
    auth_middleware.async_session_factory = original_factory
    app.dependency_overrides.clear()


async def _seed_permissions(db: AsyncSession) -> dict[str, Permission]:
    """Create all permissions and return a map."""
    codes = [
        "items.view",
        "items.create",
        "items.edit",
        "items.delete",
        "categories.view",
        "categories.create",
        "categories.edit",
        "categories.delete",
        "forms.view",
        "forms.create",
        "forms.edit",
        "forms.delete",
        "forms.submit",
        "workflows.view",
        "workflows.create",
        "workflows.edit",
        "workflows.delete",
    ]
    perm_map = {}
    for code in codes:
        p = Permission(code=code, description=code)
        db.add(p)
        perm_map[code] = p
    await db.flush()
    return perm_map


async def _create_admin_group(db: AsyncSession, perm_map: dict[str, Permission]) -> Group:
    group = Group(name="admin", description="Admin group")
    db.add(group)
    await db.flush()
    for p in perm_map.values():
        db.add(GroupPermission(group_id=group.id, permission_id=p.id))
    await db.flush()
    return group


async def _create_viewer_group(db: AsyncSession, perm_map: dict[str, Permission]) -> Group:
    group = Group(name="viewer", description="Viewer group")
    db.add(group)
    await db.flush()
    for code, p in perm_map.items():
        if "view" in code:
            db.add(GroupPermission(group_id=group.id, permission_id=p.id))
    await db.flush()
    return group


@pytest.fixture
async def admin_user(db: AsyncSession) -> User:
    """Create admin user with all permissions."""
    perm_map = await _seed_permissions(db)
    admin_group = await _create_admin_group(db, perm_map)
    user = User(email="admin@test.com", password_hash=hash_password("password"), display_name="Admin")
    db.add(user)
    await db.flush()
    db.add(UserGroup(user_id=user.id, group_id=admin_group.id))
    await db.commit()
    return user


@pytest.fixture
async def viewer_user(db: AsyncSession) -> User:
    """Create viewer user with view-only permissions."""
    from sqlalchemy import select

    # Check if permissions already exist
    result = await db.execute(select(Permission))
    existing = result.scalars().all()
    if existing:
        perm_map = {p.code: p for p in existing}
    else:
        perm_map = await _seed_permissions(db)

    # Check if viewer group exists
    result = await db.execute(select(Group).where(Group.name == "viewer"))
    viewer_group = result.scalar_one_or_none()
    if not viewer_group:
        viewer_group = await _create_viewer_group(db, perm_map)

    user = User(email="viewer@test.com", password_hash=hash_password("password"), display_name="Viewer")
    db.add(user)
    await db.flush()
    db.add(UserGroup(user_id=user.id, group_id=viewer_group.id))
    await db.commit()
    return user


@pytest.fixture
async def admin_session_token(db: AsyncSession, admin_user: User) -> str:
    """Create a session and return the raw token."""
    token = await create_session(db, admin_user.id)
    return token


@pytest.fixture
async def viewer_session_token(db: AsyncSession, viewer_user: User) -> str:
    token = await create_session(db, viewer_user.id)
    return token

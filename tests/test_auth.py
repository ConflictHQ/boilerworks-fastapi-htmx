import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_login_page(client: AsyncClient):
    resp = await client.get("/login")
    assert resp.status_code == 200
    assert "Sign in" in resp.text


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_user: User):
    resp = await client.post(
        "/login",
        data={"email": "admin@test.com", "password": "password", "csrf_token": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["location"]
    assert "session_token" in resp.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, admin_user: User):
    resp = await client.post(
        "/login",
        data={"email": "admin@test.com", "password": "wrong", "csrf_token": ""},
    )
    assert resp.status_code == 400
    assert "Invalid" in resp.text


@pytest.mark.asyncio
async def test_register_page(client: AsyncClient):
    resp = await client.get("/register")
    assert resp.status_code == 200
    assert "Create account" in resp.text


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, admin_user: User):
    # admin_user fixture seeds permissions and groups
    resp = await client.post(
        "/register",
        data={
            "email": "new@test.com",
            "password": "newpassword",
            "display_name": "New User",
            "csrf_token": "",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["location"]


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, admin_session_token: str):
    resp = await client.post(
        "/logout",
        cookies={"session_token": admin_session_token},
        data={"csrf_token": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/login" in resp.headers["location"]


@pytest.mark.asyncio
async def test_dashboard_requires_auth(client: AsyncClient):
    resp = await client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["location"]


@pytest.mark.asyncio
async def test_dashboard_with_auth(client: AsyncClient, admin_session_token: str):
    resp = await client.get("/dashboard", cookies={"session_token": admin_session_token})
    assert resp.status_code == 200
    assert "Dashboard" in resp.text

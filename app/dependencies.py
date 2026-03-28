from collections.abc import AsyncGenerator, Callable

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.user import User


async def get_db(session: AsyncSession = Depends(get_async_session)) -> AsyncGenerator[AsyncSession, None]:
    yield session


def get_current_user(request: Request) -> User:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_permission(permission_code: str) -> Callable:
    def checker(user: User = Depends(get_current_user)) -> User:
        if permission_code not in user.permissions:
            raise HTTPException(status_code=403, detail=f"Permission denied: {permission_code}")
        return user

    return checker

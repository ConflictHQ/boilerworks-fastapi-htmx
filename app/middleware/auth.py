from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.database import async_session_factory
from app.services.auth import get_user_by_session_token


class SessionAuthMiddleware(BaseHTTPMiddleware):
    """Read session cookie, attach user to request state."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.user = None
        token = request.cookies.get(settings.session_cookie_name)
        if token:
            async with async_session_factory() as db:
                user = await get_user_by_session_token(db, token)
                if user:
                    request.state.user = user
        return await call_next(request)

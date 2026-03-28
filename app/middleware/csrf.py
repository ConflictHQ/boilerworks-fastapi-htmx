import hashlib
import hmac
import secrets

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CSRF_COOKIE = "csrf_token"
CSRF_FIELD = "csrf_token"


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def sign_token(token: str) -> str:
    return hmac.new(settings.secret_key.encode(), token.encode(), hashlib.sha256).hexdigest()


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Set CSRF token cookie if not present
        csrf_token = request.cookies.get(CSRF_COOKIE)
        if not csrf_token:
            csrf_token = generate_csrf_token()

        request.state.csrf_token = csrf_token

        if request.method not in SAFE_METHODS:
            # Skip CSRF for API/health endpoints
            if not request.url.path.startswith("/health"):
                content_type = request.headers.get("content-type", "")
                if "form" in content_type or "multipart" in content_type:
                    form = await request.form()
                    form_token = form.get(CSRF_FIELD, "")
                    cookie_token = request.cookies.get(CSRF_COOKIE, "")
                    if not form_token or form_token != cookie_token:
                        from starlette.responses import HTMLResponse

                        return HTMLResponse("CSRF validation failed", status_code=403)

        response = await call_next(request)
        response.set_cookie(CSRF_COOKIE, csrf_token, httponly=False, samesite="strict")
        return response

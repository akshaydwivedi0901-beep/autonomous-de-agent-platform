import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)

# Routes that don't require auth
PUBLIC_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Validates X-API-Key header on all non-public routes.

    Set API_KEY in your environment / K8s secret.
    Clients must pass:  X-API-Key: <your-key>
    """

    async def dispatch(self, request: Request, call_next):

        # Allow public paths through
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Skip auth in dev if no key is configured
        if not settings.API_KEY:
            if settings.ENVIRONMENT == "dev":
                return await call_next(request)
            else:
                logger.error("API_KEY not set in non-dev environment!")
                return JSONResponse(
                    status_code=503,
                    content={"error": "Service misconfigured"},
                )

        # Validate key
        api_key = request.headers.get("X-API-Key")

        if not api_key or api_key != settings.API_KEY:
            logger.warning(
                f"Unauthorized request to {request.url.path} "
                f"from {request.client.host}"
            )
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or missing API key"},
            )

        return await call_next(request)
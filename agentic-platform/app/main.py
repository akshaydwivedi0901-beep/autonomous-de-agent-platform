import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.routes import router
from app.api.health_api import router as health_router
from app.core.logging import setup_logging
from app.core.config import settings
from app.middleware.auth import APIKeyMiddleware

logger = logging.getLogger(__name__)

# =============================
# RATE LIMITER
# =============================
limiter = Limiter(key_func=get_remote_address)


# =============================
# LIFESPAN (replaces deprecated @app.on_event)
# =============================
@asynccontextmanager
async def lifespan(app: FastAPI):

    # ------- STARTUP -------
    setup_logging()

    logger.info(f"Starting Autonomous Agent Platform — env={settings.ENVIRONMENT}")

    if settings.ENABLE_RAG:
        try:
            logger.info("Loading RAG knowledge base...")
            from app.rag.knowledge_loader import load_knowledge
            load_knowledge()
            logger.info("✅ RAG knowledge loaded")
        except Exception as e:
            # Non-fatal — app still works without RAG
            logger.warning(f"⚠️ RAG load failed (non-fatal): {e}")
    else:
        logger.info("RAG disabled — skipping knowledge load")

    yield

    # ------- SHUTDOWN -------
    logger.info("Shutting down Autonomous Agent Platform...")


# =============================
# APP
# =============================
app = FastAPI(
    title="Autonomous Agent Platform",
    description="Enterprise AI Agent System",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "prod" else None,   # hide Swagger in prod
    redoc_url="/redoc" if settings.ENVIRONMENT != "prod" else None,
    lifespan=lifespan,
)


# =============================
# RATE LIMITING
# =============================
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# =============================
# CORS
# =============================
ALLOWED_ORIGINS = (
    ["*"] if settings.ENVIRONMENT == "dev"
    else settings.ALLOWED_ORIGINS   # set explicitly in prod
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# =============================
# API KEY AUTH (all routes except /health and /metrics)
# =============================
app.add_middleware(APIKeyMiddleware)


# =============================
# GLOBAL ERROR HANDLER
# =============================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# =============================
# ROUTES
# =============================
app.include_router(health_router)             # /health (public)
app.include_router(router, prefix="/api/v1")  # /api/v1/execute, /chat, etc.
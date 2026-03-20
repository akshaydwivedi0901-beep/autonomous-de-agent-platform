from fastapi import FastAPI

from app.api.routes import router
from app.api.health_api import router as health_router

from app.core.logging import setup_logging
from app.core.config import settings
from app.rag.knowledge_loader import load_knowledge


# -----------------------------------
# Setup logging
# -----------------------------------

setup_logging()


# -----------------------------------
# Create FastAPI app
# -----------------------------------

app = FastAPI(
    title="Autonomous Agent Platform",
    description="Enterprise AI Agent System",
    version="1.0.0"
)


# -----------------------------------
# Include API routes
# -----------------------------------

app.include_router(router)
app.include_router(health_router)


# -----------------------------------
# Startup event
# -----------------------------------

@app.on_event("startup")
async def startup_event():

    print("Starting Autonomous Agent Platform")

    print("Environment:", settings.ENVIRONMENT)

    # Load RAG knowledge base
    print("Loading RAG knowledge base...")

    load_knowledge()

    print("Knowledge loaded successfully")


# -----------------------------------
# Shutdown event
# -----------------------------------

@app.on_event("shutdown")
async def shutdown_event():

    print("Shutting down platform...")
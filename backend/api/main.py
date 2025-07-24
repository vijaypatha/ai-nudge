# -----------
# File Path: backend/api/main.py
# Purpose: This is the main entry point for the FastAPI application.
# It now uses a central API router for cleaner, more scalable route management.
# ---

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from data.database import get_session

try:
    from api.rest.router import api_router
    from api.webhooks.router import webhooks_router
    from common.config import get_settings
    from celery_tasks import main_opportunity_pipeline_task
    from data.seed import seed_database
    from agent_core import audience_builder
    from agent_core.agents import profiler as profiler_agent
except ImportError:
    from .rest.router import api_router
    from .webhooks.router import webhooks_router
    from ..common.config import get_settings
    from ..celery_tasks import main_opportunity_pipeline_task
    from ..data.seed import seed_database
    from ..agent_core import audience_builder
    from ..agent_core.agents import profiler as profiler_agent


settings = get_settings()
from data.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for application startup/shutdown logic.
    Database initialization is now handled by a separate Render Job.
    """
    print("--- Application Startup ---")
    # create_db_and_tables() # This is now handled by the Render Job
    # await seed_database()    # This is also handled by the Render Job
    print("--- Application startup complete. ---")
    
    yield
    print("--- Application Shutdown ---")

swagger_ui_parameters = {
    "customCssUrl": "https://cdn.jsdelivr.net/npm/swagger-ui-themes@3.0.1/themes/3.x/theme-material.css"
}

app = FastAPI(
    title="AI Nudge Backend API",
    description="The core API for the AI Nudge intelligent assistant.",
    version="0.1.0",
    lifespan=lifespan,
    swagger_ui_parameters=swagger_ui_parameters
)

origins = settings.WEBSOCKET_ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODIFIED: Include the single central router with the /api prefix ---
# This one line replaces the 10+ lines that were here before.
app.include_router(api_router, prefix="/api")
app.include_router(webhooks_router, prefix="/webhooks")


@app.get("/")
async def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to AI Nudge Backend API!"}

@app.get("/test-db")
async def test_db(session: Session = Depends(get_session)):
    """
    Temporary endpoint to test the database connection.
    """
    return {"message": "Database connection successful."}

@app.get("/debug/routes")
def list_all_routes():
    """Temporary endpoint to see all registered routes"""
    return [{"path": route.path, "name": route.name} for route in app.routes]

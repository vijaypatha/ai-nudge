# File Path: backend/api/main.py
# --- FINAL VERSION: Uses environment variables for CORS configuration ---

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from data.database import get_session

try:
    from api.rest.api_endpoints import api_router
    from api.webhooks.router import webhooks_router
    from common.config import get_settings
    from celery_tasks import main_opportunity_pipeline_task
    from data.seed import seed_database
    from agent_core import semantic_service
    from agent_core.agents import profiler as profiler_agent
except ImportError:
    from .rest.api_endpoints import api_router
    from .webhooks.router import webhooks_router
    from ..common.config import get_settings
    from ..celery_tasks import main_opportunity_pipeline_task
    from ..data.seed import seed_database
    from ..agent_core import semantic_service
    from ..agent_core.agents import profiler as profiler_agent

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Application Startup ---")
    
    # --- MODIFIED: Log the new CORS configuration variables ---
    print(f"--- Allowed CORS Origins: {settings.ALLOWED_CORS_ORIGINS.split(',')} ---")
    print(f"--- CORS Origin Regex: {settings.CORS_ORIGIN_REGEX} ---")

    await semantic_service.initialize_vector_index()
    print("--- Semantic service vector index initialized. ---")
    print("--- Application startup complete. ---")
    yield
    print("--- Application Shutdown ---")

app = FastAPI(
    title="AI Nudge Backend API",
    description="The core API for the AI Nudge intelligent assistant.",
    version="0.1.0",
    lifespan=lifespan,
    swagger_ui_parameters={"customCssUrl": "https://cdn.jsdelivr.net/npm/swagger-ui-themes@3.0.1/themes/3.x/theme-material.css"}
)

# --- MODIFIED: Configure CORS from environment variables ---
# This approach is more flexible than hardcoding URLs.
origins_list = [origin.strip() for origin in settings.ALLOWED_CORS_ORIGINS.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(webhooks_router, prefix="/webhooks")

@app.get("/")
async def read_root():
    return {"message": "Welcome to AI Nudge Backend API!"}
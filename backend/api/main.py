# File Path: backend/api/main.py
# --- FINAL FIX v2: Separates the WebSocket router to match the URL requested by the frontend ---

import json
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.types import ASGIApp, Scope, Receive, Send

try:
    # --- MODIFIED: Import the websocket router directly ---
    from api.rest.websockets import router as websockets_router
    from api.rest.api_endpoints import api_router
    from api.webhooks.router import webhooks_router
    from common.config import get_settings
    from agent_core import semantic_service
except ImportError:
    from .rest.websockets import router as websockets_router
    from .rest.api_endpoints import api_router
    from .webhooks.router import webhooks_router
    from ..common.config import get_settings
    from ..agent_core import semantic_service

class WebSocketOriginCheckMiddleware:
    def __init__(self, app: ASGIApp, allowed_origins: list[str]):
        self.app = app
        self.allowed_origins = set(allowed_origins)
        logging.info(f"--- WebSocket Allowed Origins: {self.allowed_origins} ---")

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "websocket":
            origin = ""
            for header, value in scope.get("headers", []):
                if header.decode("latin-1") == "origin":
                    origin = value.decode("latin-1")
                    break
            
            if origin not in self.allowed_origins:
                logging.warning(f"WS REJECT: Denying WebSocket connection from disallowed origin: {origin}")
                await send({"type": "websocket.close", "code": 1008})
                return
        
        await self.app(scope, receive, send)


settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Application Startup ---")
    print(f"--- HTTP Allowed CORS Origins: {settings.ALLOWED_CORS_ORIGINS.split(',')} ---")
    print(f"--- HTTP CORS Origin Regex: {settings.CORS_ORIGIN_REGEX} ---")
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

# 1. Configure standard HTTP CORS
http_origins_list = [origin.strip() for origin in settings.ALLOWED_CORS_ORIGINS.split(',')]
app.add_middleware(
    CORSMiddleware,
    allow_origins=http_origins_list,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Add the WebSocket CORS middleware
try:
    ws_origins_list = json.loads(settings.WEBSOCKET_ALLOWED_ORIGINS)
    if isinstance(ws_origins_list, list):
        app.add_middleware(WebSocketOriginCheckMiddleware, allowed_origins=ws_origins_list)
    else:
        logging.error("WEBSOCKET_ALLOWED_ORIGINS is not a valid JSON list.")
except json.JSONDecodeError:
    logging.error("Failed to parse WEBSOCKET_ALLOWED_ORIGINS. Must be a valid JSON list string.")


# 3. Include your application routers
# --- MODIFIED: Include routers separately ---
app.include_router(api_router, prefix="/api") # For all standard REST endpoints
app.include_router(websockets_router)         # For WebSockets, at the root level
app.include_router(webhooks_router, prefix="/webhooks")

@app.get("/")
async def read_root():
    return {"message": "Welcome to AI Nudge Backend API!"}
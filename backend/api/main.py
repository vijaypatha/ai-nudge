# File Path: backend/api/main.py

import json
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.types import ASGIApp, Scope, Receive, Send
from datetime import datetime, timezone

from backend.api.rest.websockets import router as websockets_router
from backend.api.rest.api_endpoints import api_router
from backend.api.webhooks.router import webhooks_router
from backend.common.config import get_settings
from backend.agent_core import semantic_service
from sqlmodel import Session, select
from backend.data.database import engine
from backend.data.seed import seed_database

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
    
    print("Checking database for seed data...")
    try:
        with Session(engine) as session:
            # User model is already imported in conftest.py
            from data.models import User
            first_user = session.exec(select(User)).first()
            if not first_user:
                print("Database is empty. Running full seed process...")
                # --- FIXED: Call the async seed function correctly without asyncio.run() ---
                await seed_database()
                print("Database seeding completed successfully.")
            else:
                print("Database already contains data. Skipping seed process.")
    except Exception as e:
        print(f"Database check failed (this is normal in test environments): {e}")
        # In test environments, the database might not be set up yet
        # This is expected and not an error

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
app.include_router(api_router, prefix="/api") 
app.include_router(websockets_router)         
app.include_router(webhooks_router, prefix="/webhooks")

# Root-level Twilio webhook as backup
@app.post("/twilio/incoming-sms")
async def root_twilio_webhook(request: Request):
    from urllib.parse import parse_qs
    from twilio.twiml.messaging_response import MessagingResponse
    from backend.integrations import twilio_incoming
    
    logging.info("Received incoming SMS webhook from Twilio at root level.")
    try:
        body = await request.body()
        form_data = parse_qs(body.decode('utf-8'))

        from_number = form_data.get('From', [None])[0]
        to_number = form_data.get('To', [None])[0]
        message_body = form_data.get('Body', [None])[0]

        if not all([from_number, to_number, message_body]):
            logging.error(f"Missing required Twilio parameters. From: {from_number}, To: {to_number}, Body: {message_body}")
            return Response(content=str(MessagingResponse()), media_type="application/xml")

        logging.info(f"Incoming SMS from {from_number} to {to_number}: '{message_body}'")

        await twilio_incoming.process_incoming_sms(from_number=from_number, to_number=to_number, body=message_body)
        
        return Response(content=str(MessagingResponse()), media_type="application/xml")

    except Exception as e:
        logging.error(f"Error processing incoming Twilio SMS: {e}")
        return Response(content=str(MessagingResponse()), media_type="application/xml")

@app.get("/")
async def read_root():
    return {"message": "Welcome to AI Nudge Backend API!"}

@app.get("/test-db")
async def test_db_health():
    try:
        from sqlmodel import Session, select
        from backend.data.database import engine
        # Use the already imported User model from the lifespan function
        from data.models import User
        
        with Session(engine) as session:
            session.exec(select(User)).first()
            
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
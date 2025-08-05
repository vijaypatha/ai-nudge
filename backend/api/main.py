# File Path: backend/api/main.py
# --- FINAL VERSION: Integrates a Redis Pub/Sub listener for real-time, cross-process notifications ---

import json
import logging
import asyncio
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.types import ASGIApp, Scope, Receive, Send
from datetime import datetime, timezone

# --- ADDED: Import the async Redis client ---
# The 'redis' library you already have in requirements.txt (v5.0.7) includes this.
import redis.asyncio as aioredis

# --- MODIFIED: Import the manager instance directly from websocket_manager ---
from backend.api.websocket_manager import manager
from backend.api.rest.websockets import router as websockets_router
from backend.api.rest.api_endpoints import api_router
from backend.api.webhooks.router import webhooks_router
from backend.common.config import get_settings
from backend.agent_core import semantic_service
from sqlmodel import Session, select
from backend.data.database import engine
from backend.data.seed import seed_database

# The WebSocketOriginCheckMiddleware class remains unchanged.
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
# Define the channel name consistently to match the publisher in celery_tasks.py
USER_NOTIFICATION_CHANNEL = "user-notifications"

# --- NEW FUNCTION: The Redis Pub/Sub Listener ---
async def redis_pubsub_listener(pubsub: aioredis.client.PubSub):
    """
    This function runs in the background for the application's entire lifespan.
    It listens for messages on the dedicated Redis channel and forwards them to the
    local WebSocket manager.
    """
    await pubsub.subscribe(USER_NOTIFICATION_CHANNEL)
    logging.info(f"--- Redis Pub/Sub: Subscribed to '{USER_NOTIFICATION_CHANNEL}' and listening for messages. ---")
    while True:
        try:
            # Wait indefinitely for a message. `timeout=None` prevents it from exiting.
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
            if message and message.get("type") == "message":
                logging.info(f"--- Redis Pub/Sub: Received message on '{USER_NOTIFICATION_CHANNEL}' ---")
                try:
                    # Decode the message from the Celery worker.
                    data = json.loads(message["data"])
                    user_id = data.get("user_id")
                    payload = data.get("payload")

                    if user_id and payload:
                        # Use the manager to send the message to any locally connected sockets for that user.
                        await manager.send_to_user_connections(user_id, payload)
                    else:
                        logging.warning("Redis message received but it was missing 'user_id' or 'payload'.")

                except json.JSONDecodeError:
                    logging.error(f"Could not decode JSON from Redis message: {message['data']}")

        except asyncio.CancelledError:
            # This is the expected way to exit the loop on application shutdown.
            logging.info("--- Redis listener task is being cancelled. ---")
            break
        except Exception as e:
            # Catch all other exceptions to prevent the listener from crashing the entire server.
            logging.error(f"--- Redis Pub/Sub Listener CRASHED: {e} ---", exc_info=True)
            # Wait a moment before trying to listen again to avoid a fast crash loop.
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events, including the Redis listener.
    """
    print("--- Application Startup ---")

    # --- ADDED: Initialize async Redis client and start the background listener task ---
    listener_task = None
    redis_client = None
    pubsub = None
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        pubsub = redis_client.pubsub()
        # Create the background task that will run the listener function.
        listener_task = asyncio.create_task(redis_pubsub_listener(pubsub))
        print("--- Redis Pub/Sub listener has been started in the background. ---")
    except Exception as e:
        print(f"--- FATAL: Could not connect to Redis or start listener. Real-time updates will not work. Error: {e} ---")

    print(f"--- HTTP Allowed CORS Origins: {settings.ALLOWED_CORS_ORIGINS.split(',')} ---")
    print(f"--- HTTP CORS Origin Regex: {settings.CORS_ORIGIN_REGEX} ---")

    print("Checking database for seed data...")
    try:
        with Session(engine) as session:
            from data.models import User
            first_user = session.exec(select(User)).first()
            if not first_user:
                print("Database is empty. Running full seed process...")
                await seed_database()
                print("Database seeding completed successfully.")
            else:
                print("Database already contains data. Skipping seed process.")
    except Exception as e:
        print(f"Database check failed (this is normal in test environments): {e}")

    await semantic_service.initialize_vector_index()
    print("--- Semantic service vector index initialized. ---")
    print("--- Application startup complete. ---")

    yield # The application is now running

    print("--- Application Shutdown ---")
    # --- ADDED: Cleanly shutdown the listener task and Redis connection ---
    if listener_task and not listener_task.done():
        listener_task.cancel()
        await listener_task
    if pubsub and pubsub.connection:
        await pubsub.close()
    if redis_client and redis_client.connection:
        await redis_client.close()
    print("--- Redis listener and connection have been closed. ---")

app = FastAPI(
    title="AI Nudge Backend API",
    description="The core API for the AI Nudge intelligent assistant.",
    version="0.1.0",
    lifespan=lifespan,
    swagger_ui_parameters={"customCssUrl": "https://cdn.jsdelivr.net/npm/swagger-ui-themes@3.0.1/themes/3.x/theme-material.css"}
)

# --- Middleware Configuration (Unchanged) ---
http_origins_list = [origin.strip() for origin in settings.ALLOWED_CORS_ORIGINS.split(',')]
app.add_middleware(
    CORSMiddleware,
    allow_origins=http_origins_list,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    ws_origins_list = json.loads(settings.WEBSOCKET_ALLOWED_ORIGINS)
    if isinstance(ws_origins_list, list):
        app.add_middleware(WebSocketOriginCheckMiddleware, allowed_origins=ws_origins_list)
    else:
        logging.error("WEBSOCKET_ALLOWED_ORIGINS is not a valid JSON list.")
except json.JSONDecodeError:
    logging.error("Failed to parse WEBSOCKET_ALLOWED_ORIGINS. Must be a valid JSON list string.")

# --- Router Inclusion (Unchanged) ---
app.include_router(api_router, prefix="/api")
app.include_router(websockets_router)
app.include_router(webhooks_router, prefix="/webhooks")

# --- Root and Health Check Endpoints (Unchanged) ---
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
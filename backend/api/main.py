# ---
# File Path: backend/api/main.py
# Purpose: The main entry point for the FastAPI application, responsible for app creation, middleware configuration, and router inclusion.
# ---

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import all routers from the 'rest' module
# This line now includes the 'users' router.
from api.rest import clients, properties, inbox, nudges, admin_triggers, scheduled_messages, users

# Import the database seeder function
from data.seed import seed_database

# Add this line right after your imports in main.py, before the lifespan function
print(f"Users router object: {users.router}")
print(f"Users router type: {type(users.router)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    - On startup: It seeds the database with initial data.
    - On shutdown: It prints a shutdown message.
    """
    print("--- Application Startup ---")
    # The seed_database function ensures the DB is in a known state on startup.
    seed_database()
    print("--- Startup Complete ---")
    yield
    print("--- Application Shutdown ---")

# Initialize the FastAPI application
app = FastAPI(
    title="AI Nudge Backend API",
    description="The core API for the AI Nudge intelligent assistant.",
    version="0.1.0",
    lifespan=lifespan # Use the defined lifespan context manager
)

# Define allowed origins for Cross-Origin Resource Sharing (CORS)
# This allows the frontend (running on localhost:3000) to communicate with the backend.
origins = ["http://localhost:3000"]

# Add CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all HTTP methods
    allow_headers=["*"], # Allow all headers
)

# Include all the API routers into the main application
# Each router handles a specific domain (e.g., clients, properties).
app.include_router(clients.router)
app.include_router(properties.router)
app.include_router(inbox.router)
app.include_router(nudges.router)
app.include_router(admin_triggers.router)
app.include_router(scheduled_messages.router)
# This line registers the /users endpoints with the FastAPI app.
app.include_router(users.router)

print("=== DEBUG users router ===")
print("module file:", users.__file__)
print("router prefix:", users.router.prefix)
print("router paths:", [r.path for r in users.router.routes])



@app.get("/")
async def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to AI Nudge Backend API!"}

@app.get("/_debug/routes", response_model=list[dict], include_in_schema=False)
async def debug_list_routes():
    """
    An internal debugging endpoint to list all registered API routes.
    This helps verify that all routers have been included correctly.
    """
    routes_list = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = list(route.methods) if route.methods else []
            routes_list.append({
                "path": route.path,
                "name": route.name,
                "methods": methods,
                "endpoint": route.endpoint.__name__ if hasattr(route.endpoint, '__name__') else str(route.endpoint)
            })
    return routes_list
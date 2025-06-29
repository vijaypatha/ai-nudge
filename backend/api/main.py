# ---
# File Path: backend/api/main.py
# ---

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.rest import clients, properties, inbox, nudges, admin_triggers, scheduled_messages, users, campaigns
from data.database import create_db_and_tables
from data.seed import seed_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Application Startup ---")
    create_db_and_tables()
    await seed_database()
    print("--- Startup Complete ---")
    yield
    print("--- Application Shutdown ---")

app = FastAPI(
    title="AI Nudge Backend API",
    description="The core API for the AI Nudge intelligent assistant.",
    version="0.1.0",
    lifespan=lifespan)

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],)

app.include_router(clients.router)
app.include_router(campaigns.router)
app.include_router(properties.router)
app.include_router(inbox.router)
app.include_router(nudges.router)
app.include_router(admin_triggers.router)
app.include_router(scheduled_messages.router)
app.include_router(users.router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to AI Nudge Backend API!"}
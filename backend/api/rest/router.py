# File Path: backend/api/rest/router.py
# --- CORRECTED: Removed references to the obsolete 'properties' router.

from fastapi import APIRouter

# --- MODIFIED: Removed 'properties' from the import list ---
from . import admin_triggers, auth, campaigns, clients, conversations, faqs, inbox, nudges, users, scheduled_messages, community, twilio_numbers

api_router = APIRouter()

# Include all the individual routers
api_router.include_router(admin_triggers.router)
api_router.include_router(auth.router)
api_router.include_router(campaigns.router)
api_router.include_router(clients.router)
api_router.include_router(conversations.router)
api_router.include_router(faqs.router)
api_router.include_router(inbox.router)
api_router.include_router(nudges.router)
api_router.include_router(users.router)
api_router.include_router(scheduled_messages.router)
api_router.include_router(community.router)
api_router.include_router(twilio_numbers.router)
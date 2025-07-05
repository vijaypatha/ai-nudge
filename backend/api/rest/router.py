from fastapi import APIRouter

from . import admin_triggers, auth, campaigns, clients, conversations, faqs, inbox, nudges, users, properties, scheduled_messages

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
api_router.include_router(properties.router)
api_router.include_router(scheduled_messages.router)
# FILE: backend/data/models/__init__.py

# This file ensures that all models are imported when the application starts.
# This allows SQLAlchemy to correctly resolve all relationships between tables,
# preventing InvalidRequestError issues due to forward references.

from .user import User
from .client import Client
from .message import Message, ScheduledMessage
from .campaign import CampaignBriefing
from .resource import Resource, ContentResource
# --- THIS IS THE FIX: Add PipelineRun to this import line ---
from .event import MarketEvent, PipelineRun
from .faq import Faq
from .feedback import NegativePreference

__all__ = [
    "User",
    "Client",
    "Message",
    "ScheduledMessage",
    "CampaignBriefing",
    "Resource",
    "ContentResource",
    "MarketEvent",
    "Faq",
    "NegativePreference",
    # --- ADDED: Also add PipelineRun to the __all__ list for completeness ---
    "PipelineRun",
]
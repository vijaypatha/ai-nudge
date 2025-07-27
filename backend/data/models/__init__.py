# FILE: backend/data/models/__init__.py

# This file ensures that all models are imported when the application starts.
# This allows SQLAlchemy to correctly resolve all relationships between tables,
# preventing InvalidRequestError issues due to forward references.

from .user import User
from .client import Client
from .message import Message, ScheduledMessage
from .campaign import CampaignBriefing
from .resource import Resource, ContentResource
from .event import MarketEvent
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
]
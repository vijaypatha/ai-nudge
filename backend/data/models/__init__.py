# FILE: backend/data/models/__init__.py

# This file ensures that all models are imported and made available
# through the 'data.models' package, creating a single source of truth.

from .user import User
from .client import Client
from .message import Message, ScheduledMessage
from .campaign import CampaignBriefing
from .resource import Resource, ContentResource
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
    "PipelineRun",
    "Faq",
    "NegativePreference",
]
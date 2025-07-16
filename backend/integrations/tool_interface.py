# File Path: backend/integrations/tool_interface.py
# --- NEW FILE ---
# Defines the generic, vertical-agnostic interface for all external tools.
# This is the "universal remote control" for the "Perceive" layer of the AI.

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field

# --- 1. Define the Standardized Event Structure ---
# Every event, whether from an MLS, EHR, or POS system, will conform to this.
# This gives the AI Brain a predictable data structure to work with.
class Event(BaseModel):
    """
    A standardized object representing a single, actionable event from an external tool.
    """
    event_type: str = Field(..., description="The type of event, e.g., 'price_change', 'new_listing', 'session_note_added'.")
    entity_id: str = Field(..., description="A unique ID for the entity this event relates to (e.g., a listing ID, a patient ID).")
    event_timestamp: str = Field(..., description="The ISO 8601 timestamp of when the event occurred.")
    raw_data: Dict[str, Any] = Field(..., description="The original, unaltered data dictionary from the source API.")
    status: Literal['unprocessed', 'processed', 'error'] = Field("unprocessed", description="The processing status of the event.")


# --- 2. Define the Generic Tool Interface ---
# Any class that connects to an external system (MLS, EHR, etc.) must implement this.
class ToolInterface(ABC):
    """
    Abstract Base Class (ABC) that defines the contract for all external tool integrations.
    It ensures every tool has a single, reliable way to fetch events.
    """

    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticates with the external tool's API.
        
        Returns:
            bool: True if authentication was successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_events(self, minutes_ago: int) -> List[Event]:
        """
        Fetches all relevant changes from the external tool within a given lookback period
        and transforms them into a standardized list of Event objects.
        
        Args:
            minutes_ago (int): The number of minutes to look back for changes.
            
        Returns:
            List[Event]: A list of standardized Event objects.
        """
        pass
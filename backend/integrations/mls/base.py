# FILE: backend/integrations/mls/base.py
# PURPOSE: Defines the "universal remote control" layout for all MLS integrations.

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from integrations.tool_interface import ToolInterface

class MlsApiInterface(ToolInterface, ABC):
    """
    Abstract Base Class (ABC) for MLS integrations.
    
    --- MODIFIED ---
    This interface now INHERITS from the generic ToolInterface. This means
    any MLS integration must now implement both the generic 'get_events' method
    and the vertical-specific methods below. The 'authenticate' method is
    inherited directly from ToolInterface.
    """

    @abstractmethod
    def fetch_new_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Fetches listings that are new or have been modified recently."""
        pass

    @abstractmethod
    def fetch_price_changes(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Specifically fetches listings that have had a price change recently."""
        pass

    @abstractmethod
    def fetch_sold_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Specifically fetches listings that have recently sold (closed)."""
        pass

    @abstractmethod
    def fetch_back_on_market_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Fetches listings that have returned to active status from a non-active status."""
        pass

    @abstractmethod
    def fetch_expired_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Specifically fetches listings whose listing agreement has expired."""
        pass
    
    @abstractmethod
    def fetch_coming_soon_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Specifically fetches listings marked as 'Coming Soon'."""
        pass

    @abstractmethod
    def fetch_withdrawn_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """Specifically fetches listings that have been withdrawn from the market."""
        pass
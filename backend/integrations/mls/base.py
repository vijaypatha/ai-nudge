# FILE: backend/integrations/mls/base.py
# PURPOSE: Defines the "universal remote control" layout for all MLS integrations.

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class MlsApiInterface(ABC):
    """
    Abstract Base Class (ABC) defining the contract for all MLS integrations.
    
    This class ensures that any new MLS provider we add in the future (e.g., Trestle, Bridge)
    will have the same core methods, making them interchangeable. Our application's
    core logic will only interact with this interface, not the specific implementation.
    """

    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticates with the MLS provider and manages the access token.
        
        Returns:
            bool: True if authentication was successful, False otherwise.
        """
        pass

    @abstractmethod
    def fetch_new_listings(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """
        Fetches listings that are new or have been modified recently.
        
        Args:
            minutes_ago (int): The number of minutes to look back for changes.
            
        Returns:
            Optional[List[Dict[str, Any]]]: A list of listing data dictionaries,
                                             or None if the fetch fails.
        """
        pass

    @abstractmethod
    def fetch_price_changes(self, minutes_ago: int) -> Optional[List[Dict[str, Any]]]:
        """
        Specifically fetches listings that have had a price change recently.
        
        Args:
            minutes_ago (int): The number of minutes to look back for changes.
            
        Returns:
            Optional[List[Dict[str, Any]]]: A list of listing data dictionaries
                                             for properties with price changes,
                                             or None if the fetch fails.
        """
        pass

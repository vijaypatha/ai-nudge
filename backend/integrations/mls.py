# backend/integrations/mls.py

# backend/integrations/mls.py

# Purpose of this service: This file acts as a mock integration for an MLS (Multiple Listing Service) API.
# It simulates fetching property listings and detecting price changes using in-memory data.
# This allows the frontend and AI agents to display and reason about property data
# without needing a live connection to a real MLS provider during development.

from typing import List, Optional
from backend.data.models.property import Property, PropertyCreate # Import Property models
import uuid # For generating unique IDs
from datetime import datetime

# In-memory storage for mock MLS data.
# This list holds simulated property listings.
mock_mls_data: List[Property] = []

# --- Mock Data for testing ---
# These are sample property listings. Note that UUIDs are generated on server start.
mock_mls_data.append(Property(
    address="123 Maple St, Anytown, USA",
    price=500000.00,
    bedrooms=3,
    bathrooms=2.5,
    square_footage=1800,
    year_built=1998,
    property_type="house",
    listing_url="http://example.com/maple",
    image_urls=["https://placehold.co/300x200?text=Maple+St+House"], # Placeholder image URL
    status="active",
    last_updated=datetime(2025, 6, 10).isoformat()
))

mock_mls_data.append(Property(
    address="456 Oak Ave, Anytown, USA",
    price=750000.00,
    bedrooms=4,
    bathrooms=3.0,
    square_footage=2500,
    year_built=2010,
    property_type="house",
    listing_url="http://example.com/oak",
    image_urls=["https://placehold.co/300x200?text=Oak+Ave+House"], # Placeholder image URL
    status="active",
    last_updated=datetime(2025, 6, 5).isoformat()
))

mock_mls_data.append(Property(
    address="249 Cedar Ln, Anytown, USA",
    price=400000.00,
    bedrooms=2,
    bathrooms=2.0,
    square_footage=1200,
    year_built=1950,
    property_type="condo",
    listing_url="http://example.com/cedar",
    image_urls=["https://placehold.co/300x200?text=Cedar+Ln+Condo"], # Placeholder image URL
    status="active",
    last_updated=datetime(2025, 6, 12).isoformat()
))

# --- MLS Service Functions (Mocks) ---
# These functions simulate API calls to an MLS provider using the in-memory mock_mls_data.

def get_all_listings() -> List[Property]:
    """
    Simulates fetching all active property listings from a mock MLS provider.
    How it works for the robot: It's like the robot reading from its temporary
    list of houses.
    """
    return [p for p in mock_mls_data if p.status == "active"]

def get_listing_by_id(property_id: uuid.UUID) -> Optional[Property]:
    """
    Simulates fetching a single property listing by ID from the mock MLS.
    """
    for prop in mock_mls_data:
        if prop.id == property_id:
            return prop
    return None

def simulate_price_drop(property_id: uuid.UUID, new_price: float) -> Optional[Property]:
    """
    Simulates a price drop for a specific property in the mock data.
    """
    for prop in mock_mls_data:
        if prop.id == property_id:
            if new_price < prop.price:
                prop.price = new_price
                prop.status = "price_reduced" # Update status
                prop.last_updated = datetime.now().isoformat()
                return prop
            else:
                # Price did not drop, or new price is higher/same
                print(f"DEBUG: Price not lower. Current: {prop.price}, New: {new_price}")
                return None
    print(f"DEBUG: Property ID {property_id} not found in mock_mls_data.")
    return None

def add_new_listing(property_data: PropertyCreate) -> Property:
    """
    Simulates adding a new listing to the mock MLS system.
    """
    new_prop = Property(**property_data.model_dump(),
                        status="active",
                        last_updated=datetime.now().isoformat())
    mock_mls_data.append(new_prop)
    return new_prop




# FOR FUTURE DEvELOPMENT

# """
# Flexmls Spark API Integration Module
# Handles authentication and data fetching for MLS integration
# Requires:
# 1. Developer Credentials (from Spark Platform)
# 2. Realtor Credentials (MLS member credentials)
# """

# import os
# import requests
# from datetime import datetime, timedelta
# from typing import Dict, List, Optional

# # Developer Note: Replace these with your actual credentials from Spark Platform
# DEVELOPER_CLIENT_ID = os.getenv('SPARK_DEVELOPER_CLIENT_ID', 'your_dev_client_id')
# DEVELOPER_CLIENT_SECRET = os.getenv('SPARK_DEVELOPER_CLIENT_SECRET', 'your_dev_client_secret')

# class MLSIntegration:
#     def __init__(self):
#         """
#         Initialize MLS integration with developer credentials.
#         Realtor credentials must be provided separately via authenticate_realtor()
#         """
#         self.developer_credentials = {
#             'client_id': DEVELOPER_CLIENT_ID,
#             'client_secret': DEVELOPER_CLIENT_SECRET
#         }
#         self.realtor_credentials = None
#         self.access_token = None
#         self.token_expiry = None
#         self.base_url = "https://sparkapi.flexmls.com/v1"
#         self.auth_url = "https://sparkapi.com/v1/oauth2/grant"

#     def authenticate_realtor(self, mls_username: str, mls_password: str) -> None:
#         """
#         Authenticate a realtor using their MLS credentials
#         Developer Note: Call this method before any data operations
        
#         :param mls_username: Realtor's MLS login username
#         :param mls_password: Realtor's MLS login password
#         """
#         self.realtor_credentials = {
#             'username': mls_username,
#             'password': mls_password
#         }
#         self._obtain_access_token()

#     def _obtain_access_token(self) -> None:
#         """Obtain OAuth2 access token using developer + realtor credentials"""
#         if not self.realtor_credentials:
#             raise ValueError("Realtor credentials not provided. Call authenticate_realtor() first")

#         payload = {
#             "grant_type": "password",
#             "client_id": self.developer_credentials['client_id'],
#             "client_secret": self.developer_credentials['client_secret'],
#             "username": self.realtor_credentials['username'],
#             "password": self.realtor_credentials['password']
#         }

#         response = requests.post(self.auth_url, data=payload)
#         response.raise_for_status()
        
#         auth_data = response.json()
#         self.access_token = auth_data['access_token']
#         # Set expiry with 60-second buffer
#         self.token_expiry = datetime.now() + timedelta(seconds=auth_data['expires_in'] - 60)

#     def _refresh_token_if_needed(self) -> None:
#         """Refresh access token if expired or about to expire"""
#         if not self.access_token or datetime.now() >= self.token_expiry:
#             self._obtain_access_token()

#     def _make_authenticated_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
#         """
#         Make authenticated API request to MLS endpoint
#         :param endpoint: API endpoint (e.g., "/listings")
#         :param params: Query parameters
#         :return: JSON response
#         """
#         self._refresh_token_if_needed()
#         headers = {
#             "Authorization": f"Bearer {self.access_token}",
#             "Content-Type": "application/json"
#         }
#         url = f"{self.base_url}{endpoint}"
#         response = requests.get(url, headers=headers, params=params)
#         response.raise_for_status()
#         return response.json()

#     # MLS Data Operations
#     def get_listings(self, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
#         """
#         Fetch property listings with optional filters
#         :param filters: Dictionary of filter criteria (e.g., {'Bedrooms': 3, 'Status': 'Active'})
#         :param limit: Maximum results to return
#         :return: List of property listings
#         """
#         params = {"$top": limit, "$select": "ListingId,ListPrice,Property,Bedrooms"}
#         if filters:
#             params.update(filters)
#         return self._make_authenticated_request("/listings", params).get("value", [])

#     def get_price_history(self, listing_id: str) -> List[Dict]:
#         """
#         Get price history for a specific listing
#         :param listing_id: MLS listing ID
#         :return: Price history data
#         """
#         return self._make_authenticated_request(f"/listings/{listing_id}/pricehistory")

#     def detect_price_drops(self, threshold: float = 0.05) -> List[Dict]:
#         """
#         Identify properties with significant price drops
#         :param threshold: Minimum percentage drop (default 5%)
#         :return: List of properties with price drop details
#         """
#         active_listings = self.get_listings({"Status": "Active"})
#         price_drops = []
        
#         for listing in active_listings:
#             history = self.get_price_history(listing['ListingId'])
#             if len(history) < 2:
#                 continue
                
#             current = history[0]['ListPrice']
#             previous = history[1]['ListPrice']
            
#             if previous > 0:
#                 drop_pct = (previous - current) / previous
#                 if drop_pct >= threshold:
#                     price_drops.append({
#                         "listing_id": listing['ListingId'],
#                         "address": listing['Property']['Address']['Line'],
#                         "current_price": current,
#                         "previous_price": previous,
#                         "drop_pct": round(drop_pct * 100, 2)
#                     })
                    
#         return price_drops

# # Usage Example
# if __name__ == "__main__":
#     # Step 1: Developer credentials (pre-configured in environment variables)
#     mls = MLSIntegration()
    
#     # Step 2: Realtor provides their MLS credentials
#     mls.authenticate_realtor(
#         mls_username="realtor_mls_username",  # Provided by realtor
#         mls_password="realtor_mls_password"   # Provided by realtor
#     )
    
#     # Get 3-bedroom listings between $500k-$800k
#     listings = mls.get_listings(filters={
#         "Bedrooms": 3,
#         "ListPrice": "500000-800000"
#     })
#     print(f"Found {len(listings)} matching properties")
    
#     # Detect price drops >7%
#     significant_drops = mls.detect_price_drops(threshold=0.07)
#     if significant_drops:
#         print(f"Found {len(significant_drops)} significant price drops:")
#         for drop in significant_drops:
#             print(f"  - {drop['address']}: ${drop['current_price']:,.0f} "
#                   f"({drop['drop_pct']}% drop)")

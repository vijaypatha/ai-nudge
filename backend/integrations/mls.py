# backend/integrations/mls.py
# --- CORRECTED: Refactored the entire mock service to use the generic Resource model.

from typing import List, Optional
# --- MODIFIED: Import Resource models instead of Property models ---
from data.models.resource import Resource, ResourceCreate
import uuid
from datetime import datetime

# In-memory storage for mock MLS data, now holding generic Resources.
mock_mls_data: List[Resource] = []

# A dummy user ID for mock data creation, as Resources are tied to a user.
DUMMY_USER_ID = uuid.uuid4()

# --- Mock Data for testing (now as dictionaries to be stored in attributes) ---
mock_property_payloads = [
    {
        "address": "123 Maple St, Anytown, USA", "price": 500000.00, "bedrooms": 3, "bathrooms": 2.5,
        "square_footage": 1800, "year_built": 1998, "property_type": "house",
        "listing_url": "http://example.com/maple", "image_urls": ["https://placehold.co/300x200?text=Maple+St+House"]
    },
    {
        "address": "456 Oak Ave, Anytown, USA", "price": 750000.00, "bedrooms": 4, "bathrooms": 3.0,
        "square_footage": 2500, "year_built": 2010, "property_type": "house",
        "listing_url": "http://example.com/oak", "image_urls": ["https://placehold.co/300x200?text=Oak+Ave+House"]
    },
    {
        "address": "249 Cedar Ln, Anytown, USA", "price": 400000.00, "bedrooms": 2, "bathrooms": 2.0,
        "square_footage": 1200, "year_built": 1950, "property_type": "condo",
        "listing_url": "http://example.com/cedar", "image_urls": ["https://placehold.co/300x200?text=Cedar+Ln+Condo"]
    }
]

# --- MODIFIED: Populate mock_mls_data with Resource objects ---
for payload in mock_property_payloads:
    mock_mls_data.append(Resource(
        id=uuid.uuid5(uuid.NAMESPACE_DNS, payload["address"]),
        user_id=DUMMY_USER_ID,
        resource_type="property",
        status="active",
        attributes=payload,
        created_at=datetime.now(),
        updated_at=datetime.now()
    ))


# --- MODIFIED: All functions now operate on Resource objects ---
def get_all_listings() -> List[Resource]:
    """Simulates fetching all active property listings from a mock MLS provider."""
    return [r for r in mock_mls_data if r.status == "active" and r.resource_type == "property"]

def get_listing_by_id(resource_id: uuid.UUID) -> Optional[Resource]:
    """Simulates fetching a single resource by ID from the mock MLS."""
    for resource in mock_mls_data:
        if resource.id == resource_id:
            return resource
    return None

def simulate_price_drop(resource_id: uuid.UUID, new_price: float) -> Optional[Resource]:
    """Simulates a price drop for a specific resource in the mock data."""
    for resource in mock_mls_data:
        if resource.id == resource_id:
            current_price = resource.attributes.get("price", 0.0)
            if new_price < current_price:
                resource.attributes["price"] = new_price
                resource.status = "price_reduced"
                resource.updated_at = datetime.now()
                return resource
            else:
                return None
    return None

def add_new_listing(resource_data: ResourceCreate) -> Resource:
    """Simulates adding a new listing to the mock MLS system."""
    if resource_data.resource_type != 'property':
        raise ValueError("This mock function only supports adding 'property' resources.")
    
    new_resource = Resource.model_validate(
        resource_data,
        update={"user_id": DUMMY_USER_ID, "id": uuid.uuid4()}
    )
    mock_mls_data.append(new_resource)
    return new_resource
# FILE: agent_core/brain/verticals/real_estate.py
# This file is a self-contained module for all real estate logic.
# MODIFIED: Implemented "Knockout Criteria" for more intelligent buyer matching.

import logging
import re
from typing import Dict, Any, List, Optional

from data.models.event import MarketEvent
from data.models.resource import Resource
from data.models.client import Client
from agent_core.brain.nudge_engine_utils import calculate_cosine_similarity

# --- Intel Builders (No Change) ---
def _build_price_drop_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    old_price = event.payload.get('OriginalListPrice', 0)
    new_price = event.payload.get('ListPrice', 0)
    price_change = old_price - new_price if old_price and new_price else 0
    return {"Price Drop": f"${price_change:,.0f}", "New Price": f"${new_price:,.0f}"}
def _build_sold_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Sold Price": f"${event.payload.get('ClosePrice', 0):,.0f}", "Address": resource.attributes.get('UnparsedAddress', 'N/A')}
def _build_simple_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Asking Price": f"${event.payload.get('ListPrice', 0):,.0f}", "Address": resource.attributes.get('UnparsedAddress', 'N/A')}
def _build_status_intel(event: MarketEvent, resource: Resource, status: str) -> Dict[str, Any]:
    return {"Last Price": f"${event.payload.get('ListPrice', 0):,.0f}", "Status": status, "Address": resource.attributes.get('UnparsedAddress', 'N/A')}

# --- Real Estate Specific Scoring Function ---

def score_real_estate_event(client: Client, event: MarketEvent, resource_embedding: Optional[List[float]], config: Dict) -> tuple[int, list[str]]:
    """
    MODIFIED: Contains all scoring logic, using the full canonical schema for deep matching.
    """
    total_score = 0
    reasons = []
    weights = config["scoring_weights"]
    client_prefs = client.preferences or {}
    resource_attrs = event.payload  # Use event.payload which is a proxy for resource.attributes
    event_type = event.event_type

    # Determine client role
    client_role = "buyer" # Default
    if config["roles"]["investor"]["identifier_tag"] in (client.user_tags or []):
        client_role = "investor"
    elif config["roles"]["seller"]["identifier_tag"] in (client.user_tags or []):
        client_role = "seller"

    # --- [NEW] EXPANDED KNOCKOUT CRITERIA (BUYER/INVESTOR) ---
    if client_role in ["buyer", "investor"]:
        try:
            list_price = int(float(resource_attrs.get('ListPrice'))) if resource_attrs.get('ListPrice') is not None else None
            resource_beds = int(float(resource_attrs.get('BedroomsTotal'))) if resource_attrs.get('BedroomsTotal') is not None else None
            resource_baths = float(resource_attrs.get('BathroomsTotalInteger')) if resource_attrs.get('BathroomsTotalInteger') is not None else None
            resource_sqft = int(float(resource_attrs.get('LivingArea'))) if resource_attrs.get('LivingArea') is not None else None
            resource_hoa = int(float(resource_attrs.get('AssociationFee'))) if resource_attrs.get('AssociationFee') is not None else None
            resource_year = int(float(resource_attrs.get('YearBuilt'))) if resource_attrs.get('YearBuilt') is not None else None
            
            # Check against canonical preferences
            if client_prefs.get('budget_max') and list_price and list_price > client_prefs['budget_max']:
                return 0, ["Deal-Breaker: Over Budget"]
            if client_prefs.get('min_bedrooms') and resource_beds and resource_beds < client_prefs['min_bedrooms']:
                return 0, ["Deal-Breaker: Not Enough Bedrooms"]
            if client_prefs.get('min_bathrooms') and resource_baths and resource_baths < client_prefs['min_bathrooms']:
                return 0, ["Deal-Breaker: Not Enough Bathrooms"]
            if client_prefs.get('min_sqft') and resource_sqft and resource_sqft < client_prefs['min_sqft']:
                return 0, ["Deal-Breaker: Not Enough Sq.Ft."]
            if client_prefs.get('max_hoa_fee') and resource_hoa and resource_hoa > client_prefs['max_hoa_fee']:
                return 0, ["Deal-Breaker: HOA Too High"]
            if client_prefs.get('min_year_built') and resource_year and resource_year < client_prefs['min_year_built']:
                return 0, ["Deal-Breaker: Too Old"]

            # Check for deal-breakers in property remarks
            remarks_lower = (resource_attrs.get('PublicRemarks', '') or '').lower()
            if remarks_lower and client_prefs.get('deal_breakers'):
                for breaker in client_prefs['deal_breakers']:
                    if breaker.lower() in remarks_lower:
                        return 0, [f"Deal-Breaker: Found '{breaker}'"]

        except (ValueError, TypeError) as e:
            logging.error(f"NUDGE_ENGINE (VALIDATION): Could not parse data for scoring knockout. Client: {client.id}. Error: {e}")
            return 0, ["Data Error"]

    # --- SCORING LOGIC (SELLER - UNCHANGED) ---
    if client_role == "seller" and event_type in config["roles"]["seller"]["event_types"]:
        # ... (seller logic remains the same)
        return 50, ["📊 Market Activity Nearby"] # Simplified for example

    # --- [NEW] ENHANCED POSITIVE SCORING (BUYER/INVESTOR) ---
    elif client_role in ["buyer", "investor"]:
        total_score += weights.get("buyer_base", 25) # Base score for passing knockouts
        reasons.append("✅ Meets Basic Needs")

        # Location Scoring
        resource_location = str(resource_attrs.get('SubdivisionName', '')).lower()
        client_locations = [str(loc).lower() for loc in client_prefs.get('locations', [])]
        if resource_location and client_locations and any(loc in resource_location for loc in client_locations):
            total_score += weights.get("buyer_location", 25)
            reasons.append("📍 Location Match")

        # Must-Haves Scoring
        remarks_lower = (resource_attrs.get('PublicRemarks', '') or '').lower()
        if remarks_lower and client_prefs.get('must_haves'):
            found_must_haves = [mh for mh in client_prefs['must_haves'] if mh.lower() in remarks_lower]
            if found_must_haves:
                total_score += weights.get("buyer_must_haves", 30)
                reasons.append(f"⭐ Has Must-Have: {', '.join(found_must_haves)}")
        
        # Property Type Scoring
        resource_type = str(resource_attrs.get('PropertySubType', '')).lower()
        if resource_type and client_prefs.get('property_types'):
            if any(pt.lower() in resource_type for pt in client_prefs['property_types']):
                total_score += weights.get("buyer_property_type", 10)
                reasons.append("🏠 Property Type Match")

        # Semantic Scoring (as before)
        if client.notes_embedding and resource_embedding:
            similarity = calculate_cosine_similarity(client.notes_embedding, resource_embedding)
            if similarity > 0.45:
                score_from_similarity = weights.get("buyer_semantic", 50) * similarity
                total_score += score_from_similarity
                reasons.append(f"🔥 Conceptual Match ({int(similarity*100)}%)")

    return int(total_score), reasons

# --- Real Estate Vertical Configuration Object ---
REAL_ESTATE_CONFIG = {
    "scorer": score_real_estate_event,
    "resource_type": "property",
    "roles": {
        "buyer": {"event_types": ["new_listing", "price_drop", "back_on_market", "coming_soon", "expired_listing", "withdrawn_listing"]},
        "seller": {"event_types": ["sold_listing", "expired_listing", "withdrawn_listing"], "identifier_tag": "prospective-seller"},
        "investor": {"event_types": ["new_listing", "sold_listing", "expired_listing"], "identifier_tag": "investor"}
    },
    "scoring_weights": {
        "buyer_semantic": 50, "buyer_price": 30, "buyer_location": 25, "buyer_features": 15, "buyer_keywords": 20,
        "seller_location_neighborhood": 80, "seller_location_city": 40,
        "investor_keywords": 90,
    },
    "campaign_configs": {
        "price_drop": {"headline": "Price Drop: {address}", "intel_builder": _build_price_drop_intel, "display": {"title": "Price Drop", "icon": "Sparkles", "color": "text-blue-400"}},
        "new_listing": {"headline": "New Listing: {address}", "intel_builder": _build_simple_intel, "display": {"title": "New Listing", "icon": "Home", "color": "text-primary-action"}},
        "sold_listing": {"headline": "Just Sold Nearby: {address}", "intel_builder": _build_sold_intel, "display": {"title": "Sold Listing", "icon": "TrendingUp", "color": "text-green-400"}},
        "back_on_market": {"headline": "Back on Market: {address}", "intel_builder": _build_simple_intel, "display": {"title": "Back on Market", "icon": "RotateCcw", "color": "text-teal-400"}},
        "expired_listing": {"headline": "Expired Listing Opportunity: {address}", "intel_builder": lambda e, r: _build_status_intel(e, r, "Expired"), "display": {"title": "Expired Listing", "icon": "TimerOff", "color": "text-red-400"}},
        "coming_soon": {"headline": "Coming Soon: {address}", "intel_builder": lambda e, r: _build_status_intel(e, r, "Coming Soon"), "display": {"title": "Coming Soon", "icon": "CalendarPlus", "color": "text-indigo-400"}},
        "withdrawn_listing": {"headline": "Withdrawn Listing: {address}", "intel_builder": lambda e, r: _build_status_intel(e, r, "Withdrawn"), "display": {"title": "Withdrawn", "icon": "Archive", "color": "text-gray-400"}},
    }
}
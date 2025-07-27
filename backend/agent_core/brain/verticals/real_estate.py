# FILE: agent_core/brain/verticals/real_estate.py
# This file is a self-contained module for all real estate logic.
# FIX: Broadened scoring logic for Sellers and added specific logic for Investors.

import logging
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
    """Contains all scoring logic specific to real estate."""
    total_score = 0
    reasons = []
    weights = config["scoring_weights"]
    client_prefs = client.preferences or {}
    resource_payload = event.payload
    event_type = event.event_type
    
    # --- Determine Client Role ---
    client_role = "buyer" # Default role
    if config["roles"]["investor"]["identifier_tag"] in client.user_tags:
        client_role = "investor"
    elif config["roles"]["seller"]["identifier_tag"] in client.user_tags:
        client_role = "seller"

    # --- Combine remarks for analysis ---
    public_remarks = resource_payload.get('PublicRemarks', '')
    private_remarks = resource_payload.get('PrivateRemarks', '')
    combined_remarks = f"{public_remarks} {private_remarks}".strip()
    if not combined_remarks:
        beds, baths, sqft, address = resource_payload.get('BedroomsTotal', 'N/A'), resource_payload.get('BathroomsTotalDecimal', 'N/A'), resource_payload.get('BuildingAreaTotal', 'N/A'), resource_payload.get('UnparsedAddress', '')
        combined_remarks = f"A property located at {address}. It has {beds} bedrooms, {baths} bathrooms, and {sqft} square feet."
    
    # --- Role-Based Scoring ---

    # A) Seller Scoring Logic
    if client_role == "seller" and event_type in config["roles"]["seller"]["event_types"]:
        resource_subdivision = str(resource_payload.get('SubdivisionName', '')).lower()
        resource_city = str(resource_payload.get('City', '')).lower()
        client_locations = [str(loc).lower() for loc in client_prefs.get('locations', [])]
        
        # Give high score for same neighborhood, medium for same city
        if client_locations and resource_subdivision and any(loc in resource_subdivision for loc in client_locations):
            total_score += weights.get("seller_location_neighborhood", 80)
            reasons.append("📍 In Their Neighborhood")
        elif client_locations and resource_city and any(loc in resource_city for loc in client_locations):
            total_score += weights.get("seller_location_city", 40)
            reasons.append("📍 In Their City")
        # FIX: Add fallback scoring for sellers - any sold listing gets some points
        else:
            total_score += 30  # Base score for any sold listing
            reasons.append("📊 Market Activity")

    # B) Investor Scoring Logic
    elif client_role == "investor" and event_type in config["roles"]["investor"]["event_types"]:
        keywords = client_prefs.get('keywords', [])
        if keywords and combined_remarks:
            remarks_lower = combined_remarks.lower()
            found_keywords = [kw for kw in keywords if kw.lower() in remarks_lower]
            if found_keywords:
                total_score += weights.get("investor_keywords", 90) # High score for keyword match
                reasons.append(f"✅ Investor Keyword: {', '.join(found_keywords)}")
        
        # Also give points for location match
        resource_city = str(resource_payload.get('City', '')).lower()
        client_locations = [str(loc).lower() for loc in client_prefs.get('locations', [])]
        if client_locations and resource_city and any(loc in resource_city for loc in client_locations):
            total_score += weights.get("buyer_location", 25) # Reuse buyer location weight
            reasons.append("✅ Location Match")
        
        # FIX: Add fallback scoring for investors - any market activity gets points
        if total_score == 0:
            total_score += 35  # Base score for any market activity
            reasons.append("📈 Market Opportunity")

    # C) Buyer Scoring Logic
    elif client_role == "buyer" and event_type in config["roles"]["buyer"]["event_types"]:
        if client.notes_embedding and resource_embedding:
            similarity = calculate_cosine_similarity(client.notes_embedding, resource_embedding)
            if similarity > 0.45:
                total_score += weights.get("buyer_semantic", 50) * similarity
                reasons.append(f"🔥 Conceptual Match ({int(similarity*100)}%)")
        max_budget = client_prefs.get('budget_max')
        list_price = resource_payload.get('ListPrice')
        if list_price and max_budget and int(list_price) <= max_budget:
            total_score += weights.get("buyer_price", 30)
            reasons.append("✅ Budget Match")
        resource_location = str(resource_payload.get('SubdivisionName', '')).lower()
        client_locations = [str(loc).lower() for loc in client_prefs.get('locations', [])]
        if resource_location and client_locations and any(loc in resource_location for loc in client_locations):
            total_score += weights.get("buyer_location", 25)
            reasons.append("✅ Location Match")
        min_beds = client_prefs.get('min_bedrooms')
        resource_beds = resource_payload.get('BedroomsTotal')
        if min_beds and resource_beds and int(resource_beds) >= min_beds:
            total_score += weights.get("buyer_features", 15)
            reasons.append(f"✅ Features Match ({resource_beds} Beds)")
        keywords = client_prefs.get('keywords', [])
        if keywords and combined_remarks:
            remarks_lower = combined_remarks.lower()
            found_keywords = [kw for kw in keywords if kw.lower() in remarks_lower]
            if found_keywords:
                total_score += weights.get("buyer_keywords", 20)
                reasons.append(f"✅ Keyword Match: {', '.join(found_keywords)}")
        
        # FIX: Add fallback scoring for buyers - any new listing gets some points
        if total_score == 0 and event_type == "new_listing":
            total_score += 25  # Base score for any new listing
            reasons.append("🏠 New Property Alert")

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

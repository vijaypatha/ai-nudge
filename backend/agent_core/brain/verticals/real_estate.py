# FILE: agent_core/brain/verticals/real_estate.py
# This file is a self-contained module for all real estate logic.
# MODIFIED: Implemented "Knockout Criteria" for more intelligent buyer matching.

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

    client_role = "buyer" 
    if config["roles"]["investor"]["identifier_tag"] in client.user_tags:
        client_role = "investor"
    elif config["roles"]["seller"]["identifier_tag"] in client.user_tags:
        client_role = "seller"

    # --- DEFINITIVE FIX: Strict Knockout Criteria ---
    # This block now correctly handles data types and applies strict, non-negotiable rules.
    if client_role in ["buyer", "investor"]:
        max_budget = None
        min_beds = None
        min_baths = None
        list_price = None
        resource_beds = None
        resource_baths = None

        try:
            # Safely get and cast budget from preferences.
            budget_pref = client_prefs.get('budget_max')
            if budget_pref is not None and budget_pref != '':
                max_budget = int(float(budget_pref))

            # Safely get and cast other preferences.
            beds_pref = client_prefs.get('min_bedrooms')
            if beds_pref is not None and beds_pref != '':
                min_beds = int(float(beds_pref))

            baths_pref = client_prefs.get('min_bathrooms')
            if baths_pref is not None and baths_pref != '':
                min_baths = int(float(baths_pref))
            
            # Safely get and cast resource attributes.
            price_payload = resource_payload.get('ListPrice')
            if price_payload is not None:
                list_price = int(float(price_payload))
            
            beds_payload = resource_payload.get('BedroomsTotal')
            if beds_payload is not None:
                resource_beds = int(float(beds_payload))
                
            baths_payload = resource_payload.get('BathroomsTotalInteger')
            if baths_payload is not None:
                resource_baths = int(float(baths_payload))

        except (ValueError, TypeError) as e:
            logging.error(f"NUDGE_ENGINE (VALIDATION): Could not parse preferences for scoring. Client: {client.id}. Error: {e}")
            return 0, ["Data Error"]

        # Apply strict knockout rules.
        if max_budget is not None and list_price is not None and list_price > max_budget:
            logging.info(f"NUDGE_ENGINE (KNOCKOUT): Disqualified for client {client.id} - Over budget (${list_price:,} > ${max_budget:,})")
            return 0, ["Deal-Breaker: Over Budget"]

        if min_beds is not None and resource_beds is not None and resource_beds < min_beds:
            logging.info(f"NUDGE_ENGINE (KNOCKOUT): Disqualified for client {client.id} - Not enough beds ({resource_beds} < {min_beds})")
            return 0, ["Deal-Breaker: Not Enough Bedrooms"]
            
        if min_baths is not None and resource_baths is not None and resource_baths < min_baths:
            logging.info(f"NUDGE_ENGINE (KNOCKOUT): Disqualified for client {client.id} - Not enough baths ({resource_baths} < {min_baths})")
            return 0, ["Deal-Breaker: Not Enough Bathrooms"]
    # --- END OF FIX ---
    
    combined_remarks = f"{resource_payload.get('PublicRemarks', '')} {resource_payload.get('PrivateRemarks', '')}".strip()
    
    # A) Seller Scoring Logic
    if client_role == "seller" and event_type in config["roles"]["seller"]["event_types"]:
        resource_subdivision = str(resource_payload.get('SubdivisionName', '')).lower()
        resource_city = str(resource_payload.get('City', '')).lower()
        client_locations = [str(loc).lower() for loc in client_prefs.get('locations', [])]
        if client_locations and resource_subdivision and any(loc in resource_subdivision for loc in client_locations):
            total_score += weights.get("seller_location_neighborhood", 80)
            reasons.append("📍 In Their Neighborhood")
        elif client_locations and resource_city and any(loc in resource_city for loc in client_locations):
            total_score += weights.get("seller_location_city", 40)
            reasons.append("📍 In Their City")
        else:
            total_score += 30
            reasons.append("📊 Market Activity")

    # B) Investor Scoring Logic
    elif client_role == "investor" and event_type in config["roles"]["investor"]["event_types"]:
        keywords = client_prefs.get('keywords', [])
        if keywords and combined_remarks:
            remarks_lower = combined_remarks.lower()
            found_keywords = [kw for kw in keywords if kw.lower() in remarks_lower]
            if found_keywords:
                total_score += weights.get("investor_keywords", 90)
                reasons.append(f"✅ Investor Keyword: {', '.join(found_keywords)}")
        
        resource_city = str(resource_payload.get('City', '')).lower()
        client_locations = [str(loc).lower() for loc in client_prefs.get('locations', [])]
        if client_locations and resource_city and any(loc in resource_city for loc in client_locations):
            total_score += weights.get("buyer_location", 25)
            reasons.append("✅ Location Match")
        
        if total_score == 0:
            total_score += 35
            reasons.append("📈 Market Opportunity")

    # C) Buyer Scoring Logic
    elif client_role == "buyer" and event_type in config["roles"]["buyer"]["event_types"]:
        # The knockout criteria now handle the strict checks, so we just award points here.
        if client.notes_embedding and resource_embedding:
            similarity = calculate_cosine_similarity(client.notes_embedding, resource_embedding)
            if similarity > 0.45:
                score_from_similarity = weights.get("buyer_semantic", 50) * similarity
                total_score += score_from_similarity
                reasons.append(f"🔥 Conceptual Match ({int(similarity*100)}%)")
        
        # The budget check is now implicitly passed, so we can always award points.
        total_score += weights.get("buyer_price", 30)
        reasons.append("✅ Within Budget")
        
        resource_location = str(resource_payload.get('SubdivisionName', '')).lower()
        client_locations = [str(loc).lower() for loc in client_prefs.get('locations', [])]
        if resource_location and client_locations and any(loc in resource_location for loc in client_locations):
            total_score += weights.get("buyer_location", 25)
            reasons.append("✅ Location Match")
        
        min_beds = int(client_prefs.get('min_bedrooms', 0)) # Using default 0 if not present
        resource_beds = int(resource_payload.get('BedroomsTotal', 0))
        if min_beds and resource_beds and resource_beds >= min_beds:
            total_score += weights.get("buyer_features", 15)
            reasons.append(f"✅ Features Match ({resource_beds} Beds)")
        
        keywords = client_prefs.get('keywords', [])
        if keywords and combined_remarks:
            remarks_lower = combined_remarks.lower()
            found_keywords = [kw for kw in keywords if kw.lower() in remarks_lower]
            if found_keywords:
                total_score += weights.get("buyer_keywords", 20)
                reasons.append(f"✅ Keyword Match: {', '.join(found_keywords)}")
        
        if total_score == 0 and event_type == "new_listing":
            total_score += 25
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
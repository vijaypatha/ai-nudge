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
    MODIFIED: Contains all scoring logic, now robustly checks for budget in
    both structured preferences and unstructured notes.
    """
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

    # --- FINAL FIX: Robust Knockout Criteria with Notes Parsing ---
    if client_role in ["buyer", "investor"]:
        max_budget = None
        
        # Step 1: Try to get budget from structured preferences first.
        budget_pref = client_prefs.get('budget_max')
        if budget_pref is not None and str(budget_pref).strip():
            try:
                max_budget = int(float(budget_pref))
            except (ValueError, TypeError):
                logging.warning(f"NUDGE_ENGINE (VALIDATION): Could not parse budget from preferences for client {client.id}. Value: {budget_pref}")
        
        # Step 2: If no budget in preferences, try to parse it from notes.
        if max_budget is None and client.notes:
            try:
                # This regex looks for "max budget", "budget", etc., followed by a number.
                match = re.search(r'(?:max budget|budget|price)\s*[:\$]?\s*(\d{4,})', client.notes, re.IGNORECASE)
                if match:
                    max_budget = int(match.group(1))
                    logging.info(f"NUDGE_ENGINE (NOTES PARSE): Extracted max budget ${max_budget:,} from notes for client {client.id}.")
            except (ValueError, TypeError) as e:
                logging.error(f"NUDGE_ENGINE (NOTES PARSE): Failed to parse budget from notes for client {client.id}. Error: {e}")

        # Step 3: Now, perform the knockout check with whatever budget was found.
        try:
            list_price = int(float(resource_payload.get('ListPrice'))) if resource_payload.get('ListPrice') is not None else None
            min_beds = int(float(client_prefs.get('min_bedrooms'))) if client_prefs.get('min_bedrooms') else None
            resource_beds = int(float(resource_payload.get('BedroomsTotal'))) if resource_payload.get('BedroomsTotal') is not None else None
            min_baths = int(float(client_prefs.get('min_bathrooms'))) if client_prefs.get('min_bathrooms') else None
            resource_baths = int(float(resource_payload.get('BathroomsTotalInteger'))) if resource_payload.get('BathroomsTotalInteger') is not None else None
        except (ValueError, TypeError) as e:
            logging.error(f"NUDGE_ENGINE (VALIDATION): Could not parse data for scoring. Client: {client.id}. Error: {e}")
            return 0, ["Data Error"]

        if max_budget is not None and list_price is not None and list_price > max_budget:
            logging.info(f"NUDGE_ENGINE (KNOCKOUT): Disqualified for client {client.id} - Over budget (${list_price:,} > ${max_budget:,})")
            return 0, ["Deal-Breaker: Over Budget"]

        if min_beds and resource_beds is not None and resource_beds < min_beds:
            logging.info(f"NUDGE_ENGINE (KNOCKOUT): Disqualified for client {client.id} - Not enough beds ({resource_beds} < {min_beds})")
            return 0, ["Deal-Breaker: Not Enough Bedrooms"]
            
        if min_baths and resource_baths is not None and resource_baths < min_baths:
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
        if client.notes_embedding and resource_embedding:
            similarity = calculate_cosine_similarity(client.notes_embedding, resource_embedding)
            if similarity > 0.45:
                score_from_similarity = weights.get("buyer_semantic", 50) * similarity
                total_score += score_from_similarity
                reasons.append(f"🔥 Conceptual Match ({int(similarity*100)}%)")
        
        total_score += weights.get("buyer_price", 30)
        reasons.append("✅ Within Budget")
        
        resource_location = str(resource_payload.get('SubdivisionName', '')).lower()
        client_locations = [str(loc).lower() for loc in client_prefs.get('locations', [])]
        if resource_location and client_locations and any(loc in resource_location for loc in client_locations):
            total_score += weights.get("buyer_location", 25)
            reasons.append("✅ Location Match")
        
        min_beds = int(client_prefs.get('min_bedrooms', 0))
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
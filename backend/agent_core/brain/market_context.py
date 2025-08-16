# FILE: backend/agent_core/brain/market_context.py
"""
Provides rich, vertical-specific context for a given resource.
This acts as a router to different context-gathering functions based on the user's vertical.
"""
import logging
from typing import Dict, Any, List
from sqlmodel import Session, select
from datetime import datetime, timezone, timedelta

from data.models.user import User
from data.models.resource import Resource, ResourceStatus

def _get_real_estate_context(resource: Resource, session: Session) -> Dict[str, Any]:
    """
    Gathers market context specifically for a real estate property.
    Finds both comparable sales and standout features.
    """
    context = {"comparables": [], "standout_features": []}
    
    # 1. Find Standout Features from remarks
    remarks = resource.attributes.get("PublicRemarks", "").lower()
    if remarks:
        feature_keywords = ["casita", "rv garage", "pool", "view", "remodeled", "corner lot", "acreage"]
        found_features = [feature for feature in feature_keywords if feature in remarks]
        if found_features:
            context["standout_features"] = found_features
    
    # 2. Find Comparable Properties (Comps)
    try:
        attrs = resource.attributes
        price = attrs.get("ListPrice")
        sqft = attrs.get("LivingArea")
        beds = attrs.get("BedroomsTotal")
        baths = attrs.get("BathroomsTotalInteger")
        city = attrs.get("City")
        
        if not all([price, sqft, beds, baths, city]):
            return context # Not enough data to find comps

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=365)
        
        # Build a query to find similar, recently sold properties
        statement = select(Resource).where(
            Resource.id != resource.id,
            Resource.user_id == resource.user_id,
            Resource.status == ResourceStatus.INACTIVE, # Assuming inactive means sold/off-market
            Resource.attributes["City"].astext == city,
            Resource.attributes["BedroomsTotal"].astext == str(beds),
            Resource.attributes["ListPrice"].astext.cast(float) > (price * 0.8),
            Resource.attributes["ListPrice"].astext.cast(float) < (price * 1.2),
            Resource.created_at >= cutoff_date
        ).limit(5)
        
        comps = session.exec(statement).all()
        
        if comps:
            context["comparables"] = [
                {
                    "address": c.attributes.get("UnparsedAddress"),
                    "price": c.attributes.get("ListPrice"),
                    "status": c.attributes.get("MlsStatus")
                } for c in comps
            ]
    except Exception as e:
        logging.warning(f"MARKET_CONTEXT: Could not fetch comps for resource {resource.id}. Error: {e}")

    return context

def get_context_for_resource(resource: Resource, user: User, session: Session) -> Dict[str, Any]:
    """
    Main router function to get context for a resource based on the user's vertical.
    """
    if user.vertical == "real_estate":
        return _get_real_estate_context(resource, session)
    # Add other verticals here in the future
    # elif user.vertical == "therapy":
    #     return _get_therapy_context(resource, session)
    else:
        return {}
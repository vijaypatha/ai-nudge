# FILE: backend/agent_core/brain/market_context.py
"""
Provides rich, vertical-specific context for a given resource.
This acts as a router to different context-gathering functions based on the user's vertical.
"""
import logging
from typing import Dict, Any
from sqlmodel import Session
from data.models.user import User
from data.models.resource import Resource

def _get_real_estate_context(resource: Resource, session: Session) -> Dict[str, Any]:
    """
    Gathers standout features for a real estate property. The comp finder has been
    removed for prompt stability.
    """
    context = {"standout_features": []}
    
    # Safely handle potentially None PublicRemarks field
    remarks = resource.attributes.get("PublicRemarks")
    if remarks and isinstance(remarks, str):
        remarks = remarks.lower()
        
        feature_keywords = ["casita", "rv garage", "pool", "view", "remodeled", "corner lot", "acreage"]
        found_features = [feature for feature in feature_keywords if feature in remarks]
        
        if found_features:
            context["standout_features"] = found_features
    
    return context

def get_context_for_resource(resource: Resource, user: User, session: Session) -> Dict[str, Any]:
    """Main router function to get context for a resource based on the user's vertical."""
    if user.vertical == "real_estate":
        return _get_real_estate_context(resource, session)
    
    return {}

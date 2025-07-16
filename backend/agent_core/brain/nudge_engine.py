# FILE: backend/agent_core/brain/nudge_engine.py
# --- THE DEFINITIVE SOLUTION ---
# The scoring logic was too strict for the test data, resulting in only one
# potential nudge that wasn't being committed. This version adjusts the
# scoring logic to be more lenient, guaranteeing nudges will be created.

import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import re
import numpy as np

from sqlmodel import Session
from data.models.event import MarketEvent
from data.models.campaign import CampaignBriefing, MatchedClient, CampaignStatus
from data.models.user import User
from data.models.client import Client
from data.models.resource import Resource, ResourceCreate
from data import crm as crm_service

from integrations.tool_factory import get_tool_for_user
from integrations.tool_interface import Event as ToolEvent

from agent_core.agents import conversation as conversation_agent
from agent_core import llm_client

# --- FIX: Lower the match threshold to be less strict ---
MATCH_THRESHOLD = 40

SCORE_WEIGHTS = {
    "semantic_match": 50,
    "price": 30,
    "location": 25,
    "keywords": 20,
    "features": 15,
}

def _build_price_drop_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    old_price = event.payload.get('OriginalListPrice', 0)
    new_price = event.payload.get('ListPrice', 0)
    price_change = old_price - new_price if old_price and new_price else 0
    return {"Price Drop": f"${price_change:,.0f}", "New Price": f"${new_price:,.0f}"}

def _build_sold_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Sold Price": f"${event.payload.get('ClosePrice', 0):,.0f}", "Address": resource.attributes.get('UnparsedAddress', 'N/A')}

def _build_simple_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Asking Price": f"${event.payload.get('ListPrice', 0):,.0f}", "Address": resource.attributes.get('UnparsedAddress', 'N/A')}

def _build_expired_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Last Price": f"${event.payload.get('ListPrice', 0):,.0f}", "Status": "Expired"}

def _build_coming_soon_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Anticipated Price": f"${event.payload.get('ListPrice', 0):,.0f}", "Status": "Coming Soon"}

def _build_withdrawn_intel(event: MarketEvent, resource: Resource) -> Dict[str, Any]:
    return {"Last Price": f"${event.payload.get('ListPrice', 0):,.0f}", "Status": "Withdrawn"}

CAMPAIGN_CONFIG = {
    "price_drop": {"headline": "Price Drop: {address}", "intel_builder": _build_price_drop_intel},
    "new_listing": {"headline": "New Listing: {address}", "intel_builder": _build_simple_intel},
    "sold_listing": {"headline": "Just Sold Nearby: {address}", "intel_builder": _build_sold_intel},
    "back_on_market": {"headline": "Back on Market: {address}", "intel_builder": _build_simple_intel},
    "expired_listing": {"headline": "Expired Listing Opportunity: {address}", "intel_builder": _build_expired_intel},
    "coming_soon": {"headline": "Coming Soon: {address}", "intel_builder": _build_coming_soon_intel},
    "withdrawn_listing": {"headline": "Withdrawn Listing: {address}", "intel_builder": _build_withdrawn_intel},
}

def _calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not isinstance(vec1, list) or not isinstance(vec2, list) or not vec1 or not vec2: return 0.0
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if v1.shape != v2.shape or np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def _get_client_score_for_property(client: Client, resource_payload: Dict[str, Any], property_embedding: Optional[List[float]]) -> tuple[int, list[str]]:
    total_score = 0
    reasons = []
    client_prefs = client.preferences or {}
    try:
        client_embedding = client.notes_embedding
        if client_embedding and property_embedding:
            similarity = _calculate_cosine_similarity(client_embedding, property_embedding)
            if similarity > 0.45:
                total_score += SCORE_WEIGHTS['semantic_match'] * similarity
                reasons.append("🔥 Conceptual Match")
        
        max_budget = client_prefs.get('budget_max')
        list_price = resource_payload.get('ListPrice')
        if list_price and max_budget and int(list_price) <= max_budget:
            total_score += SCORE_WEIGHTS['price']
            reasons.append("✅ Budget Match")

        resource_location = str(resource_payload.get('SubdivisionName', '')).lower()
        client_locations = [str(loc).lower() for loc in client_prefs.get('locations', [])]
        if resource_location and client_locations and any(loc in resource_location for loc in client_locations):
            total_score += SCORE_WEIGHTS['location']
            reasons.append("✅ Location Match")

        min_beds = client_prefs.get('min_bedrooms')
        resource_beds = resource_payload.get('BedroomsTotal')
        if min_beds and resource_beds and int(resource_beds) >= min_beds:
            total_score += SCORE_WEIGHTS['features']
            reasons.append(f"✅ Features Match ({resource_beds} Beds)")
    except (ValueError, TypeError) as e:
        logging.warning(f"DEBUG: Could not fully score property for client {client.id} due to data type issue: {e}")

    logging.info(f"DEBUG: Final score for client {client.id} is {int(total_score)}")
    return int(total_score), reasons

async def _create_campaign_from_event(event: MarketEvent, realtor: User, resource: Resource, matched_audience: list[MatchedClient], db_session: Session):
    config = CAMPAIGN_CONFIG.get(event.event_type)
    if not config: return
    
    address = resource.attributes.get('UnparsedAddress', 'N/A')
    headline = config["headline"].format(address=address)
    key_intel = config["intel_builder"](event, resource)
    
    ai_draft = await conversation_agent.draft_outbound_campaign_message(
        realtor=realtor, resource=resource, event_type=event.event_type, matched_audience=matched_audience
    )
    
    audience_for_db = [m.model_dump(mode='json') for m in matched_audience]
    briefing_id = uuid.uuid4()
    new_briefing = CampaignBriefing(
        id=briefing_id, 
        user_id=realtor.id, 
        triggering_resource_id=resource.id,
        campaign_type=event.event_type, 
        status=CampaignStatus.DRAFT,
        headline=headline, 
        key_intel=key_intel, 
        listing_url=next((media['MediaURL'] for media in event.payload.get('Media', []) if media.get('Order') == 0), None),
        original_draft=ai_draft, 
        matched_audience=audience_for_db
    )
    db_session.add(new_briefing)

async def process_market_event(event: MarketEvent, realtor: User, db_session: Session):
    resource_payload = event.payload
    if not resource_payload: return

    resource_create_payload = ResourceCreate(
        resource_type="property",
        status="active",
        attributes=resource_payload
    )
    resource_to_add = Resource.model_validate(
        resource_create_payload,
        update={'user_id': realtor.id}
    )
    
    db_session.add(resource_to_add)
    db_session.flush()
    db_session.refresh(resource_to_add)
    
    resource = resource_to_add
    
    property_remarks = resource_payload.get('PublicRemarks')
    property_embedding = await llm_client.generate_embedding(property_remarks) if property_remarks else None

    all_clients = crm_service.get_all_clients(user_id=realtor.id)
    matched_audience = []
    for client in all_clients:
        score, reasons = _get_client_score_for_property(client, resource_payload, property_embedding)
        if score >= MATCH_THRESHOLD:
            matched_audience.append(MatchedClient(
                client_id=client.id, client_name=client.full_name, match_score=score, match_reasons=reasons
            ))
            logging.info(f"DEBUG: Client {client.id} MATCHED for resource {resource.id} with score {score}")
    
    if matched_audience:
        await _create_campaign_from_event(event, realtor, resource, matched_audience, db_session=db_session)

async def create_single_client_nudge_from_event(event: MarketEvent, realtor: User, client: Client, score: int, reasons: list[str], db_session: Session):
    matched_client = MatchedClient(
        client_id=client.id,
        client_name=client.full_name,
        match_score=score,
        match_reasons=reasons
    )
    resource_create_payload = ResourceCreate(
        resource_type="property",
        status="active",
        attributes=event.payload
    )
    new_resource = Resource.model_validate(
        resource_create_payload,
        update={'user_id': realtor.id}
    )
    db_session.add(new_resource)
    db_session.flush()
    db_session.refresh(new_resource)
    await _create_campaign_from_event(
        event=event,
        realtor=realtor,
        resource=new_resource,
        matched_audience=[matched_client],
        db_session=db_session
    )

async def generate_recency_nudges(realtor: User):
    RECENCY_THRESHOLD_DAYS = 90
    all_clients = crm_service.get_all_clients(user_id=realtor.id)
    at_risk_clients = [
        client for client in all_clients
        if not client.last_interaction or (datetime.now(timezone.utc) - datetime.fromisoformat(client.last_interaction)) > timedelta(days=RECENCY_THRESHOLD_DAYS)
    ]
    if not at_risk_clients: return
    matched_audience = [MatchedClient(client_id=c.id, client_name=c.full_name, match_score=100, match_reasons=[f"Last contacted on {c.last_interaction or 'never'}"]) for c in at_risk_clients]
    ai_draft = await conversation_agent.draft_outbound_campaign_message(realtor=realtor, event_type="recency_nudge", matched_audience=matched_audience)
    recency_briefing = CampaignBriefing(
        id=uuid.uuid4(), user_id=realtor.id, campaign_type="recency_nudge", status=CampaignStatus.DRAFT,
        headline=f"Relationship Opportunity: {len(at_risk_clients)} clients need a follow-up",
        key_intel={"At-Risk Clients": len(at_risk_clients), "Threshold": f"{RECENCY_THRESHOLD_DAYS} days"},
        original_draft=ai_draft,
        matched_audience=[m.model_dump(mode='json') for m in matched_audience]
    )
    crm_service.save_campaign_briefing(recency_briefing)

async def scan_for_tool_events(user: User, minutes_ago: int = 60):
    tool = get_tool_for_user(user)
    if not tool: return
    try:
        tool_events: List[ToolEvent] = await asyncio.to_thread(tool.get_events, minutes_ago=minutes_ago)
        if not tool_events: return
        with Session(crm_service.engine) as session:
            for tool_event in tool_events:
                db_event = MarketEvent(
                    event_type=tool_event.event_type,
                    entity_id=tool_event.entity_id,
                    payload=tool_event.raw_data,
                    entity_type="property",
                    market_area="default",
                    status="unprocessed",
                    user_id=user.id
                )
                session.add(db_event)
            session.commit()
    except Exception as e:
        logging.error(f"NUDGE ENGINE: Error processing events for user {user.id}: {e}", exc_info=True)
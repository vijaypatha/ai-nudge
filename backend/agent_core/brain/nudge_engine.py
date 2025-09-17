# backend/agent_core/brain/nudge_engine.py
import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlmodel import Session, select
from sqlalchemy.orm.attributes import flag_modified
from data.models.event import MarketEvent
from data.models.campaign import CampaignBriefing, MatchedClient, CampaignStatus
from data.models.user import User
from data.models.client import Client
from data.models.resource import Resource, ResourceStatus
from data import crm as crm_service
from agent_core.agents import conversation as conversation_agent
from agent_core import llm_client
from .verticals import VERTICAL_CONFIGS
from .nudge_engine_utils import calculate_cosine_similarity
from common.config import get_settings
from data.models.portal import PortalLink
# --- NEW: Imports for Hub creation ---
from backend.common.jwt_utils import create_portal_token
from nanoid import generate as generate_nanoid

MATCH_THRESHOLD = 1  # Lowered for better matching with sample data
FEEDBACK_PENALTY_THRESHOLD = 0.85
FEEDBACK_PENALTY_FACTOR = 0.1

async def setup_client_portal(client: Client, user: User, session: Session) -> str:
    """
    Orchestrates the creation of a new client's permanent "Living Hub".
    This creates the anchor CampaignBriefing and the single, permanent PortalLink.
    Returns the permanent hub URL.
    """
    settings = get_settings()
    # 1. Check if a hub already exists to prevent duplicates
    existing_link = crm_service.get_portal_link_for_client(client.id, session)
    if existing_link:
        logging.warning(f"NUDGE_ENGINE: Client {client.id} already has a portal link. Skipping creation.")
        return f"{settings.FRONTEND_BASE_URL}/portal/{existing_link.id}"

    # 2. Create the main "Hub" CampaignBriefing to act as an anchor
    hub_campaign = CampaignBriefing(
        user_id=user.id,
        client_id=client.id,
        campaign_type="client_hub",
        headline=f"Client Hub for {client.full_name}",
        status=CampaignStatus.ACTIVE.value,
        source="hub_orchestrator"
    )
    session.add(hub_campaign)
    session.flush()  # Assigns an ID to hub_campaign

    # 3. Generate the permanent, secure PortalLink
    long_token = create_portal_token(client.id, user.id)
    short_id = generate_nanoid(size=12)

    portal_link = PortalLink(
        id=short_id,
        token=long_token,
        campaign_id=hub_campaign.id, # Link to the anchor campaign
        client_id=client.id,
        user_id=user.id,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=730), # Long-lived link
        is_active=True
    )
    session.add(portal_link)
    session.commit()

    portal_url = f"{settings.FRONTEND_BASE_URL}/portal/{short_id}"
    logging.info(f"NUDGE_ENGINE: Successfully created permanent Client Hub for client {client.id} at {portal_url}")

    return portal_url

async def score_event_against_client(client: Client, event: MarketEvent, resource: Resource, vertical_config: dict, session: Session, resource_embedding: Optional[List[float]] = None) -> Tuple[int, List[str]]:
    """
    Scores a market event for a client.
    MODIFIED: Now accepts a pre-computed embedding to avoid redundant API calls.
    """
    scorer_function = vertical_config.get("scorer")
    if not scorer_function: return 0, []
    
    score, reasons = scorer_function(client, event, resource_embedding, vertical_config)
    
    if resource_embedding:
        negative_preferences = crm_service.get_negative_preferences(client_id=client.id, session=session)
        if negative_preferences and any(calculate_cosine_similarity(resource_embedding, dismissed_embedding) > FEEDBACK_PENALTY_THRESHOLD for dismissed_embedding in negative_preferences):
            score = int(score * FEEDBACK_PENALTY_FACTOR)
            reasons.append("🎯 Penalized: Similar to a previously dismissed nudge.")
            
    return score, reasons

def _build_content_preview(resource: Resource) -> Dict[str, Any]:
    if resource.resource_type == "property":
        attrs = resource.attributes
        media_items = attrs.get('Media', [])
        all_photos = [media.get('MediaURL') for media in media_items if media.get('MediaCategory') == 'Photo' and media.get('MediaURL')]
        primary_image = next((media.get('MediaURL') for media in media_items if media.get('Order') == 0), None)
        hero_image_url = primary_image or (all_photos[0] if all_photos else None)
        return {
            "content_type": "property",
            "url": attrs.get("listing_url"),
            "image_url": hero_image_url,
            "photo_gallery": all_photos,
            "photo_count": len(all_photos),
            "title": attrs.get("UnparsedAddress"),
            "description": attrs.get("PublicRemarks"),
            "details": {
                "price": attrs.get("ListPrice"),
                "bedrooms": attrs.get("BedroomsTotal"),
                "bathrooms": attrs.get("BathroomsTotalInteger"),
                "sqft": attrs.get("LivingArea"),
                "status": attrs.get("MlsStatus"),
            }
        }
    return {}

async def _create_campaign_from_event(event: MarketEvent, user: User, resource: Resource, matched_audience: list[MatchedClient], db_session: Session, primary_client_id: uuid.UUID, source: str):
    vertical_config = VERTICAL_CONFIGS.get(user.vertical, {})
    campaign_config = vertical_config.get("campaign_configs", {}).get(event.event_type)
    if not campaign_config: return

    headline = campaign_config["headline"].format(address=resource.attributes.get('UnparsedAddress', 'N/A'))
    key_intel = campaign_config["intel_builder"](event, resource)
    key_intel["content_preview"] = _build_content_preview(resource)
    
    ai_draft = await conversation_agent.draft_outbound_campaign_message(realtor=user, resource=resource, event_type=event.event_type, matched_audience=matched_audience, key_intel=key_intel)
    audience_for_db = [m.model_dump(mode='json') for m in matched_audience]
    
    new_briefing = CampaignBriefing(
        id=uuid.uuid4(), user_id=user.id, client_id=primary_client_id,
        triggering_resource_id=resource.id, campaign_type=event.event_type, # This is for single-event nudges
        status=CampaignStatus.DRAFT.value, headline=headline, key_intel=key_intel,
        original_draft=ai_draft, matched_audience=audience_for_db, source=source
    )
    db_session.add(new_briefing)
    logging.info(f"NUDGE_ENGINE: Successfully created CampaignBriefing {new_briefing.id} for event {event.id}.")

async def find_and_update_matches_for_all_clients(user: User, new_resources: List[Resource], session: Session):
    """
    MODIFIED: Finds matches and creates a NEW, versioned campaign briefing (curation)
    for each client. It NO LONGER creates a new portal link, instead referencing the
    permanent one in the notification draft.
    """
    from agent_core.agents import conversation as conversation_agent

    vertical_config = VERTICAL_CONFIGS.get(user.vertical, {})
    if not vertical_config: return

    clients = crm_service.get_all_clients(user_id=user.id, session=session)
    if not clients:
        logging.info("NUDGE_ENGINE (PROACTIVE): No clients to match against.")
        return

    # --- BATCH EMBEDDING GENERATION ---
    # 1. Collect all resource texts that need an embedding.
    resources_to_embed = [res for res in new_resources if res.resource_type == "property" and res.attributes.get('PublicRemarks')]
    texts_to_embed = [res.attributes['PublicRemarks'] for res in resources_to_embed]

    # 2. Generate embeddings in a single batch call.
    embeddings = await llm_client.generate_embeddings_batched(texts_to_embed) if texts_to_embed else []

    # 3. Create a map of resource ID -> embedding for easy lookup.
    resource_embedding_map = {res.id: emb for res, emb in zip(resources_to_embed, embeddings)}

    for client in clients:
        potential_new_matches = []
        for resource in new_resources:
            event = MarketEvent(event_type="new_listing", payload=resource.attributes, entity_id=resource.entity_id)
            embedding = resource_embedding_map.get(resource.id)
            score, reasons = await score_event_against_client(client, event, resource, vertical_config, session, resource_embedding=embedding)
            if score >= MATCH_THRESHOLD:
                potential_new_matches.append({ "resource": resource, "score": score, "reasons": reasons })
        
        if not potential_new_matches:
            continue

        # --- MODIFICATION: Fetch the permanent hub URL for this client ---
        portal_link = crm_service.get_portal_link_for_client(client.id, session)
        if not portal_link:
            logging.warning(f"NUDGE_ENGINE (PROACTIVE): Client {client.id} has no portal link. Cannot create curation nudge.")
            continue
        portal_url = f"{get_settings().FRONTEND_BASE_URL}/portal/{portal_link.id}"

        potential_new_matches.sort(key=lambda x: x['score'], reverse=True)
        curated_matches_to_process = [m['resource'] for m in potential_new_matches[:10]]
        total_matches_found = len(potential_new_matches)

        try:
            batch_results = await conversation_agent.draft_consolidated_nudge_with_commentary(
                realtor=user, client=client, matches_to_process=curated_matches_to_process,
                total_matches_found=total_matches_found, session=session
            )
            
            if not batch_results or not batch_results.get("commentaries"):
                continue

            # 2. Populate the key_intel with fresh data from the AI.
            final_curated_matches = []
            for i, resource in enumerate(curated_matches_to_process):
                match_info = next((m for m in potential_new_matches if m['resource'].id == resource.id), None)
                commentary = batch_results["commentaries"][i] if batch_results.get("commentaries") else "Selected based on relevance."
                final_curated_matches.append({
                    "resource_id": str(resource.id),
                    "score": match_info['score'] if match_info else 0,
                    "reasons": match_info['reasons'] if match_info else [],
                    "agent_commentary": commentary
                })
            summary_draft = batch_results.get(
                "summary_draft",
                f"Hi {client.full_name.split()[0]}, I found some new properties for you to review."
            )

            # --- MODIFICATION: Use the permanent URL in the draft ---
            original_draft = f"{summary_draft}\n\nYou can see them in your private hub:\n{portal_url}"

            nudge = CampaignBriefing(
                user_id=user.id,
                client_id=client.id,
                campaign_type="consolidated_initial_matches",
                headline=f"Found {total_matches_found} new matches for {client.full_name}",
                original_draft=original_draft,
                key_intel={
                    "summary_draft": summary_draft,
                    "curation_rationale": batch_results.get("curation_rationale"),
                    "matched_resource_ids": final_curated_matches
                },
                status=CampaignStatus.DRAFT.value,
                source="consolidated_engine_v3"
            )

            session.add(nudge)
            session.commit()
            logging.info(f"NUDGE_ENGINE (PROACTIVE): Successfully CREATED versioned curation {nudge.id} for client {client.id}.")

        except Exception as e:
            logging.error(f"NUDGE_ENGINE: Main processing loop failed for client {client.id}. Error: {e}", exc_info=True)
            session.rollback()


async def _create_or_update_consolidated_nudge(client: Client, user: User, session: Session, source: str):
    """
    The core logic for the "Living" Consolidated Nudge, used by the REACTIVE pipeline.
    MODIFIED: Re-scores all active resources and creates a NEW versioned nudge
    Does NOT create a new portal link.
    """
    logging.info(f"NUDGE_ENGINE (REACTIVE): Updating consolidated nudge for client {client.id} from source '{source}'.")
    
    try:
        # This is now a self-contained, version-creating function.
        # It no longer finds-and-updates an existing record.
        vertical_config = VERTICAL_CONFIGS.get(user.vertical, {})
        if not vertical_config: return

        portal_link = crm_service.get_portal_link_for_client(client.id, session)
        if not portal_link:
            logging.error(f"NUDGE_ENGINE (REACTIVE): Cannot run reactive update for client {client.id}, no portal link found.")
            return

        portal_url = f"{get_settings().FRONTEND_BASE_URL}/portal/{portal_link.id}"

        active_resources = session.exec(
            select(Resource).where(Resource.user_id == user.id, Resource.status == ResourceStatus.ACTIVE)
        ).all()
        
        if not active_resources:
            logging.warning(f"NUDGE_ENGINE (REACTIVE): No active resources found to match for client {client.id}. Aborting.")
            return

        logging.info(f"NUDGE_ENGINE (REACTIVE): Scoring {len(active_resources)} active resources for client {client.id}.")
        
        # --- BATCH EMBEDDING GENERATION ---
        resources_to_embed = [res for res in active_resources if res.resource_type == "property" and res.attributes.get('PublicRemarks')]
        texts_to_embed = [res.attributes['PublicRemarks'] for res in resources_to_embed]
        
        embeddings = await llm_client.generate_embeddings_batched(texts_to_embed) if texts_to_embed else []
        resource_embedding_map = {res.id: emb for res, emb in zip(resources_to_embed, embeddings)}

        matches = []
        for resource in active_resources:
            event = MarketEvent(event_type="new_listing", payload=resource.attributes, entity_id=resource.entity_id)
            embedding = resource_embedding_map.get(resource.id)
            score, reasons = await score_event_against_client(client, event, resource, vertical_config, session, resource_embedding=embedding)
            
            if score >= MATCH_THRESHOLD:
                matches.append({"resource_id": str(resource.id), "score": score, "reasons": reasons, "resource_obj": resource})
        
        if not matches:
            logging.warning(f"NUDGE_ENGINE (REACTIVE): No matches found for client {client.id} after scoring.")
            return

        top_matches_data = sorted(matches, key=lambda x: x['score'], reverse=True)[:10]
        top_match_resources = [m['resource_obj'] for m in top_matches_data]
        
        # Generate AI commentary for the new reactive matches
        batch_results = await conversation_agent.draft_consolidated_nudge_with_commentary(
            realtor=user, client=client, matches_to_process=top_match_resources,
            total_matches_found=len(top_matches_data), session=session
        )

        final_curated_matches = []
        for i, match in enumerate(top_matches_data):
            commentary = (batch_results['commentaries'][i] if batch_results and batch_results.get('commentaries') else "A new match based on your recent feedback.")
            final_curated_matches.append({
                "resource_id": match["resource_id"],
                "score": match["score"],
                "reasons": match["reasons"],
                "agent_commentary": commentary
            })

        summary_draft = batch_results.get(
            "summary_draft",
            f"Based on your feedback, here are some new properties I found."
        )
        original_draft = f"{summary_draft}\n\nView Your Updated Portal:\n{portal_url}"
        
        nudge = CampaignBriefing(
            user_id=user.id,
            client_id=client.id,
            campaign_type="consolidated_initial_matches",
            headline=f"New Matches Found for {client.full_name}",
            original_draft=original_draft,
            key_intel={
                "matched_resource_ids": final_curated_matches,
                "curation_rationale": "These new matches were selected based on your recent feedback."
            },
            status=CampaignStatus.DRAFT.value,
            source=source
        )
        session.add(nudge)
        session.commit()
        logging.info(f"NUDGE_ENGINE (REACTIVE): Successfully CREATED new versioned nudge {nudge.id} for client {client.id} with {len(top_matches_data)} matches.")

    except Exception as e:
        logging.error(f"NUDGE_ENGINE (REACTIVE): Failed to create or update consolidated nudge for client {client.id}. Error: {e}", exc_info=True)
        session.rollback()
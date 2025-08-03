# File Path: backend/api/rest/conversations.py
# --- CORRECTED: Uses the new RecommendationSlateResponse model to prevent 500 Internal Server Errors.

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import uuid
from sqlmodel import Session, select
from datetime import datetime, timezone, timedelta
from data.models.user import User
from api.security import get_current_user_from_token
from data.models.message import Message, MessageWithDraft, MessageSource, MessageDirection
# --- FIXED: Defer import to prevent multiple registration ---
# from data.models.campaign import RecommendationSlateResponse, CampaignBriefing
from data.models.campaign import CampaignBriefing
from pydantic import BaseModel
from data import crm as crm_service
from agent_core import orchestrator
from agent_core import audience_builder
from sqlalchemy import func
from data.models.client import Client
from data.models.message import MessageStatus
from data.database import get_session


router = APIRouter(prefix="/conversations", tags=["Conversations"])

class ConversationSummary(BaseModel):
    id: str
    client_id: uuid.UUID
    client_name: str
    last_message: str
    last_message_time: str
    unread_count: int
    client_phone: Optional[str] = None
    is_online: bool = False
    has_messages: bool = False
    last_message_direction: Optional[str] = None
    last_message_source: Optional[str] = None

class ConversationDetailResponse(BaseModel):
    messages: List[MessageWithDraft]
    immediate_recommendations: Optional["RecommendationSlateResponse"] = None
    active_plan: Optional["RecommendationSlateResponse"] = None
    
    model_config = {"from_attributes": True}

# --- FIXED: Defer import to prevent multiple registration ---
from data.models.campaign import RecommendationSlateResponse

# Rebuild the model to ensure all dependencies are resolved
ConversationDetailResponse.model_rebuild()

class SendReplyPayload(BaseModel):
    content: str

class ConversationSearchQuery(BaseModel):
    natural_language_query: str


@router.get("", response_model=List[ConversationSummary])
def get_conversations(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    --- REVISED ---
    Fetches all clients for the user and formats them as conversation summaries.
    This ensures that clients with no messages yet still appear in the list.
    """
    try:
        logging.info(f"API: Fetching conversations for user {current_user.id}")
        all_clients = db.exec(
            select(Client).where(Client.user_id == current_user.id)
        ).all()
        logging.info(f"API: Found {len(all_clients)} clients for user {current_user.id}")

        summaries = []
        for client in all_clients:
            logging.debug(f"API: Processing client {client.id} ({client.full_name})")
            # Query for the last message
            last_message = db.exec(
                select(Message)
                .where(Message.client_id == client.id)
                .order_by(Message.created_at.desc())
            ).first()

            # Query for unread message count
            # Use first() to retrieve the count in a version-agnostic way
            unread_count_tuple = db.exec(
                select(func.count(Message.id))
                .where(
                    Message.client_id == client.id,
                    Message.direction == MessageDirection.INBOUND,
                    # --- FIX: Use the correct enum member for unread messages ---
                    Message.status == MessageStatus.RECEIVED
                )
            ).first()

            # Handle both tuple and integer return types from first()
            if unread_count_tuple is None:
                unread_count = 0
            elif isinstance(unread_count_tuple, tuple):
                unread_count = unread_count_tuple[0] if unread_count_tuple else 0
            else:
                # first() returned an integer directly
                unread_count = unread_count_tuple
            
            # Check if the client has any messages at all
            has_messages = last_message is not None

            # Calculate if client is online based on recent inbound message activity
            is_online = False
            if last_message and last_message.direction == MessageDirection.INBOUND:
                # Check if the last inbound message was within the last 5 minutes
                message_time = last_message.created_at.replace(tzinfo=timezone.utc) if last_message.created_at.tzinfo is None else last_message.created_at
                current_time = datetime.now(timezone.utc)
                time_diff = current_time - message_time
                is_online = time_diff.total_seconds() < 300  # 5 minutes

            summary = ConversationSummary(
                id=str(client.id), # Use client ID as the summary ID
                client_id=client.id,
                client_name=client.full_name,
                client_phone=client.phone,
                last_message=last_message.content if last_message else "No messages yet.",
                last_message_time=(
                    last_message.created_at.isoformat() 
                    if last_message 
                    else (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
                ),
                unread_count=unread_count,
                is_online=is_online,
                has_messages=has_messages,
                last_message_direction=last_message.direction if last_message else None,
                last_message_source=last_message.source if last_message else None
            )
            summaries.append(summary)
            
        logging.info(f"API: Returning {len(summaries)} conversation summaries for user {current_user.id}")
        return summaries
    except Exception as e:
        logging.error(f"API: Error in get_conversations for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch conversations")


@router.get("/messages/", response_model=ConversationDetailResponse)
async def get_conversation_history_by_client_id(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    """
    Retrieves message history and separates active AI recommendations into an immediate
    slate and a long-term plan, prioritizing Co-Pilot briefings.
    """
    try:
        history = crm_service.get_conversation_history(client_id=client_id, user_id=current_user.id)
        
        all_active_slates = crm_service.get_all_active_slates_for_client(
            client_id=client_id, user_id=current_user.id, session=session
        )
        
        # --- DEFINITIVE FIX IS HERE ---
        # Explicitly find the Co-Pilot briefing. If it exists, it MUST be the immediate recommendation.
        # This prevents the UI from accidentally showing an older, stale recommendation.
        co_pilot_briefing = next((s for s in all_active_slates if s.campaign_type == 'co_pilot_briefing'), None)
        
        if co_pilot_briefing:
            immediate_rec_slate = co_pilot_briefing
            # The active plan is the one *associated* with the co-pilot briefing, which is now paused.
            # We show the plan that IS paused, not a different DRAFT plan.
            paused_plan_id_str = co_pilot_briefing.key_intel.get("paused_plan_id")
            paused_plan_id = uuid.UUID(paused_plan_id_str) if paused_plan_id_str else None
            active_plan_slate = session.get(CampaignBriefing, paused_plan_id) if paused_plan_id else None
        else:
            # Standard logic: find the latest draft plan and the latest draft recommendation.
            immediate_rec_slate = next((s for s in all_active_slates if not s.is_plan), None)
            active_plan_slate = next((s for s in all_active_slates if s.is_plan), None)

        # --- NEW: Generate simple display_config based on user's vertical ---
        display_config = {
            "client_intel": {
                "title": "Client Intel",
                "icon": "Info"
            },
            "relationship_campaign": {
                "title": "Relationship Campaign",
                "icon": "BrainCircuit"
            },
            "properties": {
                "title": "Properties" if current_user.vertical == "real_estate" else "Content Resources",
                "icon": "Home" if current_user.vertical == "real_estate" else "BookOpen"
            }
        }

        return ConversationDetailResponse(
            messages=history if history else [],
            immediate_recommendations=immediate_rec_slate,
            active_plan=active_plan_slate,
            display_config=display_config
        )
    except Exception as e:
        logging.error(f"Error fetching messages for client {client_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch messages.")



@router.post("/{client_id}/send_reply", response_model=Message)
async def send_reply(
    client_id: uuid.UUID,
    payload: SendReplyPayload,
    current_user: User = Depends(get_current_user_from_token)
):
    """Sends a new message from the user to a client with comprehensive error handling."""
    try:
        # Validate payload
        if not payload.content or not payload.content.strip():
            raise HTTPException(status_code=400, detail="Message content cannot be empty")
        
        if len(payload.content) > 1600:  # SMS character limit
            raise HTTPException(status_code=400, detail="Message too long (max 1600 characters)")
        
        # Validate client ownership
        client = crm_service.get_client_by_id(client_id=client_id, user_id=current_user.id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        if not client.phone:
            raise HTTPException(status_code=400, detail="Client has no phone number")
        
        # Validate user has Twilio number
        if not current_user.twilio_phone_number:
            raise HTTPException(status_code=400, detail="User has no Twilio number configured")
        
        # Check for very recent duplicate messages (within 10 seconds)
        with Session(crm_service.engine) as session:
            recent_duplicate = session.exec(
                select(Message).where(
                    Message.client_id == client_id,
                    Message.user_id == current_user.id,
                    Message.direction == MessageDirection.OUTBOUND,
                    Message.content == payload.content.strip(),
                    Message.created_at >= datetime.now(timezone.utc) - timedelta(seconds=10)
                )
            ).first()
            
            if recent_duplicate:
                logging.warning(f"API: Very recent duplicate message detected for client {client_id}. "
                              f"Returning existing message instead of sending new one.")
                return recent_duplicate
        
        logging.info(f"API: Sending reply to client {client_id} from user {current_user.id}")
        
        # Orchestrator handles the entire process with error handling
        saved_message = await orchestrator.orchestrate_send_message_now(
            client_id=client_id,
            content=payload.content,
            user_id=current_user.id,
            source=MessageSource.MANUAL
        )

        if not saved_message:
            logging.error(f"API: Orchestrator failed to send message for client {client_id}")
            raise HTTPException(status_code=500, detail="Failed to send message")

        # Store all message data before the session closes
        message_data = {
            'id': saved_message.id,
            'user_id': saved_message.user_id,
            'client_id': saved_message.client_id,
            'content': saved_message.content,
            'direction': saved_message.direction,
            'status': saved_message.status,
            'source': saved_message.source,
            'sender_type': saved_message.sender_type,
            'created_at': saved_message.created_at
        }
        logging.info(f"API: Message sent successfully for client {client_id}, message ID: {message_data['id']}")
        
        # Return a fresh copy of the message data to avoid session issues
        return Message(**message_data)

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"API: Critical error in send_reply for client {client_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while sending message")


@router.get("/scheduled-messages/", response_model=List)
async def get_scheduled_messages(
    client_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get scheduled messages, optionally filtered by client_id."""
    # This function remains unchanged.
    try:
        if client_id:
            client = crm_service.get_client_by_id(client_id=client_id, user_id=current_user.id)
            if not client:
                raise HTTPException(status_code=404, detail="Client not found.")
            return crm_service.get_scheduled_messages_for_client(client_id=client_id, user_id=current_user.id)
        else:
            return crm_service.get_all_scheduled_messages(user_id=current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scheduled messages: {str(e)}")
    

@router.post("/search")
async def search_conversations(
    query: ConversationSearchQuery,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Performs a HYBRID search for clients (semantic + name keyword) and returns
    their corresponding conversation summaries.
    """
    search_query = query.natural_language_query
    logging.info(f"API: Hybrid searching conversations for user '{current_user.id}' with query: '{search_query}'")
    
    # --- Step 1: Perform SEMANTIC search ---
    semantic_match_ids = await audience_builder.find_clients_by_semantic_query(
        search_query, 
        user_id=current_user.id
    )
    
    # --- Step 2: Perform KEYWORD search on client names ---
    keyword_match_clients = crm_service.find_clients_by_name_keyword(
        query=search_query,
        user_id=current_user.id
    )
    keyword_match_ids = [client.id for client in keyword_match_clients]
    
    # --- Step 3: Combine the results ---
    # Use a set to automatically handle duplicates.
    combined_ids = set(semantic_match_ids).union(set(keyword_match_ids))
    
    if not combined_ids:
        return []

    # Step 4: Fetch the conversation summaries for the combined list of matched clients.
    summaries = crm_service.get_conversation_summaries_for_clients(
        client_ids=list(combined_ids),
        user_id=current_user.id
    )
    
    return summaries

@router.post("/{client_id}/mark-read")
async def mark_conversation_as_read(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_token)
):
    """Marks all inbound messages for a client as read."""
    try:
        # Verify the client belongs to the user
        client = crm_service.get_client_by_id(client_id=client_id, user_id=current_user.id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Mark all inbound messages as read
        with Session(crm_service.engine) as session:
            statement = select(Message).where(
                Message.client_id == client_id,
                Message.direction == 'inbound',
                Message.status == 'received'
            )
            unread_messages = session.exec(statement).all()
            
            for message in unread_messages:
                message.status = 'sent'  # Mark as read
            
            session.add_all(unread_messages)
            session.commit()
            
        logging.info(f"API: Marked {len(unread_messages)} messages as read for client {client_id}")
        return {"success": True, "messages_marked": len(unread_messages)}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"API: Failed to mark messages as read for client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to mark messages as read: {str(e)}")


@router.post("/test-recommendation")
async def test_recommendation_generation(
    current_user: User = Depends(get_current_user_from_token)
):
    """Test endpoint to verify recommendation generation works."""
    try:
        from agent_core.agents import conversation as conversation_agent
        from data.models.message import Message, MessageDirection
        
        # Get a valid client for the user
        clients = crm_service.get_all_clients(user_id=current_user.id)
        if not clients:
            raise HTTPException(status_code=404, detail="No clients found for user")
        
        client = clients[0]  # Use the first client
        
        # Create a test message
        test_message = Message(
            id=uuid.uuid4(),
            user_id=current_user.id,
            client_id=client.id,
            content="Hi! I just got a new job and we might be moving to a bigger house next year. My kids are starting high school which is exciting but stressful!",
            direction=MessageDirection.INBOUND,
            status="received",
            source="manual",
            sender_type="user",
            created_at=datetime.now(timezone.utc)
        )
        
        # Get conversation history
        conversation_history = crm_service.get_recent_messages(
            client_id=test_message.client_id, 
            user_id=current_user.id, 
            limit=10
        )
        
        # Generate recommendations
        recommendation_data = await conversation_agent.generate_recommendation_slate(
            current_user, 
            test_message.client_id, 
            test_message, 
            conversation_history
        )
        
        # --- NEW: Generate simple display_config based on user's vertical ---
        display_config = {
            "client_intel": {
                "title": "Client Intel",
                "icon": "Info"
            },
            "relationship_campaign": {
                "title": "Relationship Campaign",
                "icon": "BrainCircuit"
            },
            "properties": {
                "title": "Properties" if current_user.vertical == "real_estate" else "Content Resources",
                "icon": "Home" if current_user.vertical == "real_estate" else "BookOpen"
            }
        }
        
        return {
            "test_message": test_message.content,
            "client_id": str(test_message.client_id),
            "recommendation_data": recommendation_data,
            "has_update_client_intel": any(
                rec.get("type") == "UPDATE_CLIENT_INTEL" 
                for rec in recommendation_data.get("recommendations", [])
            ),
            "display_config": display_config
        }
        
    except Exception as e:
        logging.error(f"API: Test recommendation generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")
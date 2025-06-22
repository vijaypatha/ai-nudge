# ---
# File Path: backend/api/rest/campaigns.py
# Purpose: Defines API endpoints for outbound communications by calling the orchestrator.
# ---

from fastapi import APIRouter, HTTPException, status
from uuid import UUID

from data.models.message import SendMessageImmediate
from agent_core import orchestrator # Import the orchestrator

router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"]
)

@router.post("/messages/send-now", status_code=status.HTTP_200_OK)
async def send_message_now(message_data: SendMessageImmediate):
    """
    Sends a message immediately by calling the central orchestrator.
    This keeps the API layer clean and free of business logic.
    """
    # The API layer's only job is to validate input and call the service layer.
    success = await orchestrator.orchestrate_send_message_now(
        client_id=message_data.client_id,
        content=message_data.content
    )
    
    if success:
        return {"message": "Message sent successfully!", "client_id": message_data.client_id}
    else:
        # The orchestrator handles logging details; the API returns a generic error.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send message.")

# Note: Other campaign-related endpoints like 'schedule' would also be refactored
# to call new functions in the orchestrator, but we are only fixing the failing one for now.
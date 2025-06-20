from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class MessageSendRequest(BaseModel):
    message: str
    recipient_id: str # Example: client_id or property_id
    # Add any other relevant fields, e.g., sender_id if not implicit
    # context: Optional[dict] = None

@router.post("/messages/send-now/", summary="Send a message immediately")
async def send_message_now(payload: MessageSendRequest = Body(...)):
    logger.info(f"Received request to send message: '{payload.message}' to recipient ID: {payload.recipient_id}")
    
    if not payload.message or not payload.recipient_id:
        logger.error("Validation error: Message or recipient_id missing in payload.")
        raise HTTPException(status_code=400, detail="Message and recipient_id are required.")
    
    # Mock sending logic: In a real app, this would integrate with an email/SMS service
    # For now, we just log and return a success response.

    response_message = f"Message successfully simulated as sent to recipient {payload.recipient_id}."
    logger.info(response_message)
    return {
        "status": "success",
        "message": response_message,
        "details": {
            "recipient_id": payload.recipient_id,
            "message_length": len(payload.message)
        }
    }

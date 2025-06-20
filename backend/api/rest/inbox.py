from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional
# Corrected import path assuming llm_client is in agent_core sibling to api
from agent_core.llm_client import get_ai_suggestion
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class MessageAssistRequest(BaseModel):
    current_message: str = Field(..., description="The current message content typed by the user.")
    context: Optional[str] = Field(None, description="Optional context, like previous messages or client information.")

class SimulateIncomingMessageRequest(BaseModel):
    sender: str = Field(default="Test Client", description="Simulated sender of the message.")
    message_text: str = Field(..., description="The text of the simulated incoming message.")


@router.post("/receive-message/", summary="Get AI assistance for a message")
async def receive_message_and_assist(payload: MessageAssistRequest = Body(...)):
    logger.info(f"Received message for AI assistance: '{payload.current_message}' with context: '{payload.context if payload.context else 'No context provided'}'")

    if not payload.current_message and not payload.context: # Require at least some input
        logger.warning("AI assistance requested with no message and no context.")
        # Depending on LLM capabilities, might still try, or return error
        # For this mock, let's assume some input is good.

    try:
        # The llm_client.get_ai_suggestion expects a prompt_template and context_details
        # We can adapt the user's current_message and context to fit this.
        prompt_for_llm = f"Help me refine or continue this message: '{payload.current_message}'"
        ai_suggestion = get_ai_suggestion(prompt_template=prompt_for_llm, context_details=payload.context or "General assistance requested.")

        logger.info(f"Generated AI suggestion: {ai_suggestion}")
        return {
            "status": "success",
            "ai_suggestion": ai_suggestion,
            "original_message": payload.current_message
        }
    except Exception as e:
        logger.error(f"Error getting AI suggestion: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get AI suggestion: {str(e)}")

@router.post("/simulate-incoming-message/", summary="Simulate an incoming message to generate an AI draft")
async def simulate_incoming_message(payload: SimulateIncomingMessageRequest = Body(...)):
    logger.info(f"Simulating incoming message from '{payload.sender}': '{payload.message_text}'")

    if not payload.message_text:
        logger.error("Simulated message_text cannot be empty.")
        raise HTTPException(status_code=400, detail="Simulated message_text cannot be empty.")

    try:
        # Construct a prompt for the LLM to draft a response
        prompt_for_llm = f"Draft a professional realtor response to the following client message: '{payload.message_text}' from client '{payload.sender}'."
        # Context could be enhanced with more details about the realtor's goals, listings, etc.
        context_for_llm = "The realtor wants to be helpful, engaging, and encourage further interaction."

        ai_draft_response = get_ai_suggestion(prompt_template=prompt_for_llm, context_details=context_for_llm)

        logger.info(f"Generated AI draft for simulated message: {ai_draft_response}")
        return {
            "status": "success",
            "simulated_sender": payload.sender,
            "simulated_message": payload.message_text,
            "ai_draft_response": ai_draft_response
        }
    except Exception as e:
        logger.error(f"Error generating AI draft for simulated message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate AI draft: {str(e)}")

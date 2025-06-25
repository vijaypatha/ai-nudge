# backend/agent_core/agents/conversation.py

# Purpose: This service is the "conversation agent." It is responsible for generating intelligent, human-like draft responses.
from typing import Dict, Any
import uuid

# --- FINAL FIX: Use correct import paths relative to the backend root ---
from integrations import openai as openai_service
from data import crm as crm_service
# --- END FINAL FIX ---


async def generate_response(
    client_id: uuid.UUID,
    incoming_message_content: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generates a draft response for an incoming client message using OpenAI.
    Incorporates client context and property data for smarter responses.
    """
    print(f"CONVERSATION AGENT: Generating response for client {client_id} using OpenAI...")
    
    client_name = context.get('client_name', 'client')
    client_tags = ", ".join(context.get('client_tags', []))
    
    # Fetch property context from the internal CRM service.
    all_properties = crm_service.get_all_properties_mock()

    property_context_str = ""
    if all_properties:
        property_context_str = "\n\nAvailable Properties (for context, include only relevant ones in response):\n"
        for i, prop in enumerate(all_properties[:3]):
            property_context_str += (
                f"- Property {i+1}: {prop.address}, Price: ${prop.price:,.0f}, "
                f"Status: {prop.status}, Type: {prop.property_type}\n"
            )

    # Construct the prompt for OpenAI
    messages = [
        {"role": "system", "content": (
            "You are an AI Nudge assistant for a real estate agent. Your goal is to provide concise, "
            "helpful, and professional draft responses to client inquiries. "
            "Maintain a helpful, slightly proactive, and personalized tone. "
            "Suggest concrete next steps like sending listings or scheduling a showing when appropriate. "
            f"The client's name is {client_name}. Their tags include: {client_tags}."
            f"{property_context_str}"
        )},
        {"role": "user", "content": incoming_message_content}
    ]
    
    # Call the real OpenAI LLM
    ai_draft_content = await openai_service.generate_text_completion(
        prompt_messages=messages,
        model="gpt-4o-mini"
    )
    
    if ai_draft_content:
        print(f"CONVERSATION AGENT: Received OpenAI response: {ai_draft_content[:50]}...")
        return {
            "ai_draft": ai_draft_content,
            "confidence": 0.95,
            "suggested_action": "send_draft"
        }
    else:
        print("CONVERSATION AGENT: OpenAI failed to generate response. Falling back to generic.")
        return {
            "ai_draft": "I'm sorry, I couldn't generate a smart response right now. Please try again later.",
            "confidence": 0.1,
            "suggested_action": "review_manually"
        }
# backend/agent_core/agents/conversation.py

# Purpose of this service: This service coversation agent." It is responsible for generating intelligent, human-like draft responses to incoming client messages, leveraging external AI models (like OpenAI) and internal knowledge (like client context and property data).

from typing import Dict, Any, Optional
import uuid

# Import the real OpenAI service for generating AI responses.
from integrations import openai as openai_service
from integrations import mls as mls_service


# The _mock_llm_generate function is removed as we are now using OpenAI.

async def generate_response(
    client_id: uuid.UUID,
    incoming_message_content: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generates a draft response for an incoming client message using OpenAI.
    Incorporates client context and property data for smarter responses.

    How it works for the robot: This is like the robot's "thought process" for
    chatting, now powered by a supercomputer brain. When a customer says something,
    this part of the robot quickly thinks of a smart reply, understanding who
    the customer is AND what houses are relevant.

    - **client_id**: The unique ID of the client sending the message.
    - **incoming_message_content**: The actual text content of the message from the client.
    - **context**: A dictionary containing relevant information about the client or conversation.
      (e.g., client_tags, client_name, properties_viewed).
    Returns a dictionary containing the AI's generated draft response.
    """
    print(f"CONVERSATION AGENT: Generating response for client {client_id} using OpenAI...")
    
    client_name = context.get('client_name', 'client')
    client_tags = ", ".join(context.get('client_tags', []))
    
    # --- Fetch relevant property data (Zillow Mock Integration) ---
    # This simulates the AI having access to up-to-date property information.
    # In a real scenario, this would involve more sophisticated searching based on client interest.
    # For now, it fetches all available properties to provide as context to the LLM.
    all_properties = mls_service.get_all_listings()
    property_context_str = ""
    if all_properties:
        property_context_str = "\n\nAvailable Properties (for context, include only relevant ones in response):\n"
        for i, prop in enumerate(all_properties[:3]): # Limit to first 3 properties for brevity in the prompt
            property_context_str += (
                f"- Property {i+1}: {prop.address}, Price: ${prop.price:,.0f}, "
                f"Status: {prop.status}, Type: {prop.property_type}\n"
            )

    # --- Construct the prompt for OpenAI ---
    # This uses OpenAI's chat message format, with a 'system' message to set the AI's role
    # and a 'user' message for the actual client inquiry.
    messages = [
        {"role": "system", "content": (
            "You are an AI Nudge assistant for a real estate agent. Your goal is to provide concise, "
            "helpful, and professional draft responses to client inquiries. "
            "Maintain a helpful, slightly proactive, and personalized tone. "
            "Suggest concrete next steps like sending listings or scheduling a showing when appropriate. "
            "Your responses are drafts for the agent to review and send. "
            "If asked about properties or buying/selling, use the provided property context, but only include "
            "details that directly answer the query or are highly relevant."
            f"The client's name is {client_name}. Their tags include: {client_tags}."
            f"{property_context_str}" # Include dynamically fetched property data as context for the AI
        )},
        {"role": "user", "content": incoming_message_content}
    ]
    
    # Call the real OpenAI LLM (Large Language Model) to get a draft response.
    # The 'gpt-4o-mini' model is chosen for its balance of intelligence and cost-efficiency.
    ai_draft_content = await openai_service.generate_text_completion(
        prompt_messages=messages,
        model="gpt-4o-mini"
    )
    
    # Process the response from OpenAI.
    if ai_draft_content:
        print(f"CONVERSATION AGENT: Received OpenAI response: {ai_draft_content[:50]}...")
        return {
            "ai_draft": ai_draft_content,
            "confidence": 0.95, # Assign a high confidence as it's from a powerful LLM
            "suggested_action": "send_draft" # Suggest that the agent can send this draft
        }
    else:
        # Fallback response if OpenAI fails to generate content.
        print("CONVERSATION AGENT: OpenAI failed to generate response. Falling back to generic.")
        return {
            "ai_draft": "I'm sorry, I couldn't generate a smart response right now. Please try again later.",
            "confidence": 0.1, # Low confidence for a generic fallback
            "suggested_action": "review_manually" # Suggest manual review
        }
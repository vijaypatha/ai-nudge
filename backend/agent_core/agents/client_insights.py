# ---
# File Path: backend/agent_core/agents/client_insights.py
# Purpose: To extract structured intel from unstructured conversation text.
# ---
from agent_core.agents import conversation as conversation_agent

async def extract_intel_from_message(content: str) -> str | None:
    """
    Uses an LLM to analyze a message and extract a single, key piece of intel.
    Returns the piece of intel as a string, or None if nothing is found.
    """
    print("INTELLIGENCE AGENT: Analyzing message for potential intel...")

    prompt = (
        "Analyze the following text from a client to a professional. Your task is to identify a single, "
        "most important piece of new information that should be saved as a note in the client's profile. "
        "Examples include life events (getting married, new baby, new pet), changes in needs "
        "(needs a home office, looking in a new city), or key preferences (loves gardening, prefers modern architecture). "
        "Respond with only the single, concise note. For example, if the text is 'we are so excited to be expecting a baby', "
        "you should respond with 'Expecting a baby'. If no new, significant intel is found, respond with 'None'."
        f"\n\nClient's message: \"{content}\""
    )

    intel_suggestion = await conversation_agent.generate_response(
        client_id=None, # This is a generic task, not for a specific client response
        incoming_message_content=prompt,
        context={}
    )

    if intel_suggestion and "none" not in intel_suggestion.get("ai_draft", "").lower():
        found_intel = intel_suggestion["ai_draft"]
        print(f"INTELLIGENCE AGENT: Found new intel -> {found_intel}")
        return found_intel

    print("INTELLIGENCE AGENT: No new intel found.")
    return None
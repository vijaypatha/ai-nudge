# FILE: agent_core/brain/relationship_planner.py
# --- V6: FULLY VERTICAL-AGNOSTIC ---
# This version is now fully aligned with the refactored, vertically-aware
# playbook structure. It fixes the ImportError and makes the entire time-based
# planning process scalable for new verticals.
import re
import logging
from datetime import datetime, timedelta
from data import crm as crm_service
from data.models.user import User
from data.models.client import Client
from data.models.message import ScheduledMessage, MessageStatus
from workflow.relationship_playbooks import VERTICAL_LEGACY_PLAYBOOKS_REGISTRY
from agent_core.agents import conversation as conversation_agent

# --- Generic Date/Time Helper Functions (Unchanged) ---
def _get_next_holiday_date(holiday_name: str, send_before_days: int) -> datetime | None:
    """Calculates the next occurrence of a holiday, offset by a few days."""
    now = datetime.now()
    year = now.year
    # This can be expanded or moved to a more robust holiday library
    holidays = {
        "july_4th": datetime(year, 7, 4),
        "thanksgiving": datetime(year, 11, 28), # Note: This is a fixed date for example purposes
        "christmas": datetime(year, 12, 25)
    }
    holiday_date = holidays.get(holiday_name.lower())
    if not holiday_date: return None

    scheduled_date = holiday_date - timedelta(days=send_before_days)
    if scheduled_date < now:
        return (holiday_date.replace(year=year + 1) - timedelta(days=send_before_days))
    return scheduled_date

def _parse_birthday_from_notes(notes: list[str]) -> datetime | None:
    """Uses a regular expression to find birthdays in various formats."""
    birthday_regex = r"(?:(?:birthday|bday)\s*is\s*on)?\s*(?P<month>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december|\d{1,2})[\s/]+(?P<day>\d{1,2})"
    for note in notes:
        match = re.search(birthday_regex, note.lower())
        if match:
            try:
                month_str, day_str = match.group('month'), match.group('day')
                month_num = int(month_str) if month_str.isdigit() else (datetime.strptime(month_str, "%B").month if len(month_str) > 3 else datetime.strptime(month_str, "%b").month)
                day = int(day_str)
                return datetime(datetime.now().year, month_num, day)
            except (ValueError, IndexError):
                continue
    return None

def _parse_custom_frequency(notes: list[str]) -> int | None:
    """Parses notes like 'contact every 90 days' to get the number of days."""
    for note in notes:
        match = re.search(r"every\s+(\d+)\s+days", note, re.IGNORECASE)
        if match: return int(match.group(1))
        match = re.search(r"once a (quarter|month)", note, re.IGNORECASE)
        if match: return 90 if match.group(1) == 'quarter' else 30
    return None

# --- Agnostic Helper to Schedule a Message ---
async def _schedule_message_from_touchpoint(client: Client, user: User, touchpoint: dict, scheduled_date: datetime):
    """Helper function to generate and save a single scheduled message."""
    notes_context = ", ".join(client.preferences.get("notes", []))
    # FIX: Use 'user.full_name' instead of 'realtor.full_name'
    prompt = touchpoint["prompt"].format(client_name=client.full_name, notes=notes_context, realtor_name=user.full_name)
    
    ai_draft_result = await conversation_agent.generate_response(client_id=client.id, incoming_message_content=prompt, context={"client_name": client.full_name})
    
    if ai_draft_result and ai_draft_result.get("ai_draft"):
        is_recurring = "recurrence" in touchpoint
        message_to_schedule = ScheduledMessage(
            client_id=client.id,
            user_id=user.id, # FIX: Explicitly set user_id
            content=ai_draft_result["ai_draft"],
            scheduled_at=scheduled_date,
            status=MessageStatus.PENDING,
            playbook_touchpoint_id=touchpoint.get("id"),
            is_recurring=is_recurring
        )
        crm_service.save_scheduled_message(message_to_schedule)

# --- Vertically-Aware Main Planner Function ---
async def plan_relationship_campaign(client: Client, user: User):
    """
    (Comprehensively Upgraded) Plans a campaign by selecting playbooks
    based on the user's vertical, then matching on client tags and preferences.
    """
    logging.info(f"RELATIONSHIP PLANNER: Planning campaign for client -> {client.full_name} in vertical '{user.vertical}'")
    # This is a destructive operation, clears all old scheduled messages to create a new plan
    crm_service.delete_scheduled_messages_for_client(client_id=client.id, user_id=user.id)

    # FIX: Get the correct list of playbooks for the user's vertical
    playbooks_for_vertical = VERTICAL_LEGACY_PLAYBOOKS_REGISTRY.get(user.vertical, [])
    if not playbooks_for_vertical:
        logging.warning(f"PLANNER: No legacy playbooks found for vertical '{user.vertical}'. Aborting.")
        return

    # The custom frequency playbook is usually the first one and is special
    custom_frequency_playbook = playbooks_for_vertical[0]
    
    # --- Step 1: Check for a custom frequency preference ---
    custom_frequency_days = _parse_custom_frequency(client.preferences.get("notes", []))
    if custom_frequency_days and "touchpoints" in custom_frequency_playbook:
        logging.info(f"PLANNER: Found custom frequency of {custom_frequency_days} days for {client.full_name}.")
        touchpoint = custom_frequency_playbook["touchpoints"][0]
        touchpoint["recurrence"]["frequency_days"] = custom_frequency_days
        scheduled_date = datetime.now() + timedelta(days=custom_frequency_days)
        # FIX: Pass 'user' instead of 'realtor'
        await _schedule_message_from_touchpoint(client, user, touchpoint, scheduled_date)
        return # Custom frequency overrides all other tag-based playbooks

    # --- Step 2: If no custom rule, find a standard playbook based on tags ---
    chosen_playbook = None
    all_client_tags = (client.ai_tags or []) + (client.user_tags or [])
    # FIX: Iterate through the vertically-scoped playbooks
    for playbook in playbooks_for_vertical:
        if not playbook.get("triggers") or any(trigger in all_client_tags for trigger in playbook["triggers"]):
            chosen_playbook = playbook
            break # Found the first matching playbook
    
    if not chosen_playbook:
        logging.info(f"PLANNER: No matching playbook found for tags {all_client_tags} for {client.full_name}.")
        return

    logging.info(f"PLANNER: Matched {client.full_name} to playbook '{chosen_playbook['name']}'")

    # --- Step 3: Schedule all touchpoints from the chosen playbook ---
    for touchpoint in chosen_playbook.get("touchpoints", []):
        scheduled_date = None
        event_type = touchpoint.get("event_type")

        if event_type == "birthday":
            birthday = _parse_birthday_from_notes(client.preferences.get("notes", []))
            if birthday: scheduled_date = birthday.replace(year=datetime.now().year)
        elif event_type == "date_offset":
            scheduled_date = datetime.now() + timedelta(days=touchpoint["offset_days"])
        elif event_type == "holiday":
            scheduled_date = _get_next_holiday_date(touchpoint.get("holiday_name", ""), touchpoint.get("send_before_days", 1))
        elif event_type == "recurring":
            # This logic is for recurring touchpoints in non-custom playbooks
            if "recurrence" in touchpoint and "frequency_days" in touchpoint["recurrence"]:
                 scheduled_date = datetime.now() + timedelta(days=touchpoint["recurrence"]["frequency_days"])

        if scheduled_date:
            # If a date is in the past for this year, schedule it for next year
            if scheduled_date < datetime.now():
                scheduled_date = scheduled_date.replace(year=datetime.now().year + 1)
            # FIX: Pass 'user' instead of 'realtor'
            await _schedule_message_from_touchpoint(client, user, touchpoint, scheduled_date)
# FILE: agent_core/brain/relationship_planner.py
# --- V7: UNIFIED DATE PARSING & STANDARDIZED PROMPTS ---
# This version introduces a single, powerful date parser and uses
# a generic {user_full_name} placeholder, making the system truly agnostic.

import re
import logging
from datetime import datetime, timedelta
from data import crm as crm_service
from data.models.user import User
from data.models.client import Client
from data.models.message import ScheduledMessage, MessageStatus
from workflow.relationship_playbooks import VERTICAL_LEGACY_PLAYBOOKS_REGISTRY
from agent_core.agents import conversation as conversation_agent

# --- NEW: This function finds ALL date-based events, not just the first one. ---
def _parse_all_personal_events_from_notes(notes: list[str]) -> list[tuple[str, datetime]]:
    """
    (NEW UNIFIED PARSER) Uses re.finditer to find ALL personal events
    (birthdays, anniversaries, etc.) in the notes and returns them as a list.
    """
    events_found = []
    event_regex = r"(?i)\b(?P<event_name>birthday|bday|anniversary|tax\s+day|christmas|new\s+year's|thanksgiving)[\s,:]+(?:on|is)?\s*(?P<month>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december|\d{1,2})[\s/]+(?P<day>\d{1,2})(?:st|nd|rd|th)?\b"

    for note_line in notes:
        # Use finditer to get all non-overlapping matches
        for match in re.finditer(event_regex, note_line):
            try:
                # Sanitize the event name for matching later
                event_name = match.group('event_name').lower().replace("celebrates ", "")
                month_str = match.group('month')
                day_str = match.group('day')

                if not month_str.isdigit():
                    month_num = datetime.strptime(month_str, "%B").month if len(month_str) > 3 else datetime.strptime(month_str, "%b").month
                else:
                    month_num = int(month_str)

                day = int(day_str)
                event_date = datetime(datetime.now().year, month_num, day)

                logging.info(f"PLANNER: Found personal event '{event_name}' on {event_date.strftime('%Y-%m-%d')} from notes.")
                events_found.append((event_name, event_date))
            except (ValueError, IndexError):
                continue
    return events_found

def _parse_custom_frequency(notes: list[str]) -> int | None:
    """Parses notes like 'contact every 90 days' to get the number of days."""
    for note in notes:
        match = re.search(r"every\s+(\d+)\s+days", note, re.IGNORECASE)
        if match: return int(match.group(1))
        match = re.search(r"once a (quarter|month)", note, re.IGNORECASE)
        if match: return 90 if match.group(1) == 'quarter' else 30
    return None

async def _schedule_message_from_touchpoint(client: Client, user: User, touchpoint: dict, scheduled_date: datetime, event_name: str = "event"):
    """Helper function to generate and save a single scheduled message."""
    notes_context = client.notes or ""
    # --- NEW: Using standardized placeholder {user_full_name} ---
    prompt = touchpoint["prompt"].format(client_name=client.full_name, notes=notes_context, user_full_name=user.full_name, event_name=event_name)

    ai_draft, _ = await conversation_agent.draft_campaign_step_message(
        realtor=user, client=client, prompt=prompt, delay_days=0
    )

    if ai_draft:
        is_recurring = "recurrence" in touchpoint
        # Check if this exact recurring message is already scheduled for the future
        if is_recurring and touchpoint.get("id") and crm_service.has_future_recurring_message(client.id, touchpoint["id"]):
            logging.info(f"PLANNER: Skipping schedule for recurring message '{touchpoint.get('id')}' for client {client.id} as a future one already exists.")
            return

        message_to_schedule = ScheduledMessage(
            client_id=client.id,
            user_id=user.id,
            content=ai_draft,
            scheduled_at_utc=scheduled_date,
            timezone=user.timezone or "UTC",
            status=MessageStatus.PENDING,
            playbook_touchpoint_id=touchpoint.get("id"),
            is_recurring=is_recurring
        )
        crm_service.save_scheduled_message(message_to_schedule)


async def plan_relationship_campaign(client: Client, user: User):
    """
    (Definitive Version) Plans a campaign by finding all events in notes first,
    then matching them to the appropriate playbook touchpoints. It ONLY deletes
    messages that it is responsible for.
    """
    logging.info(f"RELATIONSHIP PLANNER: Planning campaign for client -> {client.full_name} in vertical '{user.vertical}'")

    playbooks_for_vertical = VERTICAL_LEGACY_PLAYBOOKS_REGISTRY.get(user.vertical, [])
    if not playbooks_for_vertical:
        logging.warning(f"PLANNER: No legacy playbooks found for vertical '{user.vertical}'. Aborting.")
        return

    # --- STEP 1: Identify all touchpoint IDs this planner is responsible for. ---
    managed_touchpoint_ids = []
    for playbook in playbooks_for_vertical:
        for touchpoint in playbook.get("touchpoints", []):
            if touchpoint.get("id"):
                managed_touchpoint_ids.append(touchpoint.get("id"))

    # --- STEP 2: Call the new, precise deletion function. ---
    # This ONLY deletes pending messages that were created from the IDs above,
    # leaving all other scheduled messages (e.g., from conversations) untouched.
    crm_service.delete_scheduled_messages_by_touchpoint_ids(
        client_id=client.id, 
        user_id=user.id, 
        touchpoint_ids=managed_touchpoint_ids
    )

    # --- STEP 3: Proceed with the existing logic to schedule new messages. ---
    notes_for_parsing = [client.notes] if client.notes else []
    all_client_tags = (client.ai_tags or []) + (client.user_tags or [])

    all_parsed_events = _parse_all_personal_events_from_notes(notes_for_parsing)
    custom_frequency_days = _parse_custom_frequency(notes_for_parsing)

    for playbook in playbooks_for_vertical:
        triggers = playbook.get("triggers", [])
        if triggers and not any(trigger in all_client_tags for trigger in triggers):
            continue

        for touchpoint in playbook.get("touchpoints", []):
            event_type = touchpoint.get("event_type")

            if event_type == "personal_event":
                for event_name, scheduled_date in all_parsed_events:
                    handled_events = touchpoint.get("handled_events", [])
                    if event_name in handled_events:
                        logging.info(f"PLANNER: Found matching rule '{touchpoint.get('name')}' for event '{event_name}'. Scheduling message.")
                        if scheduled_date < datetime.now():
                            scheduled_date = scheduled_date.replace(year=datetime.now().year + 1)
                        await _schedule_message_from_touchpoint(client, user, touchpoint, scheduled_date, event_name)

            elif event_type == "recurring" and custom_frequency_days:
                scheduled_date = datetime.now() + timedelta(days=custom_frequency_days)
                await _schedule_message_from_touchpoint(client, user, touchpoint, scheduled_date, "Custom Check-in")

            elif event_type == "date_offset":
                scheduled_date = datetime.now() + timedelta(days=touchpoint["offset_days"])
                await _schedule_message_from_touchpoint(client, user, touchpoint, scheduled_date, touchpoint.get("name", "check-in"))
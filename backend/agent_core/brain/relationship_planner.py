# ---
# File Path: backend/agent_core/brain/relationship_planner.py
# --- V5: Upgraded to handle Holiday Events ---
# This version adds logic to schedule messages for specific holidays.
# ---
import re
from datetime import datetime, timedelta
from data import crm as crm_service
from data.models.user import User
from data.models.client import Client
from data.models.message import ScheduledMessage, MessageStatus
from workflow.relationship_playbooks import ALL_PLAYBOOKS, CUSTOM_FREQUENCY_PLAYBOOK
from agent_core.agents import conversation as conversation_agent

def _get_next_holiday_date(holiday_name: str, send_before_days: int) -> datetime | None:
    """Calculates the next occurrence of a holiday, offset by a few days."""
    now = datetime.now()
    year = now.year
    holidays = {"july_4th": datetime(year, 7, 4), "thanksgiving": datetime(year, 11, 28), "christmas": datetime(year, 12, 25)}
    holiday_date = holidays.get(holiday_name.lower())
    if not holiday_date: return None

    # Schedule for X days before the holiday
    scheduled_date = holiday_date - timedelta(days=send_before_days)
    if scheduled_date < now:
        # If the send date has passed this year, schedule for next year's holiday
        return (holiday_date.replace(year=year + 1) - timedelta(days=send_before_days))
    return scheduled_date

def _parse_birthday_from_notes(notes: list[str]) -> datetime | None:
    """Uses a regular expression to find birthdays in various formats."""
    birthday_regex = r"(?:(?:birthday|bday)\s*is\s*on)?\s*(?P<month>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december|\d{1,2})[\s/]+(?P<day>\d{1,2})"
    for note in notes:
        match = re.search(birthday_regex, note.lower())
        if match:
            try:
                month_str = match.group('month')
                day_str = match.group('day')
                if not month_str.isdigit():
                    month_num = datetime.strptime(month_str, "%B").month if len(month_str) > 3 else datetime.strptime(month_str, "%b").month
                else:
                    month_num = int(month_str)
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

async def _schedule_message_from_touchpoint(client, realtor, touchpoint, scheduled_date):
    """Helper function to generate and save a single scheduled message."""
    notes_context = ", ".join(client.preferences.get("notes", []))
    prompt = touchpoint["prompt"].format(client_name=client.full_name, notes=notes_context, realtor_name=realtor.full_name)
    
    ai_draft_result = await conversation_agent.generate_response(client_id=client.id, incoming_message_content=prompt, context={"client_name": client.full_name})
    
    if ai_draft_result and ai_draft_result.get("ai_draft"):
        is_recurring = "recurrence" in touchpoint
        message_to_schedule = ScheduledMessage(
            client_id=client.id,
            content=ai_draft_result["ai_draft"],
            scheduled_at=scheduled_date,
            status=MessageStatus.PENDING,
            playbook_touchpoint_id=touchpoint.get("id"),
            is_recurring=is_recurring
        )
        crm_service.save_scheduled_message(message_to_schedule)
        
async def plan_relationship_campaign(client: Client, realtor: User):
    """(Majorly Upgraded) Plans a campaign based on custom frequency, tags, and recurring rules."""
    print(f"RELATIONSHIP PLANNER: Planning campaign for client -> {client.full_name}")
    crm_service.delete_scheduled_messages_for_client(client.id)

    # --- Step 1: Check for a custom frequency preference ---
    custom_frequency_days = _parse_custom_frequency(client.preferences.get("notes", []))
    if custom_frequency_days:
        print(f"PLANNER: Found custom frequency of {custom_frequency_days} days for {client.full_name}.")
        touchpoint = CUSTOM_FREQUENCY_PLAYBOOK["touchpoints"][0]
        # Make the recurrence rule match the custom preference
        touchpoint["recurrence"]["frequency_days"] = custom_frequency_days
        scheduled_date = datetime.now() + timedelta(days=custom_frequency_days)
        await _schedule_message_from_touchpoint(client, realtor, touchpoint, scheduled_date)
        return # Exit after applying the custom rule

    # --- Step 2: If no custom rule, find a playbook based on tags ---
    chosen_playbook = None
    all_client_tags = (client.ai_tags or []) + (client.user_tags or [])
    for playbook in ALL_PLAYBOOKS:
        if not playbook["triggers"] or any(trigger in all_client_tags for trigger in playbook["triggers"]):
            chosen_playbook = playbook
            break
    
    if not chosen_playbook:
        print(f"PLANNER: No matching playbook found for {client.full_name}.")
        return

    print(f"PLANNER: Matched {client.full_name} to playbook '{chosen_playbook['name']}'")

    # --- Step 3: Schedule all touchpoints from the chosen playbook ---
    for touchpoint in chosen_playbook["touchpoints"]:
        scheduled_date = None
        event_type = touchpoint["event_type"]

        if event_type == "birthday":
            birthday = _parse_birthday_from_notes(client.preferences.get("notes", []))
            if birthday: scheduled_date = birthday.replace(year=datetime.now().year)
        elif event_type == "date_offset":
            scheduled_date = datetime.now() + timedelta(days=touchpoint["offset_days"])
        elif event_type == "holiday":
            scheduled_date = _get_next_holiday_date(touchpoint.get("holiday_name", ""), touchpoint.get("send_before_days", 1))
        elif event_type == "recurring":
            scheduled_date = datetime.now() + timedelta(days=touchpoint["recurrence"]["frequency_days"])

        if scheduled_date:
            if scheduled_date < datetime.now(): scheduled_date = scheduled_date.replace(year=datetime.now().year + 1)
            await _schedule_message_from_touchpoint(client, realtor, touchpoint, scheduled_date)
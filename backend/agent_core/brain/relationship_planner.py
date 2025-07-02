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
from workflow.relationship_playbooks import ALL_PLAYBOOKS
from agent_core.agents import conversation as conversation_agent

def _get_next_holiday_date(holiday_name: str) -> datetime:
    """Calculates the next occurrence of a given holiday."""
    now = datetime.now()
    # In a real app, this would use a more robust holiday library.
    holidays = {
        "christmas": datetime(now.year, 12, 25)
    }
    holiday_date = holidays.get(holiday_name.lower())
    if holiday_date and holiday_date < now:
        return holiday_date.replace(year=now.year + 1)
    return holiday_date or now # Fallback to now if holiday not found

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

async def plan_relationship_campaign(client: Client, realtor: User):
    """(UPGRADED) Analyzes a client and schedules a full sequence of relationship touchpoints."""
    print(f"RELATIONSHIP PLANNER: Planning campaign for client -> {client.full_name}")

    chosen_playbook = None
    all_client_tags = (client.ai_tags or []) + (client.user_tags or [])
    
    for playbook in ALL_PLAYBOOKS:
        if any(trigger in all_client_tags for trigger in playbook["triggers"]):
            chosen_playbook = playbook
            break

    if not chosen_playbook:
        print(f"RELATIONSHIP PLANNER: No matching playbook found for {client.full_name}.")
        return

    print(f"RELATIONSHIP PLANNER: Matched {client.full_name} to playbook '{chosen_playbook['name']}'")
    crm_service.delete_scheduled_messages_for_client(client.id)

    for touchpoint in chosen_playbook["touchpoints"]:
        scheduled_date = None
        event_type = touchpoint["event_type"]

        if event_type == "birthday":
            birthday = _parse_birthday_from_notes(client.preferences.get("notes", []))
            if birthday:
                scheduled_date = birthday.replace(year=datetime.now().year)
                if scheduled_date < datetime.now():
                    scheduled_date = scheduled_date.replace(year=datetime.now().year + 1)
        
        elif event_type == "date_offset":
            scheduled_date = datetime.now() + timedelta(days=touchpoint["offset_days"])
        
        # NEW: Handle holiday event types
        elif event_type == "holiday":
            scheduled_date = _get_next_holiday_date(touchpoint.get("holiday_name", ""))

        if scheduled_date:
            notes_context = ", ".join(client.preferences.get("notes", []))
            prompt = touchpoint["prompt"].format(client_name=client.full_name, notes=notes_context, realtor_name=realtor.full_name)

            ai_draft_result = await conversation_agent.generate_response(
                client_id=client.id,
                incoming_message_content=prompt,
                context={"client_name": client.full_name}
            )

            if ai_draft_result and ai_draft_result.get("ai_draft"):
                message_to_schedule = ScheduledMessage(
                    client_id=client.id,
                    content=ai_draft_result["ai_draft"],
                    scheduled_at=scheduled_date,
                    status=MessageStatus.PENDING 
                )
                crm_service.save_scheduled_message(message_to_schedule)
            else:
                print(f"  - FAILED: Could not generate AI draft for task '{touchpoint['name']}'")
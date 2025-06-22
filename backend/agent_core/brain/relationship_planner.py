# ---
# File Path: backend/agent_core/brain/relationship_planner.py
# Purpose: Proactively plans and schedules relationship campaigns for clients.
# ---
from datetime import datetime, timedelta
from data import crm as crm_service
from data.models.user import User
from data.models.client import Client
from data.models.message import ScheduledMessage, ScheduledMessageCreate
from workflow.relationship_playbooks import ALL_PLAYBOOKS
from agent_core.agents import conversation as conversation_agent

def _parse_birthday_from_notes(notes: list[str]) -> datetime | None:
    # ... (this helper function remains the same) ...
    for note in notes:
        if "birthday is on" in note.lower():
            try:
                date_str = note.lower().split("birthday is on")[1].strip()
                bday_this_year = datetime.strptime(f"{date_str} {datetime.now().year}", "%B %d %Y")
                return bday_this_year
            except ValueError:
                continue
    return None

async def plan_relationship_campaign(client: Client, realtor: User):
    """Analyzes a client and schedules a full sequence of relationship touchpoints."""
    print(f"RELATIONSHIP PLANNER: Planning campaign for new client -> {client.full_name}")

    chosen_playbook = None
    # ... (playbook matching logic is the same) ...
    if "buyer" in client.tags:
        chosen_playbook = ALL_PLAYBOOKS[0]

    if not chosen_playbook:
        print(f"RELATIONSHIP PLANNER: No matching playbook found for {client.full_name}.")
        return

    print(f"RELATIONSHIP PLANNER: Matched {client.full_name} to playbook '{chosen_playbook['name']}'")

    for touchpoint in chosen_playbook["touchpoints"]:
        scheduled_date = None
        if touchpoint["event_type"] == "birthday":
            birthday = _parse_birthday_from_notes(client.preferences.get("notes", []))
            if birthday:
                if birthday < datetime.now():
                    scheduled_date = birthday.replace(year=datetime.now().year + 1)
                else:
                    scheduled_date = birthday

        elif touchpoint["event_type"] == "quarterly_check_in":
            scheduled_date = datetime.now() + timedelta(days=touchpoint["offset_days"])

        if scheduled_date:
            # --- This is the new, implemented logic ---
            # 1. Generate the AI draft for the touchpoint.
            notes_context = ", ".join(client.preferences.get("notes", []))
            prompt = touchpoint["prompt"].format(client_name=client.full_name, notes=notes_context, realtor_name=realtor.full_name)

            ai_draft_result = await conversation_agent.generate_response(
                client_id=client.id,
                incoming_message_content=prompt,
                context={"client_name": client.full_name}
            )

            # 2. If successful, create and save the scheduled message.
            if ai_draft_result and ai_draft_result.get("ai_draft"):
                message_to_schedule = ScheduledMessageCreate(
                    client_id=client.id,
                    content=ai_draft_result["ai_draft"],
                    scheduled_at=scheduled_date
                )
                # The full ScheduledMessage object is created with a new ID and default status.
                final_message = ScheduledMessage(**message_to_schedule.model_dump())
                crm_service.save_scheduled_message(final_message)
            else:
                print(f"  - FAILED: Could not generate AI draft for task '{touchpoint['name']}'")
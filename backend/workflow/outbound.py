# ---
# File Path: backend/workflow/outbound.py
# Purpose: This new service orchestrates the process of sending a campaign to its audience.
# ---
import uuid
from data import crm as crm_service
from integrations import twilio_outgoing

# --- MODIFIED: Added user_id for security ---
async def send_campaign_to_audience(campaign_id: uuid.UUID, user_id: uuid.UUID):
    """
    Fetches a campaign, personalizes the message for each recipient,
    sends it via Twilio, and updates the interaction timestamp.
    This function is now tenant-aware and requires a user_id.
    """
    print(f"OUTBOUND WORKFLOW: Starting send for campaign_id: {campaign_id} for user_id: {user_id}")
    
    # --- MODIFIED: Use secure CRM function ---
    campaign = crm_service.get_campaign_briefing_by_id(campaign_id, user_id=user_id)
    if not campaign:
        print(f"OUTBOUND WORKFLOW ERROR: Campaign {campaign_id} not found for user {user_id}.")
        return

    final_draft = campaign.edited_draft if campaign.edited_draft else campaign.original_draft
    if not final_draft:
        print(f"OUTBOUND WORKFLOW ERROR: Campaign {campaign_id} has no message content.")
        return

    audience = campaign.matched_audience
    if not audience:
        print(f"OUTBOUND WORKFLOW ERROR: Campaign {campaign_id} has no audience.")
        return

    success_count = 0
    failure_count = 0
    for recipient in audience:
        client_id_str = recipient.get("client_id")
        if not client_id_str:
            continue

        client_id = uuid.UUID(client_id_str)
        # --- MODIFIED: Use secure CRM function ---
        client = crm_service.get_client_by_id(client_id, user_id=user_id)
        if not client or not client.phone:
            print(f"OUTBOUND WORKFLOW WARNING: Client {client_id} not found for user {user_id} or has no phone. Skipping.")
            failure_count += 1
            continue
        
        personalized_message = final_draft.replace("[Client Name]", client.full_name.split(" ")[0])
        was_sent = twilio_outgoing.send_sms(to_number=client.phone, body=personalized_message)
        
        if was_sent:
            # --- MODIFIED: Use secure CRM function ---
            crm_service.update_last_interaction(client_id, user_id=user_id)
            success_count += 1
        else:
            failure_count += 1
            
    print(f"OUTBOUND WORKFLOW: Campaign send complete for {campaign_id}. Success: {success_count}, Failed: {failure_count}.")
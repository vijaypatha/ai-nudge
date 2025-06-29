# ---
# File Path: backend/workflow/outbound.py
# Purpose: This new service orchestrates the process of sending a campaign to its audience.
# ---
import uuid
from data import crm as crm_service
from integrations import twilio_outgoing

async def send_campaign_to_audience(campaign_id: uuid.UUID):
    """
    Fetches a campaign, personalizes the message for each recipient,
    and sends it via Twilio.

    Args:
        campaign_id: The UUID of the campaign to be sent.
    """
    print(f"OUTBOUND WORKFLOW: Starting send for campaign_id: {campaign_id}")
    
    # 1. Fetch the campaign from the database
    campaign = crm_service.get_campaign_briefing_by_id(campaign_id)
    if not campaign:
        print(f"OUTBOUND WORKFLOW ERROR: Campaign {campaign_id} not found.")
        return

    # 2. Determine the final message draft (use edited version if it exists)
    final_draft = campaign.edited_draft if campaign.edited_draft else campaign.original_draft
    if not final_draft:
        print(f"OUTBOUND WORKFLOW ERROR: Campaign {campaign_id} has no message draft.")
        return

    # 3. Get the audience and iterate
    audience = campaign.matched_audience
    if not audience:
        print(f"OUTBOUND WORKFLOW WARNING: Campaign {campaign_id} has no audience. Nothing to send.")
        return

    success_count = 0
    failure_count = 0

    for recipient in audience:
        # The audience is stored as a list of dictionaries
        client_id_str = recipient.get("client_id")
        if not client_id_str:
            continue

        client = crm_service.get_client_by_id(uuid.UUID(client_id_str))
        if not client or not client.phone:
            print(f"OUTBOUND WORKFLOW WARNING: Skipping client {client_id_str} - no phone number.")
            failure_count += 1
            continue

        # 4. Personalize the message by replacing the placeholder
        # Uses the client's first name for a more personal touch.
        personalized_message = final_draft.replace("[Client Name]", client.full_name.split(" ")[0])

        # 5. Send the final personalized SMS via the Twilio integration
        was_sent = twilio_outgoing.send_sms(to_number=client.phone, body=personalized_message)
        
        if was_sent:
            success_count += 1
        else:
            failure_count += 1
            
    print(f"OUTBOUND WORKFLOW: Campaign send complete for {campaign_id}. Success: {success_count}, Failed: {failure_count}.")
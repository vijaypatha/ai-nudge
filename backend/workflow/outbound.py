"""
File Path: backend/workflow/outbound.py
FINAL VERSION: Adds robust logging, error handling, and session management.
"""
import uuid
import logging
from sqlmodel import Session
from data.database import engine
from data import crm as crm_service
from integrations import twilio_outgoing

# Get a logger instance for this module
logger = logging.getLogger(__name__)

async def send_campaign_to_audience(campaign_id: uuid.UUID, user_id: uuid.UUID):
    """
    Fetches a campaign, personalizes the message for each recipient,
    sends it via Twilio, and updates the interaction timestamp within a
    single, safe transaction.
    """
    logger.info(f"OUTBOUND WORKFLOW: Starting send for campaign_id: {campaign_id} for user_id: {user_id}")
    
    # Use a single, consistent session for the entire task
    with Session(engine) as session:
        try:
            campaign = crm_service.get_campaign_briefing_by_id(campaign_id, user_id=user_id, session=session)
            if not campaign:
                logger.error(f"OUTBOUND WORKFLOW ERROR: Campaign {campaign_id} not found for user {user_id}.")
                return

            final_draft = campaign.edited_draft if campaign.edited_draft else campaign.original_draft
            if not final_draft or not final_draft.strip():
                logger.error(f"OUTBOUND WORKFLOW ERROR: Campaign {campaign_id} has no message content.")
                return

            audience = campaign.matched_audience
            if not audience:
                logger.error(f"OUTBOUND WORKFLOW ERROR: Campaign {campaign_id} has no audience.")
                return
            
            user = crm_service.get_user_by_id(user_id, session=session)
            if not user or not user.twilio_phone_number:
                logger.error(f"OUTBOUND WORKFLOW ERROR: User {user_id} has no Twilio number configured. Cannot send campaign.")
                return

            success_count = 0
            failure_count = 0
            for recipient in audience:
                client_id_str = recipient.get("client_id")
                if not client_id_str:
                    continue

                client = crm_service.get_client_by_id(uuid.UUID(client_id_str), user_id=user_id, session=session)
                if not client or not client.phone:
                    logger.warning(f"OUTBOUND WORKFLOW: Client {client_id_str} not found or has no phone. Skipping.")
                    failure_count += 1
                    continue
                
                # Personalize the message with the client's first name
                first_name = client.full_name.split(" ")[0] if client.full_name else "there"
                personalized_message = final_draft.replace("[Client Name]", first_name)
                
                was_sent = twilio_outgoing.send_sms(
                    from_number=user.twilio_phone_number,
                    to_number=client.phone, 
                    body=personalized_message
                )
                
                if was_sent:
                    crm_service.update_last_interaction(client.id, user_id=user_id, session=session)
                    success_count += 1
                else:
                    failure_count += 1
            
            # Commit all last_interaction updates at the end
            session.commit()
            
            logger.info(f"OUTBOUND WORKFLOW: Campaign send complete for {campaign_id}. Success: {success_count}, Failed: {failure_count}.")

        except Exception as e:
            logger.error(f"OUTBOUND WORKFLOW: A critical error occurred while sending campaign {campaign_id}. Error: {e}", exc_info=True)
            session.rollback()
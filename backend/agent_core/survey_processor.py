# File Path: backend/agent_core/survey_processor.py
# Purpose: Processes survey responses and extracts structured preferences and tags

import logging
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime, timezone
from sqlmodel import Session, select

from data.models.client import Client, ClientIntakeSurvey
from data.models.user import User
from agent_core.survey_config import get_survey_config, SurveyConfig
from agent_core import llm_client
from data import crm as crm_service
from agent_core.semantic_service import update_client_embedding

logger = logging.getLogger(__name__)

async def process_survey_responses(survey_id: str, session: Session) -> bool:
    """
    Process survey responses by triggering the main AI synthesis engine.
    Returns True if processing was successful.
    """
    try:
        survey = session.exec(select(ClientIntakeSurvey).where(ClientIntakeSurvey.id == survey_id)).first()
        if not survey:
            logger.error(f"SURVEY PROCESSOR: Survey {survey_id} not found")
            return False

        client = session.exec(select(Client).where(Client.id == survey.client_id)).first()
        user = session.exec(select(User).where(User.id == survey.user_id)).first()
        
        if not client or not user:
            logger.error(f"SURVEY PROCESSOR: Client or user not found for survey {survey_id}")
            return False

        # 1. Mark the survey as completed and processed.
        survey.processed = True
        survey.completed_at = datetime.now(timezone.utc).isoformat()
        client.intake_survey_completed = True
        
        session.add(survey)
        session.add(client)
        session.commit()
        
        # --- THIS IS THE FIX ---
        # Refresh the client object to load the newly saved survey relationship
        # before passing it to the synthesis engine.
        session.refresh(client)
        # --- END FIX ---
        
        # 2. Call the main, centralized AI synthesis engine from crm.py.
        logger.info(f"SURVEY PROCESSOR: Triggering main AI synthesis for client {client.id} after survey completion.")
        await crm_service._run_synthesis_and_update_client(client, user, session)
        
        logger.info(f"SURVEY PROCESSOR: Successfully processed survey {survey_id} for client {client.id}")
        return True
        
    except Exception as e:
        logger.error(f"SURVEY PROCESSOR: Error processing survey {survey_id}: {e}", exc_info=True)
        session.rollback()
        return False

def extract_preferences_from_responses(responses: Dict[str, Any], survey_config: SurveyConfig) -> Dict[str, Any]:
    """
    Extract structured preferences from survey responses using the survey configuration.
    """
    preferences = {}
    
    for question in survey_config.questions:
        if question.preference_key and question.id in responses:
            response_value = responses[question.id]
            
            # Handle different question types
            if question.type.value == "number":
                try:
                    preferences[question.preference_key] = int(response_value)
                except (ValueError, TypeError):
                    preferences[question.preference_key] = response_value
            elif question.type.value == "multi_select":
                # For multi-select, store as list
                if isinstance(response_value, list):
                    preferences[question.preference_key] = response_value
                else:
                    preferences[question.preference_key] = [response_value] if response_value else []
            else:
                # For text, select, boolean, etc.
                preferences[question.preference_key] = response_value
    
    return preferences

async def generate_tags_from_responses(responses: Dict[str, Any], survey_config: SurveyConfig, user_vertical: str) -> List[str]:
    """
    Generate relevant tags from survey responses using AI.
    """
    try:
        # Create a summary of responses for AI analysis
        response_summary = []
        for question in survey_config.questions:
            if question.id in responses:
                response_value = responses[question.id]
                if response_value:
                    if isinstance(response_value, list):
                        response_summary.append(f"{question.question}: {', '.join(response_value)}")
                    else:
                        response_summary.append(f"{question.question}: {response_value}")
        
        if not response_summary:
            return []
        
        summary_text = "\n".join(response_summary)
        
        # Generate tags using AI
        prompt = f"""
        You are analyzing survey responses for a {user_vertical} professional.
        
        Based on the following survey responses, generate 3-5 relevant tags that would help categorize and understand this client.
        Tags should be short, descriptive, and useful for matching with relevant opportunities or content.
        
        Survey responses:
        {summary_text}
        
        Generate tags as a JSON array of strings. Examples for real estate: ["first-time buyer", "luxury market", "family needs", "investment property"]
        Examples for therapy: ["anxiety", "first-time client", "work stress", "relationship issues"]
        
        Return only the JSON array, no other text.
        """
        
        response = await llm_client.get_chat_completion(
            prompt,
            temperature=0.3,
            json_response=True
        )
        
        if response:
            try:
                tags = json.loads(response)
                if isinstance(tags, list):
                    # Clean and validate tags
                    cleaned_tags = []
                    for tag in tags:
                        if isinstance(tag, str) and tag.strip():
                            cleaned_tags.append(tag.strip().lower())
                    return cleaned_tags[:5]  # Limit to 5 tags
            except json.JSONDecodeError:
                logger.warning(f"SURVEY PROCESSOR: Failed to parse AI-generated tags: {response}")
        
        return []
        
    except Exception as e:
        logger.error(f"SURVEY PROCESSOR: Error generating tags: {e}")
        return []

async def send_intake_survey(client_id: str, user_id: str, survey_type: str, session: Session) -> bool:
    """
    Send an intake survey to a client via SMS.
    """
    try:
        client = session.exec(select(Client).where(Client.id == client_id)).first()
        user = session.exec(select(User).where(User.id == user_id)).first()
        
        if not client or not user:
            logger.error(f"SURVEY PROCESSOR: Client or user not found")
            return False
        
        survey_config = get_survey_config(survey_type, user, session)
        if not survey_config:
            logger.error(f"SURVEY PROCESSOR: No config found for survey type {survey_type}")
            return False
        
        survey = ClientIntakeSurvey(
            client_id=client_id, user_id=user_id, survey_type=survey_type
        )
        session.add(survey)
        session.commit()
        session.refresh(survey)
        
        survey_message = generate_survey_message(client, user, survey_config, survey.id)
        
        from integrations import twilio_outgoing
        
        # --- THIS IS THE FIX ---
        # Removed 'await' because send_sms is a regular synchronous function.
        success = twilio_outgoing.send_sms(
            to_number=client.phone,
            from_number=user.twilio_phone_number,
            body=survey_message
        )
        # --- END FIX ---
        
        if success:
            client.intake_survey_sent_at = datetime.now(timezone.utc).isoformat()
            session.add(client)
            session.commit()
            logger.info(f"SURVEY PROCESSOR: Survey sent to client {client_id}")
            return True
        else:
            logger.error(f"SURVEY PROCESSOR: Failed to send survey to client {client_id}")
            return False
            
    except Exception as e:
        logger.error(f"SURVEY PROCESSOR: Error sending survey: {e}", exc_info=True)
        session.rollback()
        return False

def generate_survey_message(client: Client, user: User, survey_config: SurveyConfig, survey_id: str) -> str:
    """
    Generate the initial survey message to send to the client.
    """
    client_name = client.full_name.split()[0] if client.full_name else "there"
    
    # Use localhost for development, production domain for production
    import os
    base_url = os.getenv("SURVEY_BASE_URL", "http://localhost:3000")
    
    message = f"""Hi {client_name}! 👋

{user.full_name} would love to better understand your needs to provide the best service possible.

Could you take a quick {survey_config.estimated_time} survey? It will help us personalize our recommendations for you.

Click here to start: {base_url}/survey/{survey_id}

Or reply with "survey" and we'll send you the questions via text.

Thanks! 😊"""

    return message

import os

async def _send_agent_notification_email(user: User, client: Client, survey: ClientIntakeSurvey):
    """
    (Placeholder) Sends an email notification to the agent.
    NOTE: This requires a real email sending service (e.g., SendGrid, SES) to be implemented.
    """
    # Use environment variables for frontend URL
    frontend_base_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
    client_url = f"{frontend_base_url}/clients/{client.id}"
    
    subject = f"🚀 New Survey Completed: {client.full_name}"
    body = f"""Hi {user.full_name.split()[0]},

Great news! Your client, {client.full_name}, just completed their intake survey.

Their preferences and tags have been automatically updated in their profile. The system is already working to find them the best matches.

View their updated profile here:
{client_url}

This is a great time to review their new preferences and prepare for your next conversation.
"""
    
    # --- TODO: Replace this with your actual email sending logic ---
    logger.info("--- AGENT NOTIFICATION (SIMULATED) ---")
    logger.info(f"To: {user.email}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Body:\n{body}")
    logger.info("------------------------------------")
    # Example: await email_service.send(to=user.email, subject=subject, body=body)


async def handle_survey_response(client_id: str, survey_id: str, responses: Dict[str, Any], session: Session) -> bool:
    """
    Handle survey responses submitted by the client.
    """
    try:
        survey = session.exec(select(ClientIntakeSurvey).where(ClientIntakeSurvey.id == survey_id)).first()
        if not survey:
            logger.error(f"SURVEY PROCESSOR: Survey {survey_id} not found")
            return False
        
        if survey.completed_at:
            logger.warning(f"SURVEY PROCESSOR: Attempted to process already completed survey {survey_id}")
            return True

        survey.responses = responses
        session.add(survey)
        session.commit()
        
        success = await process_survey_responses(str(survey.id), session)
        
        if success:
            client = session.exec(select(Client).where(Client.id == survey.client_id)).first()
            user = session.exec(select(User).where(User.id == survey.user_id)).first()
            
            if client and user:
                from integrations import twilio_outgoing
                
                # 1. Send "Thank You" SMS to the client
                if client.phone and user.twilio_phone_number:
                    client_message = f"""Thank you for completing the survey! 🎉

We're already analyzing your preferences to find the perfect opportunities for you.

{user.full_name.split()[0]} will be in touch soon with your first set of personalized matches!"""
                    
                    # --- THIS IS THE FIX ---
                    twilio_outgoing.send_sms(
                        to_number=client.phone,
                        from_number=user.twilio_phone_number,
                        body=client_message
                    )
                
                # 2. Send notification SMS to the agent
                if user.phone_number and user.twilio_phone_number:
                    agent_message = f"🚀 New Survey: {client.full_name} just completed their intake survey. Their profile is updated and ready for review in your app."
                    
                    # --- THIS IS THE FIX ---
                    twilio_outgoing.send_sms(
                        to_number=user.phone_number,
                        from_number=user.twilio_phone_number,
                        body=agent_message
                    )
                else:
                    logger.warning(f"SURVEY PROCESSOR: Agent {user.id} cannot receive SMS notification. Missing phone_number or twilio_phone_number.")

        return success
        
    except Exception as e:
        logger.error(f"SURVEY PROCESSOR: Error handling survey response for survey_id {survey_id}: {e}", exc_info=True)
        session.rollback()
        return False
# File Path: backend/agent_core/survey_processor.py
# Purpose: Processes survey responses and extracts structured preferences and tags

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from sqlmodel import Session, select

from data.models.client import Client, ClientIntakeSurvey
from data.models.user import User
from agent_core.survey_config import get_survey_config, SurveyConfig
from agent_core import llm_client
from data import crm as crm_service
from agent_core.semantic_service import update_client_embedding

logger = logging.getLogger(__name__)

def _safe_get_first_name(full_name: str | None) -> str:
    """Safely extracts the first name from a full name string."""
    if not full_name or not full_name.strip():
        return "The team"
    return full_name.strip().split()[0]

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
        
        # Refresh the client object to load the newly saved survey relationship
        # before passing it to the synthesis engine.
        session.refresh(client)
        
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
            
            if question.type.value == "number":
                try:
                    preferences[question.preference_key] = int(response_value)
                except (ValueError, TypeError):
                    preferences[question.preference_key] = response_value
            elif question.type.value == "multi_select":
                if isinstance(response_value, list):
                    preferences[question.preference_key] = response_value
                else:
                    preferences[question.preference_key] = [response_value] if response_value else []
            else:
                preferences[question.preference_key] = response_value
    
    return preferences

async def generate_tags_from_responses(responses: Dict[str, Any], survey_config: SurveyConfig, user_vertical: str) -> List[str]:
    """
    Generate relevant tags from survey responses using AI.
    """
    try:
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
                    cleaned_tags = []
                    for tag in tags:
                        if isinstance(tag, str) and tag.strip():
                            cleaned_tags.append(tag.strip().lower())
                    return cleaned_tags[:5]
            except json.JSONDecodeError:
                logger.warning(f"SURVEY PROCESSOR: Failed to parse AI-generated tags: {response}")
        
        return []
        
    except Exception as e:
        logger.error(f"SURVEY PROCESSOR: Error generating tags: {e}")
        return []

async def send_intake_survey(client_id: str, user_id: str, template_id: str, session: Session, custom_message: Optional[str] = None) -> bool:
    """
    Send an intake survey to a client via SMS using a SurveyTemplate.
    Can now accept an optional custom message to override the default.
    """
    from data.models.survey import SurveyTemplate

    try:
        client = session.get(Client, client_id)
        user = session.get(User, user_id)
        template = session.get(SurveyTemplate, template_id)

        if not client or not user or not template:
            logger.error(f"Survey Processor: Client, user, or template not found.")
            return False

        survey = ClientIntakeSurvey(
            client_id=client_id, user_id=user_id, template_id=template_id
        )
        session.add(survey)
        session.commit()
        session.refresh(survey)

        survey_message = generate_survey_message(client, user, template, survey.id, custom_message)

        from integrations import twilio_outgoing

        success = twilio_outgoing.send_sms(
            to_number=client.phone,
            from_number=user.twilio_phone_number,
            body=survey_message
        )

        if success:
            client.intake_survey_sent_at = datetime.now(timezone.utc).isoformat()
            session.add(client)
            session.commit()
            logger.info(f"Survey from template {template_id} sent to client {client_id}")
            return True
        else:
            logger.error(f"Failed to send survey to client {client_id}")
            return False

    except Exception as e:
        logger.error(f"Error sending survey: {e}", exc_info=True)
        session.rollback()
        return False

def generate_survey_message(client: Client, user: User, template: "SurveyTemplate", survey_id: str, custom_message: Optional[str] = None) -> str:
    """
    Generate the survey message. Uses the custom message if provided, otherwise falls back to a default.
    """
    import os
    base_url = os.getenv("SURVEY_BASE_URL", "http://localhost:3000")
    survey_link = f"{base_url}/survey/{survey_id}"

    if custom_message and custom_message.strip():
        return f"{custom_message.strip()}\n{survey_link}"

    client_first_name = _safe_get_first_name(client.full_name)
    return f"""Hi {client_first_name},

To help personalize my service for you, please take a moment to fill out this short survey: {template.name}

{survey_link}

Thank you,
{_safe_get_first_name(user.full_name)}"""

async def _send_agent_notification_email(user: User, client: Client, survey: ClientIntakeSurvey):
    """
    (Placeholder) Sends an email notification to the agent.
    """
    import os
    frontend_base_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
    client_url = f"{frontend_base_url}/clients/{client.id}"
    
    agent_first_name = _safe_get_first_name(user.full_name)
    subject = f"New Survey Completed: {client.full_name}"
    body = f"""Hi {agent_first_name},

Great news! Your client, {client.full_name}, just completed their intake survey.

Their preferences and tags have been automatically updated in their profile. The system is already working to find them the best matches.

View their updated profile here:
{client_url}

This is a great time to review their new preferences and prepare for your next conversation.
"""
    
    logger.info("--- AGENT NOTIFICATION (SIMULATED) ---")
    logger.info(f"To: {user.email}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Body:\n{body}")
    logger.info("------------------------------------")

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
                
                agent_first_name = _safe_get_first_name(user.full_name)

                if client.phone and user.twilio_phone_number:
                    client_message = f"""Thank you for completing the survey. Your responses have been received. {agent_first_name} will review your information and be in touch with you shortly."""
                    
                    twilio_outgoing.send_sms(
                        to_number=client.phone,
                        from_number=user.twilio_phone_number,
                        body=client_message
                    )
                
                if user.phone_number and user.twilio_phone_number:
                    agent_message = f"New Survey: {client.full_name} just completed their intake survey. Their profile is updated and ready for review in your app."
                    
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
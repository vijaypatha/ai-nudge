# File Path: backend/api/rest/surveys.py
# Purpose: API endpoints for survey management, now including custom question CRUD.

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select
from pydantic import BaseModel


from data.database import get_session
from data.models.user import User
from data.models.client import Client, ClientIntakeSurvey
from data.models.survey import SurveyQuestion, SurveyQuestionCreate, SurveyQuestionUpdate
from data import crm as crm_service
from api.rest.auth import get_current_user_from_token
from agent_core.survey_config import get_survey_config, get_available_surveys, determine_survey_type
from agent_core.survey_processor import send_intake_survey, handle_survey_response

router = APIRouter(prefix="/surveys", tags=["surveys"])
logger = logging.getLogger(__name__)

# --- NEW: Pydantic models for the survey submission response ---
class QuestionAnswerPair(BaseModel):
    question: str
    answer: Any

class SurveySubmissionResponse(BaseModel):
    id: UUID
    completed_at: str
    survey_title: str
    questions_and_answers: List[QuestionAnswerPair]

class SendSurveyPayload(BaseModel):
    survey_type: Optional[str] = None

@router.get("/client/{client_id}", response_model=List[SurveySubmissionResponse])
async def get_surveys_for_client(
    client_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Gets all completed survey submissions for a specific client."""
    client = crm_service.get_client_by_id(client_id, current_user.id, session)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    surveys = session.exec(
        select(ClientIntakeSurvey)
        .where(ClientIntakeSurvey.client_id == client_id, ClientIntakeSurvey.completed_at != None)
        .order_by(ClientIntakeSurvey.completed_at.desc())
    ).all()

    response = []
    for survey in surveys:
        config = get_survey_config(survey.survey_type, current_user, session)
        if not config or not survey.completed_at:
            continue

        qa_pairs = []
        for question in config.questions:
            answer = survey.responses.get(question.id, "No answer")
            qa_pairs.append(QuestionAnswerPair(question=question.question, answer=answer))
        
        response.append(
            SurveySubmissionResponse(
                id=survey.id,
                completed_at=survey.completed_at,
                survey_title=config.title,
                questions_and_answers=qa_pairs
            )
        )
    return response

@router.get("/config/{survey_type}")
async def get_survey_config_endpoint(
    survey_type: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Get survey configuration. Returns user's custom config if it exists,
    otherwise returns the system default.
    """
    config = get_survey_config(survey_type, current_user, session)
    if not config:
        raise HTTPException(status_code=404, detail="Survey type not found")
    
    return {
        "survey_type": config.survey_type,
        "title": config.title,
        "description": config.description,
        "estimated_time": config.estimated_time,
        "questions": [
            {
                "id": q.id,
                "type": q.type.value,
                "question": q.question,
                "required": q.required,
                "options": q.options,
                "placeholder": q.placeholder,
                "help_text": q.help_text,
                "preference_key": q.preference_key
            } for q in config.questions
        ]
    }

# --- NEW: Endpoints for managing custom survey questions ---

@router.get("/custom-questions/{survey_type}", response_model=List[SurveyQuestion])
async def get_custom_questions(
    survey_type: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get all custom questions for a specific survey type for the current user."""
    stmt = select(SurveyQuestion).where(
        SurveyQuestion.user_id == current_user.id,
        SurveyQuestion.survey_type == survey_type
    ).order_by(SurveyQuestion.display_order)
    questions = session.exec(stmt).all()
    return questions

@router.post("/custom-questions", response_model=SurveyQuestion)
async def create_custom_question(
    question_data: SurveyQuestionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Create a new custom survey question."""
    db_question = SurveyQuestion.model_validate(question_data, update={"user_id": current_user.id})
    session.add(db_question)
    session.commit()
    session.refresh(db_question)
    return db_question

@router.put("/custom-questions/{question_id}", response_model=SurveyQuestion)
async def update_custom_question(
    question_id: UUID,
    question_data: SurveyQuestionUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Update an existing custom survey question."""
    db_question = session.get(SurveyQuestion, question_id)
    if not db_question or db_question.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Question not found")
    
    update_dict = question_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_question, key, value)
    
    session.add(db_question)
    session.commit()
    session.refresh(db_question)
    return db_question

@router.delete("/custom-questions/{question_id}", status_code=204)
async def delete_custom_question(
    question_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Delete a custom survey question."""
    db_question = session.get(SurveyQuestion, question_id)
    if not db_question or db_question.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Question not found")
        
    session.delete(db_question)
    session.commit()
    return

# --- Existing Endpoints ---

@router.get("/available")
async def get_available_surveys_endpoint(
    current_user: User = Depends(get_current_user_from_token)
):
    """Get a list of available survey types relevant to the current user."""
    survey_types = get_available_surveys(user=current_user)
    return {"survey_types": survey_types}

@router.post("/send/{client_id}")
async def send_survey_endpoint(
    client_id: UUID,
    payload: SendSurveyPayload, # Use the Pydantic model for the body
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Send an intake survey to a client, allowing for manual override."""
    client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == current_user.id)).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # --- THIS IS THE NEW LOGIC ---
    # Prioritize the agent's manual choice if it was provided.
    if payload and payload.survey_type:
        final_survey_type = payload.survey_type
        logger.info(f"SURVEYS API: Using manual override survey type '{final_survey_type}' for client {client_id}")
    else:
        # Otherwise, use the smart default logic.
        final_survey_type = determine_survey_type(current_user.vertical, client.user_tags)
    # --- END NEW LOGIC ---

    if not final_survey_type:
        raise HTTPException(status_code=400, detail="Could not determine a valid survey type for this client.")

    config = get_survey_config(final_survey_type, current_user, session)
    if not config:
        raise HTTPException(status_code=400, detail=f"Invalid survey type: {final_survey_type}")

    if not client.phone:
        raise HTTPException(status_code=400, detail="Client must have a phone number to receive surveys")

    if not current_user.twilio_phone_number:
        raise HTTPException(status_code=400, detail="User must have a Twilio phone number configured")

    # The send_intake_survey function is called with the determined survey type
    success = send_intake_survey(str(client.id), str(current_user.id), final_survey_type, session)

    if success:
        return {"message": "Survey sent successfully", "survey_type": final_survey_type}
    else:
        raise HTTPException(status_code=500, detail="Failed to send survey")

@router.post("/response/{survey_id}")
async def submit_survey_response_endpoint(
    survey_id: UUID,
    responses: Dict[str, Any],
    session: Session = Depends(get_session)
):
    """This endpoint is deprecated in favor of the public one but kept for potential internal uses."""
    survey = session.get(ClientIntakeSurvey, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    success = await handle_survey_response(str(survey.client_id), str(survey.id), responses, session)
    if success:
        return {"message": "Survey responses submitted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to process survey responses")

# --- Public Endpoints (No Authentication Required) ---

@router.get("/public/info/{survey_id}")
async def get_public_survey_info(survey_id: UUID, session: Session = Depends(get_session)):
    """Get public survey information for a specific survey ID."""
    survey = session.get(ClientIntakeSurvey, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found or invalid.")
    
    if survey.completed_at:
        raise HTTPException(status_code=410, detail="This survey has already been completed.")

    client = session.get(Client, survey.client_id)
    user = session.get(User, survey.user_id)
    
    if not client or not user:
        raise HTTPException(status_code=404, detail="Survey information not found.")

    return {
        "survey_id": str(survey.id),
        "client_name": client.full_name.split()[0] if client.full_name else "there",
        "user_name": user.full_name,
        "survey_type": survey.survey_type,
    }

@router.get("/public/config/{survey_type}")
async def get_public_survey_config(survey_type: str, survey_id: UUID, session: Session = Depends(get_session)):
    """Get public survey configuration. Requires a valid survey_id to fetch the correct user's config."""
    survey = session.get(ClientIntakeSurvey, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Invalid survey reference.")
    
    user = session.get(User, survey.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Survey owner not found.")
        
    config = get_survey_config(survey_type, user, session)
    if not config:
        raise HTTPException(status_code=404, detail="Survey type not found")
        
    return {
        "survey_type": config.survey_type,
        "title": config.title,
        "description": config.description,
        "estimated_time": config.estimated_time,
        "questions": [
            {
                "id": q.id, "type": q.type.value, "question": q.question, "required": q.required,
                "options": q.options, "placeholder": q.placeholder, "help_text": q.help_text,
                "preference_key": q.preference_key
            } for q in config.questions
        ]
    }

@router.post("/public/response/{survey_id}")
async def submit_public_survey_response(
    survey_id: UUID,
    responses: Dict[str, Any],
    session: Session = Depends(get_session)
):
    """Submit survey responses from a client (public endpoint)."""
    survey = session.get(ClientIntakeSurvey, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    if survey.completed_at:
        raise HTTPException(status_code=410, detail="Survey has already been completed.")

    success = await handle_survey_response(str(survey.client_id), str(survey.id), responses, session)
    if success:
        return {"message": "Survey responses submitted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to process survey responses")
    
@router.post("/manual-submission/{client_id}")
async def submit_manual_survey_response(
    client_id: UUID,
    responses: Dict[str, Any],
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Handles a survey submitted manually by an agent on behalf of a client.
    This creates the survey record and then triggers the main AI synthesis.
    """
    client = crm_service.get_client_by_id(client_id, current_user.id, session)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    survey_type = determine_survey_type(current_user.vertical, client.user_tags)
    if not survey_type:
        raise HTTPException(status_code=400, detail="Could not determine survey type for client.")

    # 1. Create the ClientIntakeSurvey record, just like the client-led flow.
    survey = ClientIntakeSurvey(
        client_id=client_id,
        user_id=current_user.id,
        survey_type=survey_type,
        responses=responses,
        processed=True,
        completed_at=datetime.now(timezone.utc).isoformat()
    )
    session.add(survey)
    client.intake_survey_completed = True
    session.add(client)
    session.commit()
    session.refresh(client) # Refresh to load the new survey relationship

    # 2. Trigger the main AI synthesis engine.
    logger.info(f"SURVEYS API: Triggering AI synthesis for manual submission for client {client.id}")
    await crm_service._run_synthesis_and_update_client(client, current_user, session)
    
    return {"status": "success", "message": "Manual survey submitted and processed."}
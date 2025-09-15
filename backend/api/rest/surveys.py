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
# MODIFIED: Import new models
from data.models.survey import (
    SurveyTemplate, SurveyTemplateCreate, SurveyTemplateUpdate,
    SurveyQuestion, SurveyQuestionCreate, SurveyQuestionUpdate
)
from data import crm as crm_service
from api.rest.auth import get_current_user_from_token
from agent_core.survey_config import get_survey_config, get_available_surveys, determine_survey_type
from agent_core.survey_processor import send_intake_survey, handle_survey_response

router = APIRouter(prefix="/surveys", tags=["surveys"])
logger = logging.getLogger(__name__)

# --- Survey Library (Template) Management ---

@router.get("/templates", response_model=List[SurveyTemplate])
async def get_survey_templates(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get all survey templates for the current user's library."""
    stmt = select(SurveyTemplate).where(SurveyTemplate.user_id == current_user.id).order_by(SurveyTemplate.name)
    return session.exec(stmt).all()

@router.post("/templates", response_model=SurveyTemplate)
async def create_survey_template(
    template_data: SurveyTemplateCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Create a new survey template."""
    db_template = SurveyTemplate.model_validate(template_data, update={"user_id": current_user.id})
    session.add(db_template)
    session.commit()
    session.refresh(db_template)
    return db_template

@router.get("/templates/{template_id}", response_model=SurveyTemplate)
async def get_survey_template(
    template_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get a single survey template by ID, including its questions."""
    stmt = select(SurveyTemplate).where(
        SurveyTemplate.id == template_id,
        SurveyTemplate.user_id == current_user.id
    )
    template = session.exec(stmt).first()
    if not template:
        raise HTTPException(status_code=404, detail="Survey template not found")
    # Eagerly load questions if they aren't loaded by default
    _ = template.questions
    return template

@router.put("/templates/{template_id}", response_model=SurveyTemplate)
async def update_survey_template(
    template_id: UUID,
    template_data: SurveyTemplateUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Update a survey template's metadata (name, description)."""
    db_template = session.get(SurveyTemplate, template_id)
    if not db_template or db_template.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Survey template not found")
    
    update_dict = template_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_template, key, value)
    
    session.add(db_template)
    session.commit()
    session.refresh(db_template)
    return db_template

@router.delete("/templates/{template_id}", status_code=204)
async def delete_survey_template(
    template_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Delete a survey template and all its associated questions."""
    db_template = session.get(SurveyTemplate, template_id)
    if not db_template or db_template.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Survey template not found")
        
    session.delete(db_template) # SQLAlchemy will handle cascading delete of questions
    session.commit()
    return

# --- Question Management (within a Template) ---

@router.post("/templates/{template_id}/questions", response_model=SurveyQuestion)
async def create_question_for_template(
    template_id: UUID,
    question_data: SurveyQuestionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Create a new question within a specific survey template."""
    db_template = session.get(SurveyTemplate, template_id)
    if not db_template or db_template.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Survey template not found")

    db_question = SurveyQuestion.model_validate(
        question_data,
        update={"user_id": current_user.id, "template_id": template_id}
    )
    session.add(db_question)
    session.commit()
    session.refresh(db_question)
    return db_question

@router.put("/questions/{question_id}", response_model=SurveyQuestion)
async def update_question(
    question_id: UUID,
    question_data: SurveyQuestionUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Update an existing survey question."""
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

@router.delete("/questions/{question_id}", status_code=204)
async def delete_question(
    question_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Delete a survey question."""
    db_question = session.get(SurveyQuestion, question_id)
    if not db_question or db_question.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Question not found")
        
    session.delete(db_question)
    session.commit()
    return

# --- Endpoints for Sending and Responding 
class SendSurveyPayload(BaseModel):
    template_id: UUID

class SendBulkSurveyPayload(BaseModel):
    template_id: UUID
    client_ids: List[UUID]

@router.post("/send-single/{client_id}")
async def send_single_survey(
    client_id: UUID,
    payload: SendSurveyPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token),
):
    """Send a single survey from a template to a specific client."""
    success = await send_intake_survey(str(client_id), str(current_user.id), str(payload.template_id), session)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send survey.")
    return {"status": "success", "message": "Survey sent successfully."}

@router.post("/send-bulk")
async def send_bulk_survey(
    payload: SendBulkSurveyPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token),
):
    """Send a single survey from a template to multiple clients."""
    if not payload.client_ids:
        raise HTTPException(status_code=400, detail="No client IDs provided.")

    success_count = 0
    failure_count = 0

    for client_id in payload.client_ids:
        success = await send_intake_survey(str(client_id), str(current_user.id), str(payload.template_id), session)
        if success:
            success_count += 1
        else:
            failure_count += 1

    return {
        "status": "complete",
        "message": f"Sent survey to {success_count} clients.",
        "failures": failure_count
    }

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

    # Eager load the template to get its name
    _ = survey.template

    return {
        "survey_id": str(survey.id),
        "client_name": client.full_name.split()[0] if client.full_name else "there",
        "user_name": user.full_name,
        "survey_type": survey.template.name, # Use template name for context
        "template_id": survey.template_id
    }

@router.get("/public/config/{template_id}")
async def get_public_survey_config(template_id: UUID, survey_id: UUID, session: Session = Depends(get_session)):
    """Get public survey configuration from a template. Requires a valid survey_id for authorization."""
    survey = session.get(ClientIntakeSurvey, survey_id)
    if not survey or survey.template_id != template_id:
        raise HTTPException(status_code=404, detail="Invalid survey reference.")

    template = session.get(SurveyTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Survey configuration not found.")

    return {
        "survey_type": template.name,
        "title": template.name,
        "description": template.description,
        "estimated_time": "2-3 minutes", # Can be added to template model later
        "questions": sorted([
            {
                "id": str(q.id), "type": q.question_type.value, "question": q.question_text, "required": q.is_required,
                "options": q.options, "placeholder": q.placeholder, "help_text": q.help_text
            } for q in template.questions
        ], key=lambda x: x.get('display_order', 0))
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
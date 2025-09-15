# File Path: backend/api/rest/surveys.py
# Purpose: API endpoints for all survey and question management.

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from data.database import get_session
from data.models.user import User
from data.models.client import Client, ClientIntakeSurvey
from data.models.survey import (
    SurveyTemplate, SurveyTemplateCreate, SurveyTemplateUpdate,
    SurveyQuestion, SurveyQuestionCreate, SurveyQuestionUpdate
)
from api.rest.auth import get_current_user_from_token
from agent_core.survey_processor import send_intake_survey, handle_survey_response

# --- Pydantic Models for API Data Structures ---

class AnswerInsight(BaseModel):
    answer: str
    count: int

class QuestionInsights(BaseModel):
    question_id: UUID
    question_text: str
    question_type: str
    total_responses: int
    answers: List[AnswerInsight]

class SurveyInsights(BaseModel):
    total_sends: int
    total_completions: int
    completion_rate: float
    question_insights: List[QuestionInsights]

class ReorderQuestionPayload(BaseModel):
    id: UUID
    display_order: int

class SendSurveyPayload(BaseModel):
    template_id: UUID

class SendBulkSurveyPayload(BaseModel):
    template_id: UUID
    client_ids: List[UUID]

# --- API Router ---

router = APIRouter(prefix="/surveys", tags=["surveys"])
logger = logging.getLogger(__name__)

# --- Survey Library (Template) Management ---

@router.get("/templates", response_model=List[SurveyTemplate])
async def get_survey_templates(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Fetches all survey templates for the current user's library."""
    stmt = select(SurveyTemplate).where(SurveyTemplate.user_id == current_user.id).order_by(SurveyTemplate.name)
    templates = session.exec(stmt).all()
    return templates

@router.post("/templates", response_model=SurveyTemplate)
async def create_survey_template(
    template_data: SurveyTemplateCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Creates a new, empty survey template in the user's library."""
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
    """Gets a single survey template by its ID, eagerly loading its questions."""
    stmt = select(SurveyTemplate).options(selectinload(SurveyTemplate.questions)).where(
        SurveyTemplate.id == template_id,
        SurveyTemplate.user_id == current_user.id
    )
    template = session.exec(stmt).first()
    if not template:
        raise HTTPException(status_code=404, detail="Survey template not found")
    return template

@router.put("/templates/{template_id}", response_model=SurveyTemplate)
async def update_survey_template(
    template_id: UUID,
    template_data: SurveyTemplateUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Updates a survey template's metadata, such as its name and description."""
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
    """Deletes a survey template and all of its associated questions."""
    db_template = session.get(SurveyTemplate, template_id)
    if not db_template or db_template.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Survey template not found")
        
    session.delete(db_template)
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
    """Creates a new question and associates it with a specific survey template."""
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
    """Updates the properties of an existing survey question."""
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
    """Deletes a single survey question."""
    db_question = session.get(SurveyQuestion, question_id)
    if not db_question or db_question.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Question not found")
        
    session.delete(db_question)
    session.commit()
    return

@router.post("/questions/reorder", status_code=204)
async def reorder_questions(
    payload: List[ReorderQuestionPayload],
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Updates the display order for a list of questions in a single batch operation."""
    if not payload:
        return

    question_ids = [item.id for item in payload]
    
    stmt = select(SurveyQuestion).where(
        SurveyQuestion.id.in_(question_ids),
        SurveyQuestion.user_id == current_user.id
    )
    questions_from_db = session.exec(stmt).all()

    if len(questions_from_db) != len(question_ids):
        raise HTTPException(status_code=403, detail="One or more questions not found or you don't have permission to edit them.")

    question_map = {q.id: q for q in questions_from_db}

    for item in payload:
        if item.id in question_map:
            question_to_update = question_map[item.id]
            question_to_update.display_order = item.display_order
            session.add(question_to_update)
    
    session.commit()
    return

# --- Endpoints for Sending Surveys ---

@router.post("/send-single/{client_id}")
async def send_single_survey(
    client_id: UUID,
    payload: SendSurveyPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token),
):
    """Sends a survey from a template to a single, specific client."""
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
    """Sends a survey from a template to a list of clients."""
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
    """Gets public information for a client to view before starting a survey."""
    survey = session.get(ClientIntakeSurvey, survey_id)
    if not survey or survey.completed_at:
        raise HTTPException(status_code=404, detail="Survey not found, invalid, or already completed.")

    client = session.get(Client, survey.client_id)
    user = session.get(User, survey.user_id)
    if not client or not user:
        raise HTTPException(status_code=404, detail="Survey information not found.")
    
    _ = survey.template # Eagerly load the template to get its name

    return {
        "survey_id": str(survey.id),
        "client_name": client.full_name.split()[0] if client.full_name else "there",
        "user_name": user.full_name,
        "survey_type": survey.template.name,
        "template_id": survey.template_id
    }

@router.get("/public/config/{template_id}")
async def get_public_survey_config(template_id: UUID, survey_id: UUID, session: Session = Depends(get_session)):
    """Gets the public configuration (questions, etc.) for a specific survey."""
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
        "estimated_time": "2-3 minutes",
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
    """Accepts and processes a client's submitted survey responses."""
    survey = session.get(ClientIntakeSurvey, survey_id)
    if not survey or survey.completed_at:
        raise HTTPException(status_code=404, detail="Survey not found or has already been completed.")

    success = await handle_survey_response(str(survey.client_id), str(survey.id), responses, session)
    if success:
        return {"message": "Survey responses submitted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to process survey responses")

# --- Analytics Endpoint ---

@router.get("/templates/{template_id}/insights", response_model=SurveyInsights)
async def get_survey_insights(
    template_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_from_token)
):
    """Calculates and returns analytics and aggregated responses for a survey template."""
    template = session.get(SurveyTemplate, template_id)
    if not template or template.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Template not found")

    sends_stmt = select(sa.func.count(ClientIntakeSurvey.id)).where(ClientIntakeSurvey.template_id == template_id)
    total_sends = session.exec(sends_stmt).one()

    completions_stmt = select(sa.func.count(ClientIntakeSurvey.id)).where(
        ClientIntakeSurvey.template_id == template_id,
        ClientIntakeSurvey.completed_at != None
    )
    total_completions = session.exec(completions_stmt).one()
    completion_rate = (total_completions / total_sends) * 100 if total_sends > 0 else 0

    completed_surveys_stmt = select(ClientIntakeSurvey).where(
        ClientIntakeSurvey.template_id == template_id,
        ClientIntakeSurvey.completed_at != None
    )
    completed_surveys = session.exec(completed_surveys_stmt).all()
    
    aggregated_answers = {str(q.id): {"text": q.question_text, "type": q.question_type, "answers": {}} for q in template.questions}

    for survey in completed_surveys:
        for q_id_str, response in survey.responses.items():
            if q_id_str in aggregated_answers:
                if isinstance(response, list):
                    for item in response:
                        aggregated_answers[q_id_str]["answers"][item] = aggregated_answers[q_id_str]["answers"].get(item, 0) + 1
                else:
                    response_str = str(response)
                    aggregated_answers[q_id_str]["answers"][response_str] = aggregated_answers[q_id_str]["answers"].get(response_str, 0) + 1

    question_insights = []
    for q_id_str, data in aggregated_answers.items():
        sorted_answers = sorted(
            [AnswerInsight(answer=ans, count=ct) for ans, ct in data["answers"].items()],
            key=lambda x: x.count, reverse=True
        )
        total_responses_for_question = sum(item.count for item in sorted_answers)
        question_insights.append(QuestionInsights(
            question_id=UUID(q_id_str),
            question_text=data["text"],
            question_type=data["type"],
            total_responses=total_responses_for_question,
            answers=sorted_answers
        ))

    return SurveyInsights(
        total_sends=total_sends,
        total_completions=total_completions,
        completion_rate=completion_rate,
        question_insights=question_insights
    )
# File Path: backend/agent_core/survey_config.py
# --- FINAL CORRECTED VERSION ---

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from sqlmodel import Session, select

from data.models.user import User
# NOTE: The import of UserSurveyQuestion is now moved inside the get_survey_config function

class QuestionType(Enum):
    TEXT = "text"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    RANGE = "range"
    BOOLEAN = "boolean"

@dataclass
class SurveyQuestion:
    id: str
    type: QuestionType
    question: str
    required: bool = False
    options: List[str] = field(default_factory=list)
    min_value: int = None
    max_value: int = None
    placeholder: str = None
    help_text: str = None
    preference_key: str = None

@dataclass
class SurveyConfig:
    survey_type: str
    title: str
    description: str
    questions: List[SurveyQuestion]
    estimated_time: str = "2-3 minutes"
    auto_send_delay_hours: int = 24

# --- DEFAULT SURVEY DEFINITIONS ---

REAL_ESTATE_BUYER_SURVEY = SurveyConfig(
    survey_type="real_estate_buyer",
    title="Home Buying Preferences",
    description="Help us understand your home buying needs so we can find the perfect properties for you.",
    estimated_time="3-4 minutes",
    questions=[
        SurveyQuestion(
            id="timeline",
            type=QuestionType.SELECT,
            question="When are you looking to buy?",
            required=True,
            options=["ASAP (within 30 days)", "1-3 months", "3-6 months", "6-12 months", "Just exploring"],
            preference_key="buying_timeline"
        ),
        SurveyQuestion(
            id="budget_max",
            type=QuestionType.NUMBER,
            question="What's your maximum budget?",
            required=True,
            placeholder="e.g., 500000",
            help_text="Enter the maximum amount you're comfortable spending",
            preference_key="budget_max"
        ),
        SurveyQuestion(
            id="locations",
            type=QuestionType.MULTI_SELECT,
            question="Which areas are you interested in?",
            required=True,
            options=["Downtown", "Suburbs", "Rural", "Waterfront", "Mountain View", "City Center", "Family Neighborhood"],
            preference_key="locations"
        ),
        SurveyQuestion(
            id="bedrooms",
            type=QuestionType.SELECT,
            question="How many bedrooms do you need?",
            required=True,
            options=["Studio", "1", "2", "3", "4", "5+"],
            preference_key="min_bedrooms"
        ),
        SurveyQuestion(
            id="bathrooms",
            type=QuestionType.SELECT,
            question="How many bathrooms do you need?",
            required=True,
            options=["1", "1.5", "2", "2.5", "3", "3+"],
            preference_key="min_bathrooms"
        ),
        SurveyQuestion(
            id="property_type",
            type=QuestionType.MULTI_SELECT,
            question="What type of property are you looking for?",
            required=True,
            options=["Single Family Home", "Townhouse", "Condo", "Duplex", "Multi-family", "Land"],
            preference_key="property_types"
        ),
        SurveyQuestion(
            id="must_haves",
            type=QuestionType.MULTI_SELECT,
            question="What are your must-have features?",
            required=False,
            options=["Garage", "Backyard", "Pool", "Home Office", "Walk-in Closet", "Fireplace", "Hardwood Floors", "Updated Kitchen", "Good Schools"],
            preference_key="must_haves"
        ),
        SurveyQuestion(
            id="deal_breakers",
            type=QuestionType.MULTI_SELECT,
            question="What would be deal-breakers for you?",
            required=False,
            options=["No Parking", "Small Kitchen", "No Backyard", "High HOA Fees", "Busy Street", "Old HVAC", "Foundation Issues"],
            preference_key="deal_breakers"
        ),
        SurveyQuestion(
            id="communication_preference",
            type=QuestionType.SELECT,
            question="How would you prefer to communicate?",
            required=True,
            options=["Text messages", "Phone calls", "Email", "In-person meetings"],
            preference_key="communication_preference"
        ),
        SurveyQuestion(
            id="urgency",
            type=QuestionType.SELECT,
            question="How urgent is your home search?",
            required=True,
            options=["Very urgent - need to move soon", "Somewhat urgent - within a few months", "Not urgent - just exploring", "Very flexible timeline"],
            preference_key="urgency_level"
        )
    ]
)
REAL_ESTATE_SELLER_SURVEY = SurveyConfig(
    survey_type="real_estate_seller",
    title="Home Selling Preferences",
    description="Help us understand your selling needs so we can provide the best service.",
    estimated_time="2-3 minutes",
    questions=[
        SurveyQuestion(
            id="timeline",
            type=QuestionType.SELECT,
            question="When are you looking to sell?",
            required=True,
            options=["ASAP", "1-3 months", "3-6 months", "6-12 months", "Just exploring"],
            preference_key="selling_timeline"
        ),
        SurveyQuestion(
            id="property_address",
            type=QuestionType.TEXT,
            question="What's the address of the property you want to sell?",
            required=True,
            placeholder="123 Main St, City, State",
            preference_key="property_address"
        ),
        SurveyQuestion(
            id="expected_price",
            type=QuestionType.NUMBER,
            question="What's your expected selling price?",
            required=False,
            placeholder="e.g., 450000",
            help_text="Leave blank if you'd like a market analysis",
            preference_key="expected_price"
        ),
        SurveyQuestion(
            id="property_condition",
            type=QuestionType.SELECT,
            question="How would you describe your property's condition?",
            required=True,
            options=["Move-in ready", "Needs minor updates", "Needs major updates", "Fixer-upper"],
            preference_key="property_condition"
        ),
        SurveyQuestion(
            id="selling_reason",
            type=QuestionType.SELECT,
            question="What's your main reason for selling?",
            required=True,
            options=["Upgrading to larger home", "Downsizing", "Relocating", "Investment property", "Divorce", "Inheritance", "Other"],
            preference_key="selling_reason"
        ),
        SurveyQuestion(
            id="flexibility",
            type=QuestionType.SELECT,
            question="How flexible are you with the selling timeline?",
            required=True,
            options=["Very flexible", "Somewhat flexible", "Not very flexible", "Need to sell by specific date"],
            preference_key="timeline_flexibility"
        )
    ]
)

THERAPY_SURVEY = SurveyConfig(
    survey_type="therapy",
    title="Therapy Preferences",
    description="Help us understand your therapy needs so we can provide the most relevant support.",
    estimated_time="2-3 minutes",
    questions=[
        SurveyQuestion(
            id="primary_concern",
            type=QuestionType.MULTI_SELECT,
            question="What are your primary concerns?",
            required=True,
            options=["Anxiety", "Depression", "Stress", "Relationship issues", "Work/life balance", "Grief", "Trauma", "Self-esteem", "Family issues", "Other"],
            preference_key="primary_concerns"
        ),
        SurveyQuestion(
            id="therapy_experience",
            type=QuestionType.SELECT,
            question="What's your experience with therapy?",
            required=True,
            options=["First time", "Some experience", "Currently in therapy", "Extensive experience"],
            preference_key="therapy_experience"
        ),
        SurveyQuestion(
            id="preferred_approach",
            type=QuestionType.MULTI_SELECT,
            question="What therapy approaches interest you?",
            required=False,
            options=["CBT", "Mindfulness", "EMDR", "Talk therapy", "Solution-focused", "Trauma-informed", "No preference"],
            preference_key="preferred_approaches"
        ),
        SurveyQuestion(
            id="session_frequency",
            type=QuestionType.SELECT,
            question="How often would you like to meet?",
            required=True,
            options=["Weekly", "Bi-weekly", "Monthly", "As needed"],
            preference_key="session_frequency"
        ),
        SurveyQuestion(
            id="communication_preference",
            type=QuestionType.SELECT,
            question="How would you prefer to communicate between sessions?",
            required=True,
            options=["Text messages", "Email", "Phone calls", "No communication between sessions"],
            preference_key="communication_preference"
        ),
        SurveyQuestion(
            id="urgency",
            type=QuestionType.SELECT,
            question="How urgent is your need for support?",
            required=True,
            options=["Very urgent - need immediate support", "Somewhat urgent - within a few weeks", "Not urgent - just exploring", "Preventive care"],
            preference_key="urgency_level"
        )
    ]
)

SURVEY_REGISTRY: Dict[str, SurveyConfig] = {
    "real_estate_buyer": REAL_ESTATE_BUYER_SURVEY,
    "real_estate_seller": REAL_ESTATE_SELLER_SURVEY,
    "therapy": THERAPY_SURVEY,
}

def get_survey_config(survey_type: str, user: User, session: Session) -> Optional[SurveyConfig]:
    """
    Get survey configuration by type.
    MODIFIED: Returns the user's custom questions if they exist, otherwise falls back to the system default.
    """
    from data.models.survey import SurveyQuestion as UserSurveyQuestion

    # 1. Check if the user has any custom questions for this survey type.
    custom_questions_stmt = (
        select(UserSurveyQuestion)
        .where(UserSurveyQuestion.user_id == user.id, UserSurveyQuestion.survey_type == survey_type)
        .order_by(UserSurveyQuestion.display_order)
    )
    custom_questions = session.exec(custom_questions_stmt).all()

    default_config = SURVEY_REGISTRY.get(survey_type)
    if not default_config:
        return None

    # 2. If custom questions exist, use them exclusively.
    # The frontend is responsible for the initial "cloning" of defaults.
    if custom_questions:
        questions_from_db = [
            SurveyQuestion(
                id=str(q.id),
                type=q.question_type,
                question=q.question_text,
                required=q.is_required,
                options=q.options or [],
                placeholder=q.placeholder,
                help_text=q.help_text,
                preference_key=q.preference_key,
            )
            for q in custom_questions
        ]
        # Use the default title/description but the user's custom questions.
        return SurveyConfig(
            survey_type=default_config.survey_type,
            title=default_config.title,
            description=default_config.description,
            questions=questions_from_db,
            estimated_time=default_config.estimated_time,
        )
    
    # 3. If no custom questions exist, return the hardcoded system default.
    else:
        return default_config
    
def get_available_surveys(user: User) -> List[str]:
    """Get a list of available survey types filtered by the user's vertical."""
    if user.vertical == "real_estate":
        return ["real_estate_buyer", "real_estate_seller"]
    elif user.vertical == "therapy":
        return ["therapy"]
    return []

def determine_survey_type(user_vertical: str, client_tags: List[str] = None) -> Optional[str]:
    """Determine the appropriate survey type based on user vertical and client context."""
    if user_vertical == "real_estate":
        if client_tags and "seller" in [tag.lower() for tag in client_tags]:
            return "real_estate_seller"
        return "real_estate_buyer"
    elif user_vertical == "therapy":
        return "therapy"
    return None
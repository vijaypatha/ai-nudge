# FILE: backend/data/models/event.py
# --- DEFINITIVE FIX ---
# Adds the missing `user_id` field to the MarketEvent model. This is the
# root cause of the crash in the `process_unprocessed_events` task.

import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import Field, SQLModel, Column, JSON

class MarketEvent(SQLModel, table=True):
    """
    Represents a market event captured from an external tool (e.g., MLS).
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    
    # --- THIS IS THE FIX ---
    # The user_id field was missing, causing the AttributeError.
    # This field links the event to the user it belongs to.
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    # ---------------------

    event_type: str
    entity_id: str # The unique ID of the entity from the source system (e.g., ListingKey)
    entity_type: str = Field(default="property")
    
    payload: Dict[str, Any] = Field(sa_column=Column(JSON))
    
    market_area: str
    status: str = Field(default="unprocessed", index=True) # e.g., unprocessed, processed, error

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    processed_at: Optional[datetime] = Field(default=None)

class PipelineRun(SQLModel, table=True):
    """
    Tracks automated pipeline executions for status monitoring.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    
    pipeline_type: str = Field(default="main_opportunity_pipeline")  # e.g., main_opportunity_pipeline
    status: str = Field(default="running")  # running, completed, failed
    
    started_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Results summary
    events_processed: int = Field(default=0)
    campaigns_created: int = Field(default=0)
    errors: Optional[str] = Field(default=None)
    
    # Metadata
    duration_seconds: Optional[float] = Field(default=None)
    user_count: int = Field(default=0)
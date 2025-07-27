# FILE: backend/data/models/event.py
# --- DEFINITIVE FIX ---
# Adds the missing `user_id` field to the MarketEvent model. This is the
# root cause of the crash in the `process_unprocessed_events` task.

import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import Field, SQLModel, Column, JSON
from sqlalchemy import Column, Index

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

    event_type: str = Field(index=True) # Index for event type filtering
    entity_id: str = Field(index=True) # Index for entity lookup
    entity_type: str = Field(default="property")
    
    payload: Dict[str, Any] = Field(sa_column=Column(JSON))
    
    market_area: str
    status: str = Field(default="unprocessed", index=True) # e.g., unprocessed, processed, error

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True) # Index for sorting by date
    processed_at: Optional[datetime] = Field(default=None)

    # Add composite index for common query patterns
    __table_args__ = (
        Index('ix_marketevent_user_created', 'user_id', 'created_at'),  # For user's recent events
        Index('ix_marketevent_user_type', 'user_id', 'event_type'),  # For user's events by type
    )

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
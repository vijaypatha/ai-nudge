# FILE: backend/data/models/event.py
# --- UPDATED: Adds GlobalMlsEvent for the Global Event Pool strategy ---

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Column, JSON
from sqlalchemy import Column, Index, UniqueConstraint

class MarketEvent(SQLModel, table=True):
    """
    Represents a user-specific market event, generated from a GlobalMlsEvent.
    This is what the user sees in their feed.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)

    event_type: str = Field(index=True) # e.g., new_listing, price_change
    entity_id: str = Field(index=True) # The original ListingKey from the MLS
    entity_type: str = Field(default="property")
    
    payload: Dict[str, Any] = Field(sa_column=Column(JSON))
    
    market_area: str
    status: str = Field(default="unprocessed", index=True) # e.g., unprocessed, processed, error

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    processed_at: Optional[datetime] = Field(default=None)

    __table_args__ = (
        Index('ix_marketevent_user_created', 'user_id', 'created_at'),
        Index('ix_marketevent_user_type', 'user_id', 'event_type'),
    )

class PipelineRun(SQLModel, table=True):
    """
    Tracks automated pipeline executions for status monitoring.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    
    pipeline_type: str = Field(default="main_opportunity_pipeline")
    status: str = Field(default="running")
    
    started_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    completed_at: Optional[datetime] = Field(default=None)
    
    events_processed: int = Field(default=0)
    campaigns_created: int = Field(default=0)
    errors: Optional[str] = Field(default=None)
    
    duration_seconds: Optional[float] = Field(default=None)
    user_count: int = Field(default=0)

# --- NEW MODEL FOR GLOBAL EVENT POOL ---
class GlobalMlsEvent(SQLModel, table=True):
    """
    Stores raw, unprocessed events directly from an MLS feed.
    This table is user-agnostic and acts as the central source of truth.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)

    # Identifies the MLS data source, e.g., "flexmls_washington_county"
    source_id: str = Field(index=True)

    # The unique ID for the listing from the source MLS (e.g., ListingKey)
    listing_key: str = Field(index=True)
    
    # The raw, unmodified JSON payload from the MLS API
    raw_payload: Dict[str, Any] = Field(sa_column=Column(JSON))

    # The timestamp of the event from the source data (e.g., ModificationTimestamp)
    event_timestamp: datetime = Field(index=True)

    # Timestamp when this record was created in our system
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        # Ensures we don't store the exact same listing from the same source twice
        UniqueConstraint("source_id", "listing_key", name="ux_source_id_listing_key"),
    )
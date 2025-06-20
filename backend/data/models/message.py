# backend/data/models/message.py

from pydantic import BaseModel, Field # Import necessary Pydantic components
from typing import Optional, List, Literal # For optional fields, lists, and specific string values (like 'pending', 'sent')
import uuid # For generating unique IDs
from datetime import datetime, timezone # For handling dates and times accurately

# Define a Literal type for message status.
# This ensures that the 'status' field can only take one of these predefined string values.
MessageStatus = Literal["pending", "sent", "failed", "cancelled"]

class ScheduledMessage(BaseModel):
    """
    Represents a message that has been scheduled to be sent.
    This model defines the structure of a scheduled message entry in the system.
    """
    # A unique identifier for this scheduled message.
    # Field(default_factory=uuid.uuid4) automatically generates a new UUID
    # when a new ScheduledMessage object is created.
    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique ID for the scheduled message.")

    # The unique ID of the client this message is intended for.
    # This links the message back to a specific customer in your CRM.
    client_id: uuid.UUID = Field(description="The ID of the client this message is for.")

    # The content/text of the message to be sent.
    # 'min_length=1' ensures the message content is not empty.
    content: str = Field(min_length=1, description="The content of the message to be sent.")

    # The exact date and time when the message is scheduled to be sent.
    # It is best practice to store timestamps in UTC (Coordinated Universal Time)
    # to avoid timezone complexities.
    scheduled_at: datetime = Field(description="The UTC timestamp when the message is scheduled to be sent.")

    # The current status of the scheduled message.
    # It defaults to "pending" when a new message is scheduled.
    status: MessageStatus = Field("pending", description="Current status of the scheduled message.")

    # Optional: A timestamp recording when the message was actually sent.
    # This field is initially None and gets populated once the message is delivered.
    sent_at: Optional[datetime] = Field(None, description="The UTC timestamp when the message was actually sent.")

    # Optional: Any error message if sending failed.
    # This field helps in debugging issues if a scheduled message could not be delivered.
    error_message: Optional[str] = Field(None, description="Error message if the message sending failed.")

    # Timestamp for when this scheduled message record was created in the system.
    # 'default_factory=lambda: datetime.now(timezone.utc)' ensures this is set automatically
    # to the current UTC time when the object is created.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of when the message was scheduled.")

    # Pydantic configuration for additional settings.
    # 'from_attributes = True' allows Pydantic to create models from ORM objects,
    # which is useful if you later connect to a database like SQLAlchemy.
    model_config = {
        "from_attributes": True
    }

class ScheduledMessageCreate(BaseModel):
    """
    Represents the data required from the frontend (user) to schedule a new message.
    This model includes only the fields that are expected when a user wants to schedule a message.
    The 'id', 'status', 'sent_at', 'error_message', and 'created_at' fields are
    handled automatically by the backend upon creation.
    """
    # The unique ID of the client the message is for (required when scheduling).
    client_id: uuid.UUID = Field(description="The ID of the client to send the message to.")

    # The content of the message (required).
    content: str = Field(min_length=1, description="The text content of the message.")

    # The desired time to send the message (required).
    # The frontend should ideally send this in UTC, or the backend should convert it.
    scheduled_at: datetime = Field(description="The UTC timestamp when the message should be sent.")

class SendMessageImmediate(BaseModel):
    """
    Represents the data payload for sending a message without scheduling.
    This is used for immediate, ad-hoc messages triggered from the UI.
    """
    client_id: uuid.UUID = Field(description="The ID of the client to send the message to.")
    content: str = Field(min_length=1, description="The text content of the message.")

# --- ADD THIS CLASS ---
class IncomingMessage(BaseModel):
    """
    Represents the data payload for a message received from a client.
    This model is used by endpoints that process incoming communications.
    """
    client_id: uuid.UUID = Field(description="The ID of the client who sent the message.")
    content: str = Field(min_length=1, description="The text content of the incoming message.")
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import List, Optional
from datetime import datetime

class Client(BaseModel):
    id: str = Field(..., description="Unique identifier for the client", examples=["client-001"])
    name: str = Field(..., min_length=1, description="Full name of the client", examples=["Alice Wonderland"])
    email: Optional[EmailStr] = Field(None, description="Client's email address", examples=["alice@example.com"])
    phone: Optional[str] = Field(None, description="Client's phone number", examples=["555-123-4567"])
    notes: Optional[str] = Field(None, description="General notes or preferences about the client")

class Property(BaseModel):
    id: str = Field(..., description="Unique identifier for the property", examples=["prop-abc-123"])
    address: str = Field(..., min_length=5, description="Full address of the property", examples=["123 Main St, Anytown, USA"])
    price: float = Field(..., gt=0, description="Listing price of the property", examples=[500000.00])
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms", examples=[3])
    bathrooms: float = Field(..., ge=0, description="Number of bathrooms (e.g., 2.5 for 2 full, 1 half)", examples=[2.5])
    sqft: Optional[int] = Field(None, gt=0, description="Square footage of the property", examples=[1800])
    description: Optional[str] = Field(None, description="Detailed description of the property")
    image_url: Optional[HttpUrl] = Field(None, description="URL for the property image", examples=["https://via.placeholder.com/300x200.png?text=Property+Image"])

class Message(BaseModel):
    id: str = Field(..., description="Unique message identifier", examples=["msg-xyz-789"])
    thread_id: Optional[str] = Field(None, description="Identifier for a conversation thread")
    sender_id: str = Field(..., description="ID of the sender (e.g., client ID or 'agent')", examples=["client-001"])
    receiver_id: str = Field(..., description="ID of the receiver (e.g., 'agent' or client ID)", examples=["agent-user-007"])
    content: str = Field(..., min_length=1, description="Text content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the message was created or received")
    is_ai_assisted: bool = Field(False, description="Flag indicating if AI assisted in drafting or sending this message")

class ScheduledMessage(BaseModel):
    id: str = Field(..., description="Unique ID for the scheduled message task", examples=["sched-msg-001"])
    recipient_id: str = Field(..., description="ID of the recipient (client ID)", examples=["client-002"])
    message_content: str = Field(..., min_length=1, description="Content of the message to be sent")
    scheduled_time: datetime = Field(..., description="The specific date and time the message is scheduled to be sent")
    status: str = Field("pending", description="Status of the scheduled message (e.g., pending, sent, failed, cancelled)", examples=["pending"])

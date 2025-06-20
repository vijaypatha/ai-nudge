# backend/data/models/client.py

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import uuid

# This BaseModel provides the structure for a client's core data.
# It uses Pydantic for data validation, ensuring consistency.
class Client(BaseModel):
    # A unique identifier for the client.
    # We use UUID (Universally Unique Identifier) to ensure it's truly unique.
    # Field(default_factory=uuid.uuid4) automatically generates a new UUID
    # when a new client object is created, making it unique across your system.
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

    # The client's full name.
    # The 'min_length' ensures that a name is not empty.
    full_name: str = Field(min_length=1, description="The full name of the client.")

    # The client's email address.
    # EmailStr is a Pydantic type that validates the string as a valid email format.
    email: EmailStr = Field(description="The primary email address of the client.")

    # The client's phone number.
    # Optional means this field might not always be present.
    # Using str for now, but could be validated with a regex later for specific formats.
    phone: Optional[str] = Field(None, description="The primary phone number of the client.")

    # A list of tags associated with the client.
    # Tags can be used for categorization (e.g., "hot lead", "buyer", "seller").
    # The default is an empty list, meaning a client can have no tags initially.
    tags: List[str] = Field(default_factory=list, description="A list of tags associated with the client.")

    # A simple field to store some basic interaction history (e.g., last message date).
    # This will be expanded later, but provides a placeholder for now.
    # Optional means it can be omitted.
    last_interaction: Optional[str] = Field(None, description="A simple record of the last interaction date/time.")


# This BaseModel is used specifically when creating a *new* client.
# It includes only the fields that are expected when a user wants to add a client.
# The 'id' field is omitted here because it will be generated automatically by the system.
class ClientCreate(BaseModel):
    # The client's full name, required for creation.
    full_name: str = Field(min_length=1, description="The full name of the client.")

    # The client's email address, required for creation.
    email: EmailStr = Field(description="The primary email address of the client.")

    # Optional phone number during creation.
    phone: Optional[str] = Field(None, description="The primary phone number of the client.")

    # Optional tags during creation.
    tags: List[str] = Field(default_factory=list, description="A list of tags associated with the client.")
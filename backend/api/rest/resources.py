# File Path: backend/api/rest/resources.py
# --- FINAL VERSION: Correctly wired to your existing crm.py service functions.

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

# --- Imports now match your existing structure ---
from data.models.resource import Resource, ResourceCreate, ResourceUpdate
from data.models.user import User
from api.security import get_current_user
from data import crm as resource_service # Using crm.py as the service layer

# --- Router definition remains the same ---
router = APIRouter(prefix="/resources", tags=["Resources"])

@router.post("/", response_model=Resource, status_code=201)
def create_resource(
    resource_data: ResourceCreate,
    current_user: User = Depends(get_current_user)
):
    """Creates a new generic resource linked to the authenticated user."""
    try:
        # CORRECT: Calls the synchronous 'create_resource' function from crm.py
        new_resource = resource_service.create_resource(
            user_id=current_user.id,
            resource_data=resource_data
        )
        return new_resource
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create resource.")

@router.get("/", response_model=List[Resource])
def get_all_resources_for_user(current_user: User = Depends(get_current_user)):
    """Gets all resources associated with the authenticated user."""
    try:
        # CORRECT: Calls the 'get_all_resources_for_user' function from crm.py
        return resource_service.get_all_resources_for_user(user_id=current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch resources.")

@router.patch("/{resource_id}", response_model=Resource)
def update_resource(
    resource_id: UUID,
    update_data: ResourceUpdate,
    current_user: User = Depends(get_current_user)
):
    """Updates a resource's status or attributes, serving as a generic AI trigger."""
    try:
        # CORRECT: Calls the synchronous 'update_resource' function from crm.py
        updated_resource = resource_service.update_resource(
            resource_id=resource_id,
            user_id=current_user.id,
            update_data=update_data
        )
        if not updated_resource:
            raise HTTPException(status_code=404, detail="Resource not found or access denied.")

        # --- AI TRIGGER HOOK ---
        print(f"INFO: Update trigger for resource {resource_id} processed.")
        return updated_resource
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resource ID format.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during the update.")
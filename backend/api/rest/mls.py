# backend/api/rest/mls.py
# MLS API endpoints for testing connections and managing MLS integrations

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from data.models.user import User
from api.security import get_current_user_from_token
from data.database import engine
from integrations.mls.factory import get_mls_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mls", tags=["MLS"])

@router.get("/test-connection")
async def test_mls_connection(
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Test the MLS connection using the configured API credentials
    """
    try:
        # Get the MLS client for the current user
        mls_client = get_mls_client(current_user)
        
        if not mls_client:
            raise HTTPException(
                status_code=400, 
                detail="No MLS provider configured. Please check your MLS_PROVIDER setting."
            )
        
        # Test authentication
        is_authenticated = mls_client.authenticate()
        
        if not is_authenticated:
            raise HTTPException(
                status_code=401, 
                detail="MLS authentication failed. Please check your API credentials."
            )
        
        # Test a simple API call to verify the connection works
        # Get events from the last 24 hours to test the connection
        events = mls_client.get_events(minutes_ago=1440)  # 24 hours
        
        logger.info(f"MLS connection test successful for user {current_user.id}. Found {len(events)} events.")
        
        return {
            "success": True,
            "message": "MLS connection successful",
            "events_found": len(events),
            "provider": current_user.tool_provider or "flexmls_reso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MLS connection test failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"MLS connection test failed: {str(e)}"
        ) 
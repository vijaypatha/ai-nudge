# File Path: backend/api/webhooks/mls.py
# Purpose: MLS webhook endpoints

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class MLSWebhookPayload(BaseModel):
    """MLS webhook payload model"""
    property_id: Optional[str] = None
    event_type: Optional[str] = None
    mls_id: Optional[str] = None

@router.post("/property-updates")
async def mls_property_updates_webhook(request: Request):
    """Handle property updates from MLS systems"""
    try:
        body = await request.json()
        # Process MLS property updates
        return {"status": "success", "message": "MLS property update processed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing MLS webhook: {str(e)}")

@router.post("/market-data")
async def mls_market_data_webhook(request: Request):
    """Handle market data updates from MLS systems"""
    try:
        body = await request.json()
        # Process market data updates
        return {"status": "success", "message": "Market data update processed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing market data: {str(e)}")

@router.get("/health")
async def mls_webhook_health():
    """Health check for MLS webhooks"""
    return {"status": "healthy", "service": "mls-webhooks"}

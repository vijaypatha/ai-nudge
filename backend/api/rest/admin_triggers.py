# ---
# File Path: backend/api/rest/admin_triggers.py
# Purpose: Developer endpoints to manually trigger backend processes.
# ---
from fastapi import APIRouter, status
from data import crm as crm_service
from agent_core.brain import relationship_engine

router = APIRouter(
    prefix="/admin/triggers", # Using a nested path for clarity
    tags=["Admin: Triggers"]
)

@router.post("/run-daily-scan", status_code=status.HTTP_202_ACCEPTED)
async def trigger_daily_scan():
    """
    Manually triggers the daily scan for relationship-based nudges.
    In production, this would be a scheduled cron job, not an API endpoint.
    """
    if not crm_service.mock_users_db:
        return {"status": "error", "message": "No users in database to run scan for."}

    realtor = crm_service.mock_users_db[0]
    await relationship_engine.generate_daily_relationship_nudges(realtor)

    return {"status": "accepted", "message": "Daily relationship scan initiated."}
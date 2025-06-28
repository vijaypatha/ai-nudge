# ---
# File Path: backend/api/rest/admin_triggers.py
# Purpose: Developer endpoints to manually trigger backend processes.
# ---
from fastapi import APIRouter, status, HTTPException
from data import crm as crm_service
from agent_core.brain import relationship_engine
from data.models.campaign import CampaignBriefing, MatchedClient


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

@router.post("/create-test-nudge", status_code=status.HTTP_201_CREATED)
async def create_test_nudge(count: int = 1):
    """
    (DEBUG ENDPOINT) Creates one or more hardcoded CampaignBriefings for testing.
    Use the '?count=' query parameter to create multiple nudges for the same event.
    """
    if not crm_service.mock_users_db or not crm_service.mock_properties_db:
        raise HTTPException(status_code=400, detail="Seed data must exist.")

    for i in range(count):
        test_user = crm_service.mock_users_db[0]
        test_property = crm_service.mock_properties_db[0]
        
        # This data will be used to create a consistent group for testing
        key_intel = {"Potential Commission": "$16,500 - $33,000", "Days on Market": "12 (vs 45 avg)"}
        headline = f"Price Drop: {test_property.address}"

        test_briefing = CampaignBriefing(
            user_id=test_user.id,
            campaign_type="price_drop",
            headline=headline,
            key_intel=key_intel,
            original_draft=f"Hi [Client Name], good news! A property you might like on Maple St just had a price drop. This is nudge #{i+1} in a test group.",
            matched_audience=[
                MatchedClient(client_id="a1b2c3d4-e5f6-a1b2-c3d4-e5f6a1b2c3d4", client_name="Alex Chen (Demo)", match_score=95, match_reason="Interested in this area.")
            ],
            triggering_event_id=test_property.id,
            status="new"
        )
        crm_service.save_campaign_briefing(test_briefing)
    
    return {"message": f"Successfully created {count} test nudge(s)."}
# File: find_targets.py
# --- REFACTORED: Uses the new generic tool factory ---

import os
import sys
import asyncio
from dotenv import load_dotenv

# --- Setup Environment ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'backend', '.env'))
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# --- CHANGE: Import the generic tool factory ---
from integrations.tool_factory import get_tool_for_user
from data.models.user import User # To create a dummy user

async def find_and_print_targets():
    print("--- Finding potential target properties from a generic tool... ---")
    
    # Create a dummy user object with the desired tool configured
    dummy_user = User(id=uuid.uuid4(), tool_provider="flexmls_spark")
    
    # --- CHANGE: Use the new generic factory ---
    tool = get_tool_for_user(dummy_user)
    if not tool:
        print("❌ Could not create tool. Check configuration and credentials.")
        return

    # Look back 3 days to get a good sample size
    print("Fetching events from the tool...")
    events = await asyncio.to_thread(tool.get_events, minutes_ago=4320)

    new_listings = [event.raw_data for event in events if event.event_type == 'new_listing']

    if not new_listings:
        print("❌ No recently updated 'new_listing' events found.")
        return

    print("\n✅ Found Targets! Choose one of these properties:\n" + "="*50)
    for i, listing in enumerate(new_listings[:5]): # Print the top 5
        s_fields = listing.get('StandardFields', {})
        print(f"\n--- TARGET {i+1} ---")
        print(f"  Address: {s_fields.get('UnparsedAddress', 'N/A')}")
        print(f"  Price: ${s_fields.get('ListPrice', 0):,}")
        print(f"  Bedrooms: {s_fields.get('BedroomsTotal', 'N/A')}")
        print(f"  Remarks: {s_fields.get('PublicRemarks', 'N/A')[:150]}...")
    print("\n" + "="*50)

if __name__ == "__main__":
    asyncio.run(find_and_print_targets())
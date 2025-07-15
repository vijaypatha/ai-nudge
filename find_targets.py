# File: find_targets.py
# Purpose: Fetches and prints a few recent listings to use as test targets.

import os
import sys
import asyncio
from dotenv import load_dotenv

# --- Setup Environment ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'backend', '.env'))
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from integrations.mls.factory import get_mls_client

async def find_and_print_targets():
    print("--- Finding potential target properties from MLS... ---")
    mls_client = get_mls_client()
    if not mls_client:
        print("❌ Could not create MLS client. Check credentials.")
        return

    # Look back 3 days to get a good sample size
    listings = mls_client.fetch_new_listings(minutes_ago=4320)

    if not listings:
        print("❌ No recently updated listings found.")
        return

    print("\n✅ Found Targets! Choose one of these properties:\n" + "="*50)
    for i, listing in enumerate(listings[:5]): # Print the top 5
        print(f"\n--- TARGET {i+1} ---")
        print(f"  Address: {listing.get('UnparsedAddress', 'N/A')}")
        print(f"  Price: ${listing.get('ListPrice', 0):,}")
        print(f"  Bedrooms: {listing.get('BedroomsTotal', 'N/A')}")
        print(f"  Remarks: {listing.get('PublicRemarks', 'N/A')[:150]}...")
    print("\n" + "="*50)

if __name__ == "__main__":
    asyncio.run(find_and_print_targets())
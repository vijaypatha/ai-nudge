# FILE: backend/test_mls_factory.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# --- FIX: Add Project Root to Python Path ---
# This ensures that imports like `from backend.integrations...` work correctly.
try:
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    sys.path.append(str(project_root))
    print(f"Project root added to path: {project_root}")
except NameError:
    print("Could not determine script path. Assuming running from `backend` directory.")
    sys.path.append('..')

# Load environment variables from .env file
print("Loading environment variables from .env file...")
load_dotenv(dotenv_path=Path(__file__).resolve().parent / '.env')

# Now that the path is set, we can import our modules
from backend.integrations.mls.factory import get_mls_client

def test_integration():
    """Tests the full flow: Factory -> Authenticate -> Fetch"""
    print("\n--- Starting MLS Integration Test ---")
    mls_client = get_mls_client()
    
    if not mls_client:
        print("TEST FAILED: Could not create MLS client from factory.")
        return

    print(f"Successfully created client: {mls_client.__class__.__name__}")
    
    print("\nAttempting to authenticate...")
    if mls_client.authenticate():
        print("AUTHENTICATION SUCCESSFUL.")
        
        print("\nAttempting to fetch new listings (last 24 hours)...")
        new_listings = mls_client.fetch_new_listings(minutes_ago=1440)
        
        if new_listings is not None:
            print(f"FETCH SUCCEEDED. Found {len(new_listings)} new listings.")
            if new_listings:
                print("Sample listing:", new_listings[0])
        else:
            print("FETCH FAILED. Check logs for errors.")
    else:
        print("AUTHENTICATION FAILED. Check credentials and API logs.")

    print("\n--- Test Complete ---")

if __name__ == "__main__":
    required_vars = ["MLS_PROVIDER", "SPARK_API_DEMO_TOKEN"]
    if all(os.getenv(v) for v in required_vars):
        test_integration()
    else:
        print("TEST SKIPPED: Please ensure required variables are set in your .env file.")
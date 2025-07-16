# FILE: backend/debug_spark_api.py
# --- DEFINITIVE VERSION ---
# This script makes the simplest possible valid request to the /listings
# endpoint to conclusively test the API token and filter syntax.

import os
import requests
from dotenv import load_dotenv

# Load environment variables from the backend's .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Configuration ---
TOKEN = os.getenv("SPARK_API_DEMO_TOKEN")
API_URL = "https://api.sparkapi.com/v1/listings" 

# A very simple, standard filter that should always be valid
PARAMS = {
    "_filter": "MlsStatus Eq 'Active'",
    "_limit": 1
}

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

def run_debug():
    """Executes the debug API call and prints the results."""
    print("--- Running Final Spark API Connection Debugger ---")
    
    if not TOKEN:
        print("❌ ERROR: SPARK_API_DEMO_TOKEN not found in .env file.")
        return

    print(f"Attempting to connect to: {API_URL}")
    print(f"Using Params: {PARAMS}")

    try:
        response = requests.get(API_URL, headers=HEADERS, params=PARAMS, timeout=30)
        
        print(f"\n✅ Request completed.")
        print(f"   - HTTP Status Code: {response.status_code}")
        
        print("\n--- API Response Body ---")
        try:
            # Pretty-print the JSON response
            import json
            print(json.dumps(response.json(), indent=2))
        except (requests.exceptions.JSONDecodeError, json.JSONDecodeError):
            print(response.text)
        print("-------------------------\n")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ REQUEST FAILED: {e}")

if __name__ == "__main__":
    run_debug()
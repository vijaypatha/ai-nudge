# File: verify_embedding.py
# --- FINAL VERSION: Added missing User model import to resolve relationship.

import os
import sys
import uuid
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables to get API keys, etc.
dotenv_path = Path(__file__).parent / 'backend' / '.env'
if os.path.exists(dotenv_path):
    print(f"--- Loading environment variables from: {dotenv_path} ---")
    load_dotenv(dotenv_path=dotenv_path)

# Add the 'backend' directory to the Python path
backend_path = Path(__file__).parent / 'backend'
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# --- MODIFIED: Added User import ---
from data.database import engine
from data.models.client import Client
from data.models.user import User # <-- This line is needed to resolve the relationship
from sqlmodel import Session, select, create_engine

# Connect to localhost on the exposed port
LOCAL_DATABASE_URL = "postgresql://postgres:password123@localhost:5432/realestate_db"
engine = create_engine(LOCAL_DATABASE_URL)

CLIENT_ID_TO_CHECK = uuid.UUID("e3f4a5b6-7a8b-9c0d-1e2f-3a4b5c6d7e8f")

print(f"--- Checking for embedding on Client ID: {CLIENT_ID_TO_CHECK} ---")

try:
    with Session(engine) as session:
        client = session.get(Client, CLIENT_ID_TO_CHECK)
        if client:
            print(f"Client Found: {client.full_name}")
            print(f"Notes: {client.notes}")
            if client.notes_embedding and isinstance(client.notes_embedding, list) and len(client.notes_embedding) > 0:
                print(f"✅ SUCCESS: Embedding found!")
                print(f"   - Vector Length: {len(client.notes_embedding)}")
                print(f"   - Embedding Snippet: {client.notes_embedding[:5]}...")
            else:
                print("❌ FAILED: 'notes_embedding' is empty or null.")
        else:
            print(f"Client with ID {CLIENT_ID_TO_CHECK} not found in the database.")
except Exception as e:
    print(f"\n❌ An error occurred: {e}")
# File: backend/verify_embedding.py
# --- UPDATED: To be run as a module from the project root. ---

import os
import sys
import uuid
from dotenv import load_dotenv
from pathlib import Path

# This script is now run as a module, so Python handles the path correctly.
# We only need to load the .env file.
# The path is relative to this file's location (backend/verify_embedding.py)
dotenv_path = Path(__file__).parent / '.env'
if os.path.exists(dotenv_path):
    print(f"--- Loading environment variables from: {dotenv_path} ---")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"--- WARNING: .env file not found at {dotenv_path} ---")

# Imports now work correctly for both the linter and the runtime.
from data.database import engine
from data.models.client import Client
from sqlmodel import Session, select

# Client ID from your test
CLIENT_ID_TO_CHECK = uuid.UUID("e3f4a5b6-7a8b-9c0d-1e2f-3a4b5c6d7e8f")

print(f"--- Checking for embedding on Client ID: {CLIENT_ID_TO_CHECK} ---")

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
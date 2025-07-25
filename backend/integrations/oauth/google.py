# File Path: backend/integrations/oauth/google.py

import os
import logging
from typing import List, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from data.models.client import ClientCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']

class GoogleContacts:
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

        # --- ADDED FOR DEBUGGING ---
        logger.info(f"GoogleContacts Initializing... Client ID: {self.client_id}, Redirect URI: {self.redirect_uri}")
        if self.client_secret:
            logger.info(f"GoogleContacts Client Secret Loaded: Starts with '{self.client_secret[:4]}', Ends with '{self.client_secret[-4:]}'")
        else:
            logger.info("GoogleContacts Client Secret is NOT loaded or is empty.")
        # --- END DEBUGGING BLOCK ---

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Google OAuth credentials are not fully configured in environment variables.")

        self.client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri],
            }
        }

    def get_auth_url(self, state: Optional[str] = None) -> str:
        """Generates the Google OAuth URL, including the state parameter if provided."""
        flow = Flow.from_client_config(
            client_config=self.client_config,
            scopes=SCOPES,
            redirect_uri=self.redirect_uri,
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline', 
            prompt='consent',
            state=state
        )
        
        logger.info("Generated Google Auth URL for user consent.")
        return auth_url

    def exchange_code_for_credentials(self, code: str) -> Credentials:
        """Exchanges an authorization code for a set of credentials."""
        flow = Flow.from_client_config(
            client_config=self.client_config,
            scopes=SCOPES,
            redirect_uri=self.redirect_uri,
        )
        # --- ADDED FOR DEBUGGING ---
        logger.info(f"Attempting to fetch token with config: {self.client_config}")
        # --- END DEBUGGING BLOCK ---
        flow.fetch_token(code=code)
        logger.info("Successfully exchanged authorization code for Google credentials.")
        return flow.credentials

    def fetch_contacts(self, credentials: Credentials) -> List[ClientCreate]:
        """Fetches contacts from the Google People API."""
        logger.info("Attempting to fetch contacts from Google People API...")
        contacts_list = []
        try:
            service = build('people', 'v1', credentials=credentials)
            
            results = service.people().connections().list(
                resourceName='people/me',
                pageSize=1000,
                personFields='names,emailAddresses,phoneNumbers'
            ).execute()
            
            connections = results.get('connections', [])
            logger.info(f"Retrieved {len(connections)} contact entries from Google.")

            for person in connections:
                name_info = person.get('names', [{}])[0]
                full_name = name_info.get('displayName')

                if not full_name:
                    continue

                email = next((e.get('value') for e in person.get('emailAddresses', []) if e.get('value')), None)
                phone = next((p.get('value') for p in person.get('phoneNumbers', []) if p.get('value')), None)

                contacts_list.append(
                    ClientCreate(full_name=full_name, email=email, phone=phone)
                )

            logger.info(f"Successfully processed {len(contacts_list)} valid contacts.")
            return contacts_list

        except HttpError as err:
            logger.error(f"An HTTP error occurred while fetching Google contacts: {err}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return []
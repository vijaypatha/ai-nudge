# FILE: backend/integrations/Google Search.py

import logging
import httpx
from typing import List, Dict, Any

from common.config import get_settings


class GoogleSearchTool:
    """
    A tool to search for reputable content using the Google Programmable Search Engine API.
    This tool is designed to be vertical-agnostic.
    """
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.GOOGLE_API_KEY
        self.search_engine_id = settings.GOOGLE_CSE_ID # You will need to add GOOGLE_CSE_ID to your .env and config.py
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def _is_link_viable(self, url: str) -> bool:
        """
        Performs a quick HEAD request to check if a URL is active and returns a 200 OK status.
        This prevents sending broken links to clients.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.head(url, follow_redirects=True)
                return response.status_code == 200
        except httpx.RequestError as e:
            logging.warning(f"Link viability check failed for {url}: {e}")
            return False

    async def search(self, topic: str, num_results: int = 3) -> List[Dict[str, Any]]:
        """
        Searches for content on a given topic using the pre-configured search engine.

        Args:
            topic: The search query (e.g., "anxiety coping mechanisms").
            num_results: The maximum number of results to return.

        Returns:
            A list of dictionaries, each representing a viable piece of content.
        """
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': topic,
            'num': num_results,
        }
        
        logging.info(f"Google Search Tool: Searching for topic '{topic}'")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
            
            results = response.json().get('items', [])
            
            viable_content = []
            for item in results:
                url = item.get('link')
                if url and await self._is_link_viable(url):
                    viable_content.append({
                        "title": item.get('title'),
                        "url": url,
                        "summary": item.get('snippet'),
                        "source_name": item.get('displayLink'),
                        "topic": topic
                    })
            
            logging.info(f"Google Search Tool: Found {len(viable_content)} viable results for '{topic}'.")
            return viable_content

        except httpx.HTTPStatusError as e:
            logging.error(f"Google Search Tool: HTTP error for '{topic}': {e.response.text}")
            return []
        except Exception as e:
            logging.error(f"Google Search Tool: An unexpected error occurred: {e}", exc_info=True)
            return []
import httpx
import logging
import asyncio

logger = logging.getLogger(__name__)

class OMDBClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://www.omdbapi.com/"

    async def fetch_movie_async(self, imdb_id: str) -> dict:
        params = {"apikey": self.api_key, "i": imdb_id}
        return await self.fetch_with_retries(self.base_url, params)
        
    async def fetch_with_retries(self, url, params, retries=3, backoff_factor=0.3):
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                if attempt < retries - 1:
                    await asyncio.sleep(backoff_factor * (2 ** attempt))
                else:
                    raise e
                
def get_omdb_client(api_key: str = None) -> OMDBClient:
    if not api_key:
        logger.error("OMDB_API_KEY not found in secrets")
        raise ValueError("OMDB_API_KEY is required for OMDB client")
    return OMDBClient(api_key)
"""
Football Data API client.
Handles authentication, caching, and errors.
"""
import time
from dataclasses import dataclass, field
from typing import Optional

import requests
from django.conf import settings


@dataclass
class CacheEntry:
    """Cache entry with TTL."""
    data: dict
    timestamp: float
    ttl: int = 300  # 5 minutes default

    @property
    def is_valid(self) -> bool:
        return time.time() - self.timestamp < self.ttl


class FootballDataClient:
    """Client for football-data.org API."""

    def __init__(self):
        self.base_url = settings.FOOTBALL_DATA_BASE_URL
        self.token = settings.FOOTBALL_DATA_TOKEN
        self.headers = {
            "X-Auth-Token": self.token,
        }
        self._cache: dict[str, CacheEntry] = {}

    def _get_cache_key(self, endpoint: str, params: Optional[dict] = None) -> str:
        """Generate unique cache key."""
        if params:
            params_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            return f"{endpoint}?{params_str}"
        return endpoint

    def _get_from_cache(self, cache_key: str) -> Optional[dict]:
        """Get data from cache if valid."""
        entry = self._cache.get(cache_key)
        if entry and entry.is_valid:
            return entry.data
        return None

    def _set_cache(self, cache_key: str, data: dict, ttl: int = 300):
        """Store data in cache."""
        self._cache[cache_key] = CacheEntry(data=data, timestamp=time.time(), ttl=ttl)

    def _request(self, endpoint: str, params: Optional[dict] = None, ttl: int = 300) -> dict:
        """
        Make API request with caching.

        Args:
            endpoint: API endpoint (e.g., /v4/competitions/WC/matches)
            params: Query parameters
            ttl: Cache TTL in seconds

        Returns:
            API response as dictionary

        Raises:
            requests.exceptions.RequestException: Request error
        """
        cache_key = self._get_cache_key(endpoint, params)

        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self.headers, params=params, timeout=30)

        if response.status_code == 429:
            raise Exception("Rate limit exceeded. Please wait before trying again.")
        elif response.status_code == 403:
            raise Exception("Access denied. Check your API token.")
        elif response.status_code == 404:
            raise Exception(f"Resource not found: {endpoint}")
        elif response.status_code == 400:
            raise Exception(f"Bad request: {response.text}")
        elif response.status_code != 200:
            raise Exception(f"HTTP Error {response.status_code}: {response.text}")

        data = response.json()

        self._set_cache(cache_key, data, ttl)

        return data

    def get_competition(self, code: str = "WC") -> dict:
        """Get competition info."""
        return self._request(f"/v4/competitions/{code}")

    def get_matches(self, code: str = "WC", matchday: Optional[int] = None) -> dict:
        """Get competition matches."""
        params = {}
        if matchday:
            params["matchday"] = matchday
        return self._request(f"/v4/competitions/{code}/matches", params=params)

    def get_match(self, match_id: int) -> dict:
        """Get specific match."""
        return self._request(f"/v4/matches/{match_id}")

    def get_standings(self, code: str = "WC") -> dict:
        """Get competition standings."""
        return self._request(f"/v4/competitions/{code}/standings")

    def get_scorers(self, code: str = "WC") -> dict:
        """Get competition top scorers."""
        return self._request(f"/v4/competitions/{code}/scorers")

    def get_teams(self, code: str = "WC") -> dict:
        """Get competition teams."""
        return self._request(f"/v4/competitions/{code}/teams")

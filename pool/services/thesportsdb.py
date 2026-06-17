"""
TheSportsDB API client for getting scorer data.
Free tier: 30 requests per minute.
"""
import time
from typing import Optional

import requests


# Reverse map: Spanish names -> English names for TheSportsDB
REVERSE_TEAM_MAP = {
    "México": "Mexico",
    "Sudáfrica": "South Africa",
    "Corea del Sur": "South Korea",
    "República Checa": "Czechia",
    "Canadá": "Canada",
    "Bosnia y Herzegovina": "Bosnia-Herzegovina",
    "Catar": "Qatar",
    "Suiza": "Switzerland",
    "Brasil": "Brazil",
    "Marruecos": "Morocco",
    "Haití": "Haiti",
    "Escocia": "Scotland",
    "Estados Unidos": "United States",
    "Alemania": "Germany",
    "Curazao": "Curaçao",
    "Costa de Marfil": "Ivory Coast",
    "Ecuador": "Ecuador",
    "Inglaterra": "England",
    "Japón": "Japan",
    "Nueva Zelanda": "New Zealand",
    "Túnez": "Tunisia",
    "Argentina": "Argentina",
    "Italia": "Italy",
    "Uruguay": "Uruguay",
    "Irán": "Iran",
    "España": "Spain",
    "Arabia Saudita": "Saudi Arabia",
    "Cabo Verde": "Cape Verde Islands",
    "Francia": "France",
    "Colombia": "Colombia",
    "Ghana": "Ghana",
    "Portugal": "Portugal",
    "Nigeria": "Nigeria",
    "Cuba": "Cuba",
    "Irak": "Iraq",
    "Bélgica": "Belgium",
    "Egipto": "Egypt",
    "Panamá": "Panama",
    "Noruega": "Norway",
    "Suecia": "Sweden",
    "Austria": "Austria",
    "Jordania": "Jordan",
    "Argelia": "Algeria",
    "Uzbekistán": "Uzbekistan",
    "RD Congo": "Congo DR",
}


class TheSportsDBClient:
    """Client for TheSportsDB API (free tier)."""

    BASE_URL = "https://www.thesportsdb.com/api/v1/json/123"
    WORLD_CUP_LEAGUE_ID = 4429  # FIFA World Cup

    def __init__(self):
        self._cache = {}
        self._last_request_time = 0

    def _rate_limit(self):
        """Ensure we don't exceed rate limits (30 req/min for free tier)."""
        elapsed = time.time() - self._last_request_time
        if elapsed < 2:  # Wait at least 2 seconds between requests
            time.sleep(2 - elapsed)
        self._last_request_time = time.time()

    def _get(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """Make a GET request to the API."""
        self._rate_limit()

        cache_key = f"{endpoint}:{params}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            self._cache[cache_key] = data
            return data
        except Exception as e:
            print(f"Error fetching {endpoint}: {e}")
            return None

    def search_event(self, event_name: str) -> Optional[dict]:
        """Search for an event by name."""
        return self._get("searchevents.php", {"e": event_name})

    def get_event_timeline(self, event_id: int) -> Optional[dict]:
        """Get the timeline (goals, cards, etc.) for an event."""
        return self._get("lookuptimeline.php", {"id": event_id})

    def get_event(self, event_id: int) -> Optional[dict]:
        """Get event details by ID."""
        return self._get("lookupevent.php", {"id": event_id})

    def search_events_by_date(self, date: str) -> Optional[dict]:
        """Search for events on a specific date."""
        return self._get("eventsday.php", {"d": date})

    def get_events_by_league(self, league_id: int = None) -> Optional[dict]:
        """Get events for a league."""
        if league_id is None:
            league_id = self.WORLD_CUP_LEAGUE_ID
        return self._get("eventspastleague.php", {"id": league_id})

    def find_world_cup_event_id(self, home_team: str, away_team: str, date: str) -> Optional[int]:
        """
        Find the TheSportsDB event ID for a World Cup match.
        
        Args:
            home_team: Home team name (Spanish)
            away_team: Away team name (Spanish)
            date: Match date (YYYY-MM-DD)
        
        Returns:
            Event ID or None if not found
        """
        # Map Spanish names to English for TheSportsDB
        home_en = REVERSE_TEAM_MAP.get(home_team, home_team)
        away_en = REVERSE_TEAM_MAP.get(away_team, away_team)
        
        # Try searching by team names
        search_term = f"{home_en} vs {away_en}"
        result = self.search_event(search_term)
        
        if result and result.get("event"):
            for event in result["event"]:
                # Check if it's a World Cup match
                if (event.get("strLeague") == "FIFA World Cup" and
                    event.get("strSport") == "Soccer" and
                    event.get("dateEvent") == date):
                    return int(event.get("idEvent", 0))
        
        return None

    def get_match_scorers(self, event_id: int) -> list:
        """
        Get scorers for a match from the timeline.
        
        Args:
            event_id: TheSportsDB event ID
        
        Returns:
            List of scorer dicts with 'player' and 'team' keys
        """
        timeline = self.get_event_timeline(event_id)
        if not timeline or not timeline.get("timeline"):
            return []
        
        scorers = []
        for item in timeline["timeline"]:
            # Check for goals (strTimeline == "Goal")
            if item.get("strTimeline") == "Goal":
                scorer_name = item.get("strPlayer", "")
                team_name = item.get("strTeam", "")
                assist_name = item.get("strAssist", "")
                
                if scorer_name:
                    scorers.append({
                        "player": scorer_name,
                        "team": team_name,
                        "minute": item.get("intTime", 0),
                        "assist": assist_name if assist_name else None,
                    })
        
        return scorers

"""
OpenFootball World Cup JSON client.
Fetches match data including scorers from GitHub.
"""
import time
from typing import Optional

import requests


# Map team names: Spanish (database) -> English (openfootball)
TEAM_NAME_MAP = {
    "México": "Mexico",
    "Sudáfrica": "South Africa",
    "Corea del Sur": "South Korea",
    "República Checa": "Czech Republic",
    "Canadá": "Canada",
    "Bosnia y Herzegovina": "Bosnia & Herzegovina",
    "Catar": "Qatar",
    "Suiza": "Switzerland",
    "Brasil": "Brazil",
    "Marruecos": "Morocco",
    "Haití": "Haiti",
    "Escocia": "Scotland",
    "Estados Unidos": "USA",
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
    "Cabo Verde": "Cape Verde",
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
    "RD Congo": "DR Congo",
}

# Reverse map: English -> Spanish
REVERSE_TEAM_MAP = {v: k for k, v in TEAM_NAME_MAP.items()}


class OpenFootballClient:
    """Client for openfootball World Cup JSON data."""

    DATA_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"

    def __init__(self):
        self._cache = None
        self._cache_time = 0
        self._cache_ttl = 3600  # 1 hour

    def _fetch_data(self) -> dict:
        """Fetch World Cup data from GitHub."""
        now = time.time()

        # Use cache if valid
        if self._cache and (now - self._cache_time) < self._cache_ttl:
            return self._cache

        try:
            response = requests.get(self.DATA_URL, timeout=30)
            response.raise_for_status()
            self._cache = response.json()
            self._cache_time = now
            return self._cache
        except Exception as e:
            print(f"Error fetching openfootball data: {e}")
            return self._cache or {"matches": []}

    def get_all_matches(self) -> list:
        """Get all World Cup matches."""
        data = self._fetch_data()
        return data.get("matches", [])

    def find_match(self, home_team: str, away_team: str, date: str) -> Optional[dict]:
        """
        Find a match by teams and date.

        Args:
            home_team: Home team name (Spanish)
            away_team: Away team name (Spanish)
            date: Match date (YYYY-MM-DD)

        Returns:
            Match dict or None
        """
        home_en = TEAM_NAME_MAP.get(home_team, home_team)
        away_en = TEAM_NAME_MAP.get(away_team, away_team)

        matches = self.get_all_matches()

        for match in matches:
            if (match.get("team1") == home_en and
                match.get("team2") == away_en and
                match.get("date") == date):
                return match

        return None

    def get_match_scorers(self, home_team: str, away_team: str, date: str) -> list:
        """
        Get scorers for a match.

        Args:
            home_team: Home team name (Spanish)
            away_team: Away team name (Spanish)
            date: Match date (YYYY-MM-DD)

        Returns:
            List of scorer dicts
        """
        match = self.find_match(home_team, away_team, date)
        if not match:
            return []

        scorers = []

        # Process goals1 (home team goals)
        for goal in match.get("goals1", []):
            player_name = goal.get("name", "")
            if player_name:
                scorers.append({
                    "player": player_name,
                    "team": home_team,
                    "minute": goal.get("minute", "0"),
                    "is_penalty": goal.get("penalty", False),
                    "is_own_goal": goal.get("owngoal", False),
                })

        # Process goals2 (away team goals)
        for goal in match.get("goals2", []):
            player_name = goal.get("name", "")
            if player_name:
                scorers.append({
                    "player": player_name,
                    "team": away_team,
                    "minute": goal.get("minute", "0"),
                    "is_penalty": goal.get("penalty", False),
                    "is_own_goal": goal.get("owngoal", False),
                })

        return scorers

    def get_team_scorers(self, team_name: str) -> dict:
        """
        Get all scorers for a team across all matches.

        Returns:
            Dict with player_name as key and goals count as value
        """
        team_en = TEAM_NAME_MAP.get(team_name, team_name)
        matches = self.get_all_matches()

        scorers = {}

        for match in matches:
            # Check if team is home
            if match.get("team1") == team_en:
                for goal in match.get("goals1", []):
                    player = goal.get("name", "")
                    if player:
                        scorers[player] = scorers.get(player, 0) + 1

            # Check if team is away
            if match.get("team2") == team_en:
                for goal in match.get("goals2", []):
                    player = goal.get("name", "")
                    if player:
                        scorers[player] = scorers.get(player, 0) + 1

        return scorers

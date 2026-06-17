"""
Management command to sync results with football-data.org.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from pool.models import ApiSyncLog, Match, ScorerStat, Team
from pool.services.football_api import FootballDataClient
from pool.services.openfootball import OpenFootballClient


# Map API team names to database names
TEAM_NAME_MAP = {
    "Mexico": "México",
    "South Africa": "Sudáfrica",
    "South Korea": "Corea del Sur",
    "Czechia": "República Checa",
    "Canada": "Canadá",
    "Bosnia-Herzegovina": "Bosnia y Herzegovina",
    "Qatar": "Catar",
    "Switzerland": "Suiza",
    "Brazil": "Brasil",
    "Morocco": "Marruecos",
    "Haiti": "Haití",
    "Scotland": "Escocia",
    "United States": "Estados Unidos",
    "Germany": "Alemania",
    "Curaçao": "Curazao",
    "Ivory Coast": "Costa de Marfil",
    "Ecuador": "Ecuador",
    "England": "Inglaterra",
    "Japan": "Japón",
    "New Zealand": "Nueva Zelanda",
    "Tunisia": "Túnez",
    "Argentina": "Argentina",
    "Italy": "Italia",
    "Uruguay": "Uruguay",
    "Iran": "Irán",
    "Spain": "España",
    "Saudi Arabia": "Arabia Saudita",
    "Cape Verde Islands": "Cabo Verde",
    "Cape Verde": "Cabo Verde",
    "France": "Francia",
    "Colombia": "Colombia",
    "Ghana": "Ghana",
    "Portugal": "Portugal",
    "Nigeria": "Nigeria",
    "Cuba": "Cuba",
    "Iraq": "Irak",
    "Belgium": "Bélgica",
    "Egypt": "Egipto",
    "Panama": "Panamá",
    "Norway": "Noruega",
    "Sweden": "Suecia",
    "Austria": "Austria",
    "Jordan": "Jordania",
    "Algeria": "Argelia",
    "Uzbekistan": "Uzbekistán",
    "Congo DR": "RD Congo",
    "Korea Republic": "Corea del Sur",
    "USA": "Estados Unidos",
    "DR Congo": "RD Congo",
}


class Command(BaseCommand):
    help = "Sync results from football-data.org"

    def handle(self, *args, **options):
        self.stdout.write("Starting sync with football-data.org...")

        client = FootballDataClient()
        openfootball = OpenFootballClient()

        try:
            # Step 1: Sync all matches from competition endpoint
            matches_data = client.get_matches()
            matches_created = self._sync_matches(matches_data)

            # Step 2: Fetch scorers from openfootball JSON
            scorers_updated = self._sync_scorers_openfootball(openfootball)

            log = ApiSyncLog.objects.create(
                endpoint="/v4/competitions/WC/matches",
                status_code=200,
                records_updated=matches_created + scorers_updated,
                response_message=f"Matches created: {matches_created}, Scorers updated: {scorers_updated}",
            )

            self.stdout.write(self.style.SUCCESS(
                f"Sync completed: {matches_created} matches created, "
                f"{scorers_updated} scorers updated"
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Sync error: {e}"))

            ApiSyncLog.objects.create(
                endpoint="/v4/competitions/WC/matches",
                status_code=0,
                response_message=str(e),
            )

    def _sync_matches(self, matches_data: dict) -> int:
        """Sync matches from API."""
        matches = matches_data.get("matches", [])
        created = 0

        for match_data in matches:
            api_id = match_data.get("id")
            if not api_id:
                continue

            home_team_data = match_data.get("homeTeam", {})
            away_team_data = match_data.get("awayTeam", {})

            # Get API team names and map to database names
            home_api_name = home_team_data.get("name", "")
            away_api_name = away_team_data.get("name", "")
            home_db_name = TEAM_NAME_MAP.get(home_api_name, home_api_name)
            away_db_name = TEAM_NAME_MAP.get(away_api_name, away_api_name)

            home_team = Team.objects.filter(name=home_db_name).first()
            away_team = Team.objects.filter(name=away_db_name).first()

            if not home_team or not away_team:
                continue

            # Get score - API uses "home" and "away"
            score = match_data.get("score", {})
            full_time = score.get("fullTime", {})
            home_goals = full_time.get("home")
            away_goals = full_time.get("away")

            status = match_data.get("status", "SCHEDULED")
            stage = match_data.get("stage", "GROUP_STAGE")
            group = match_data.get("group", "")

            # Map API stage names
            stage_map = {
                "LAST_32": "ROUND_OF_16",
                "LAST_16": "ROUND_OF_16",
            }
            stage = stage_map.get(stage, stage)

            match, created_match = Match.objects.update_or_create(
                api_match_id=api_id,
                defaults={
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "status": status,
                    "stage": stage,
                    "group_name": group,
                    "match_date": match_data.get("utcDate"),
                    "last_synced": timezone.now(),
                },
            )

            if created_match:
                created += 1

        return created

    def _sync_scorers_openfootball(self, openfootball: OpenFootballClient) -> int:
        """
        Fetch scorers from openfootball JSON for FINISHED matches.
        """
        # Get all FINISHED matches that haven't had goals synced
        finished_matches = Match.objects.filter(
            status="FINISHED",
            api_match_id__isnull=False,
        ).exclude(
            last_goals_synced__isnull=False,
        )

        self.stdout.write(f"Found {finished_matches.count()} finished matches to sync scorers...")

        scorers_updated = 0

        for match in finished_matches:
            try:
                home_name = match.home_team.name
                away_name = match.away_team.name
                # Get date string without timezone
                match_date = match.match_date.strftime("%Y-%m-%d") if match.match_date else ""

                # Get scorers from openfootball
                scorers = openfootball.get_match_scorers(home_name, away_name, match_date)

                if not scorers:
                    # Try with previous day (timezone difference)
                    if match.match_date:
                        prev_date = (match.match_date - timezone.timedelta(days=1)).strftime("%Y-%m-%d")
                        scorers = openfootball.get_match_scorers(home_name, away_name, prev_date)

                for scorer_data in scorers:
                    player_name = scorer_data.get("player", "")
                    team_name = scorer_data.get("team", "")

                    if not player_name:
                        continue

                    team = Team.objects.filter(name=team_name).first()
                    if not team:
                        continue

                    # Update or create scorer stat
                    stat, created = ScorerStat.objects.get_or_create(
                        player_name=player_name,
                        team=team,
                        defaults={"goals": 1},
                    )
                    if not created:
                        stat.goals += 1
                        stat.save(update_fields=["goals"])

                    scorers_updated += 1

                # Mark as synced
                match.last_goals_synced = timezone.now()
                match.save(update_fields=["last_goals_synced"])

                self.stdout.write(f"  Synced scorers for: {match}")

            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"  Error syncing scorers for {match}: {e}"
                ))

        return scorers_updated

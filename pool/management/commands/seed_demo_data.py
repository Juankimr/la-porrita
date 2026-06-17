"""
Management command to seed demo data for World Cup 2026.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from pool.models import Match, Participant, Prediction, ScoringConfig, Team


# World Cup 2026 teams data (extracted from Excel)
WORLD_CUP_TEAMS = [
    # Group A
    {"name": "México", "abbreviation": "MEX", "group": "A", "group_position": 1, "flag_emoji": "🇲🇽"},
    {"name": "Sudáfrica", "abbreviation": "RSA", "group": "A", "group_position": 2, "flag_emoji": "🇿🇦"},
    {"name": "Corea del Sur", "abbreviation": "KOR", "group": "A", "group_position": 3, "flag_emoji": "🇰🇷"},
    {"name": "República Checa", "abbreviation": "CZE", "group": "A", "group_position": 4, "flag_emoji": "🇨🇿"},
    # Group B
    {"name": "Canadá", "abbreviation": "CAN", "group": "B", "group_position": 1, "flag_emoji": "🇨🇦"},
    {"name": "Bosnia y Herzegovina", "abbreviation": "BIH", "group": "B", "group_position": 2, "flag_emoji": "🇧🇦"},
    {"name": "Catar", "abbreviation": "QAT", "group": "B", "group_position": 3, "flag_emoji": "🇶🇦"},
    {"name": "Suiza", "abbreviation": "SUI", "group": "B", "group_position": 4, "flag_emoji": "🇨🇭"},
    # Group C
    {"name": "Brasil", "abbreviation": "BRA", "group": "C", "group_position": 1, "flag_emoji": "🇧🇷"},
    {"name": "Marruecos", "abbreviation": "MAR", "group": "C", "group_position": 2, "flag_emoji": "🇲🇦"},
    {"name": "Haití", "abbreviation": "HAI", "group": "C", "group_position": 3, "flag_emoji": "🇭🇹"},
    {"name": "Escocia", "abbreviation": "SCO", "group": "C", "group_position": 4, "flag_emoji": "🏴󠁧󠁢󠁳󠁣󠁴󠁿"},
    # Group D
    {"name": "Estados Unidos", "abbreviation": "USA", "group": "D", "group_position": 1, "flag_emoji": "🇺🇸"},
    {"name": "Paraguay", "abbreviation": "PAR", "group": "D", "group_position": 2, "flag_emoji": "🇵🇾"},
    {"name": "Australia", "abbreviation": "AUS", "group": "D", "group_position": 3, "flag_emoji": "🇦🇺"},
    {"name": "Turquía", "abbreviation": "TUR", "group": "D", "group_position": 4, "flag_emoji": "🇹🇷"},
    # Group E
    {"name": "Alemania", "abbreviation": "GER", "group": "E", "group_position": 1, "flag_emoji": "🇩🇪"},
    {"name": "Curazao", "abbreviation": "CUW", "group": "E", "group_position": 2, "flag_emoji": "🇨🇼"},
    {"name": "Costa de Marfil", "abbreviation": "CIV", "group": "E", "group_position": 3, "flag_emoji": "🇨🇮"},
    {"name": "Ecuador", "abbreviation": "ECU", "group": "E", "group_position": 4, "flag_emoji": "🇪🇨"},
    # Group F
    {"name": "Inglaterra", "abbreviation": "ENG", "group": "F", "group_position": 1, "flag_emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    {"name": "Japón", "abbreviation": "JPN", "group": "F", "group_position": 2, "flag_emoji": "🇯🇵"},
    {"name": "Nueva Zelanda", "abbreviation": "NZL", "group": "F", "group_position": 3, "flag_emoji": "🇳🇿"},
    {"name": "Túnez", "abbreviation": "TUN", "group": "F", "group_position": 4, "flag_emoji": "🇹🇳"},
    # Group G
    {"name": "Argentina", "abbreviation": "ARG", "group": "G", "group_position": 1, "flag_emoji": "🇦🇷"},
    {"name": "Italia", "abbreviation": "ITA", "group": "G", "group_position": 2, "flag_emoji": "🇮🇹"},
    {"name": "Uruguay", "abbreviation": "URU", "group": "G", "group_position": 3, "flag_emoji": "🇺🇾"},
    {"name": "Irán", "abbreviation": "IRN", "group": "G", "group_position": 4, "flag_emoji": "🇮🇷"},
    # Group H
    {"name": "España", "abbreviation": "ESP", "group": "H", "group_position": 1, "flag_emoji": "🇪🇸"},
    {"name": "Arabia Saudita", "abbreviation": "KSA", "group": "H", "group_position": 2, "flag_emoji": "🇸🇦"},
    {"name": "Cabo Verde", "abbreviation": "CPV", "group": "H", "group_position": 3, "flag_emoji": "🇨🇻"},
    {"name": "Chile", "abbreviation": "CHI", "group": "H", "group_position": 4, "flag_emoji": "🇨🇱"},
    # Group I
    {"name": "Países Bajos", "abbreviation": "NED", "group": "I", "group_position": 1, "flag_emoji": "🇳🇱"},
    {"name": "Senegal", "abbreviation": "SEN", "group": "I", "group_position": 2, "flag_emoji": "🇸🇳"},
    {"name": "Guatemala", "abbreviation": "GUA", "group": "I", "group_position": 3, "flag_emoji": "🇬🇹"},
    {"name": "Bolivia", "abbreviation": "BOL", "group": "I", "group_position": 4, "flag_emoji": "🇧🇴"},
    # Group J
    {"name": "Francia", "abbreviation": "FRA", "group": "J", "group_position": 1, "flag_emoji": "🇫🇷"},
    {"name": "Colombia", "abbreviation": "COL", "group": "J", "group_position": 2, "flag_emoji": "🇨🇴"},
    {"name": "Ghana", "abbreviation": "GHA", "group": "J", "group_position": 3, "flag_emoji": "🇬🇭"},
    {"name": "Arabia Saudita B", "abbreviation": "KSA2", "group": "J", "group_position": 4, "flag_emoji": "🇸🇦"},
    # Group K
    {"name": "Portugal", "abbreviation": "POR", "group": "K", "group_position": 1, "flag_emoji": "🇵🇹"},
    {"name": "Nigeria", "abbreviation": "NGA", "group": "K", "group_position": 2, "flag_emoji": "🇳🇬"},
    {"name": "Cuba", "abbreviation": "CUB", "group": "K", "group_position": 3, "flag_emoji": "🇨🇺"},
    {"name": "Irak", "abbreviation": "IRQ", "group": "K", "group_position": 4, "flag_emoji": "🇮🇶"},
    # Group L
    {"name": "Bélgica", "abbreviation": "BEL", "group": "L", "group_position": 1, "flag_emoji": "🇧🇪"},
    {"name": "Egipto", "abbreviation": "EGY", "group": "L", "group_position": 2, "flag_emoji": "🇪🇬"},
    {"name": "Panamá", "abbreviation": "PAN", "group": "L", "group_position": 3, "flag_emoji": "🇵🇦"},
    {"name": "Jamaica", "abbreviation": "JAM", "group": "L", "group_position": 4, "flag_emoji": "🇯🇲"},
]


class Command(BaseCommand):
    help = "Create demo data for World Cup 2026"

    def handle(self, *args, **options):
        self.stdout.write("Creating demo data...")

        teams = {}
        for team_data in WORLD_CUP_TEAMS:
            team, created = Team.objects.get_or_create(
                abbreviation=team_data["abbreviation"],
                defaults=team_data,
            )
            teams[team_data["abbreviation"]] = team
            if created:
                self.stdout.write(f"  Team created: {team.name}")

        participants_data = [
            {"name": "Juan"},
            {"name": "María"},
            {"name": "Carlos"},
            {"name": "Ana"},
            {"name": "Pedro"},
        ]

        participants = []
        for p_data in participants_data:
            participant, created = Participant.objects.get_or_create(name=p_data["name"])
            participants.append(participant)
            if created:
                self.stdout.write(f"  Participant created: {participant.name}")

        config, _ = ScoringConfig.objects.get_or_create(is_active=True)
        self.stdout.write("  Scoring config created")

        from datetime import timedelta

        base_date = timezone.now() + timedelta(days=1)
        matches_created = 0

        for group_letter in "ABCDEFGHIJKL":
            group_teams = [t for t in WORLD_CUP_TEAMS if t["group"] == group_letter]
            if len(group_teams) >= 2:
                home = teams[group_teams[0]["abbreviation"]]
                away = teams[group_teams[1]["abbreviation"]]

                match_date = base_date + timedelta(hours=matches_created * 3)
                match, created = Match.objects.get_or_create(
                    home_team=home,
                    away_team=away,
                    match_date=match_date,
                    defaults={
                        "stage": "GROUP_STAGE",
                        "group_name": group_letter,
                        "matchday": 1,
                        "status": "SCHEDULED",
                    },
                )
                if created:
                    matches_created += 1

        self.stdout.write(f"  {matches_created} matches created")

        all_matches = Match.objects.all()
        predictions_created = 0

        for participant in participants:
            for match in all_matches[:6]:
                import random

                pred_home = random.randint(0, 4)
                pred_away = random.randint(0, 4)

                prediction, created = Prediction.objects.get_or_create(
                    participant=participant,
                    match=match,
                    defaults={
                        "pred_home_goals": pred_home,
                        "pred_away_goals": pred_away,
                    },
                )
                if created:
                    predictions_created += 1

        self.stdout.write(f"  {predictions_created} predictions created")

        self.stdout.write(self.style.SUCCESS("Demo data created successfully"))

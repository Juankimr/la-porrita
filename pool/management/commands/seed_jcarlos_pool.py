"""
Management command to seed Jcarlos' pool predictions.
Only creates predictions for matches that exist in the database.
"""
from django.core.management.base import BaseCommand

from pool.models import Match, Participant, Prediction, SpecialPrediction, ScoringConfig, Team


# Jcarlos' predictions: (home_name, away_name, pred_home_goals, pred_away_goals)
# Only include matches that exist in the API
PREDICTIONS = [
    # Group A
    ("México", "Sudáfrica", 2, 0),
    ("Corea del Sur", "República Checa", 2, 1),
    ("República Checa", "Sudáfrica", 1, 1),
    ("México", "Corea del Sur", 1, 1),
    ("República Checa", "México", 2, 2),
    ("Sudáfrica", "Corea del Sur", 1, 1),
    # Group B
    ("Canadá", "Bosnia y Herzegovina", 1, 0),
    ("Catar", "Suiza", 0, 3),
    ("Suiza", "Bosnia y Herzegovina", 2, 1),
    ("Canadá", "Catar", 2, 0),
    ("Suiza", "Canadá", 1, 0),
    ("Bosnia y Herzegovina", "Catar", 3, 0),
    # Group C
    ("Brasil", "Marruecos", 2, 2),
    ("Haití", "Escocia", 0, 3),
    ("Escocia", "Marruecos", 0, 2),
    ("Brasil", "Haití", 3, 0),
    ("Escocia", "Brasil", 1, 3),
    ("Marruecos", "Haití", 4, 0),
    # Group D
    ("Estados Unidos", "Paraguay", 1, 1),
    ("Australia", "Turquía", 1, 3),
    ("Estados Unidos", "Australia", 2, 1),
    ("Turquía", "Paraguay", 2, 0),
    ("Turquía", "Estados Unidos", 2, 1),
    ("Paraguay", "Australia", 1, 0),
    # Group E
    ("Alemania", "Curazao", 5, 0),
    ("Costa de Marfil", "Ecuador", 1, 2),
    ("Alemania", "Costa de Marfil", 3, 1),
    ("Ecuador", "Curazao", 3, 0),
    ("Curazao", "Costa de Marfil", 0, 3),
    ("Ecuador", "Alemania", 0, 2),
    # Group F
    ("Países Bajos", "Japón", 2, 1),
    ("Suecia", "Túnez", 2, 1),
    ("Países Bajos", "Suecia", 3, 1),
    ("Túnez", "Japón", 1, 2),
    ("Japón", "Suecia", 1, 0),
    ("Túnez", "Países Bajos", 0, 2),
    # Group G
    ("Bélgica", "Egipto", 3, 1),
    ("Irán", "Nueva Zelanda", 2, 2),
    ("Bélgica", "Irán", 3, 0),
    ("Nueva Zelanda", "Egipto", 0, 1),
    ("Egipto", "Irán", 2, 1),
    ("Nueva Zelanda", "Bélgica", 1, 2),
    # Group H
    ("España", "Cabo Verde", 4, 0),
    ("Arabia Saudita", "Uruguay", 1, 3),
    ("España", "Arabia Saudita", 3, 0),
    ("Uruguay", "Cabo Verde", 2, 0),
    ("Cabo Verde", "Arabia Saudita", 1, 1),
    ("Uruguay", "España", 1, 2),
    # Group I
    ("Francia", "Senegal", 2, 0),
    ("Irak", "Noruega", 0, 3),
    ("Francia", "Irak", 3, 0),
    ("Noruega", "Senegal", 2, 1),
    ("Noruega", "Francia", 1, 2),
    ("Senegal", "Irak", 1, 0),
    # Group J
    ("Argentina", "Argelia", 2, 0),
    ("Austria", "Jordania", 2, 0),
    ("Argentina", "Austria", 2, 1),
    ("Jordania", "Argelia", 1, 1),
    ("Argelia", "Austria", 0, 0),
    ("Jordania", "Argentina", 0, 4),
    # Group K
    ("Portugal", "RD Congo", 1, 0),
    ("Uzbekistán", "Colombia", 0, 3),
    ("Portugal", "Uzbekistán", 3, 1),
    ("Colombia", "RD Congo", 2, 0),
    ("Colombia", "Portugal", 0, 2),
    ("RD Congo", "Uzbekistán", 3, 1),
    # Group L
    ("Inglaterra", "Croacia", 1, 1),
    ("Ghana", "Panamá", 2, 0),
    ("Inglaterra", "Ghana", 2, 0),
    ("Panamá", "Croacia", 0, 3),
    ("Panamá", "Inglaterra", 0, 2),
    ("Croacia", "Ghana", 2, 1),
    # Round of 16 (only if matches exist)
    ("Corea del Sur", "Canadá", 2, 1),
    ("Marruecos", "Japón", 2, 0),
    ("Alemania", "Paraguay", 3, 1),
    ("Países Bajos", "Brasil", 1, 2),
    ("Ecuador", "Noruega", 2, 1),
    ("Francia", "Suecia", 3, 1),
    ("México", "Escocia", 1, 0),
    ("Croacia", "RD Congo", 2, 1),
    ("Bélgica", "Senegal", 3, 1),
    ("Turquía", "Bosnia y Herzegovina", 2, 0),
    ("España", "Austria", 3, 0),
    ("Colombia", "Inglaterra", 1, 2),
    ("Suiza", "Costa de Marfil", 2, 1),
    ("Estados Unidos", "Egipto", 4, 1),
    ("Argentina", "Uruguay", 4, 2),
    ("Portugal", "Ghana", 2, 0),
    # Quarter finals
    ("Alemania", "Brasil", 5, 2),
    ("España", "Turquía", 2, 0),
    ("Ecuador", "Croacia", 1, 2),
    ("Uruguay", "Portugal", 0, 1),
    # Semi finals
    ("Alemania", "España", 0, 1),
    ("Croacia", "Portugal", 4, 1),
    # Third place
    ("Alemania", "Croacia", 2, 1),
    # Final
    ("España", "Portugal", 4, 0),
]

SPECIAL_PREDICTIONS = [
    ("CHAMPION", "Portugal", None),
    ("RUNNER_UP", "España", None),
    ("THIRD_PLACE", "Alemania", None),
    ("GOLDEN_BOOT", None, "Kai Havertz"),
    ("GOLDEN_BOOT_2", None, "Oyarzabal"),
    ("GOLDEN_BOOT_3", None, "Harry Kane"),
    ("GOLDEN_BALL", None, "Lamine Yamal"),
    ("GOLDEN_BALL_2", None, "Vitinha"),
    ("GOLDEN_BALL_3", None, "Kai Havertz"),
]


class Command(BaseCommand):
    help = "Seed Jcarlos' pool predictions"

    def handle(self, *args, **options):
        self.stdout.write("Creating Jcarlos' pool predictions...")

        # Create or get participant
        participant, created = Participant.objects.get_or_create(
            name="Jcarlos",
            defaults={"email": "jcarlos@porrita.com"},
        )
        if created:
            self.stdout.write(f"  Participant created: {participant.name}")

        # Create scoring config if not exists
        config, _ = ScoringConfig.objects.get_or_create(is_active=True)

        # Create predictions only for matches that exist
        predictions_created = 0
        predictions_skipped = 0

        for home_name, away_name, pred_home, pred_away in PREDICTIONS:
            home_team = Team.objects.filter(name=home_name).first()
            away_team = Team.objects.filter(name=away_name).first()

            if not home_team or not away_team:
                predictions_skipped += 1
                continue

            match = Match.objects.filter(
                home_team=home_team,
                away_team=away_team,
            ).first()

            if not match:
                predictions_skipped += 1
                continue

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
        if predictions_skipped > 0:
            self.stdout.write(f"  {predictions_skipped} predictions skipped (match not found)")

        # Create special predictions
        special_created = 0
        for pred_type, team_name, player_name in SPECIAL_PREDICTIONS:
            team = Team.objects.filter(name=team_name).first() if team_name else None

            special_pred, created = SpecialPrediction.objects.get_or_create(
                participant=participant,
                prediction_type=pred_type,
                defaults={
                    "team": team,
                    "player_name": player_name or "",
                },
            )
            if created:
                special_created += 1

        self.stdout.write(f"  {special_created} special predictions created")
        self.stdout.write(self.style.SUCCESS("Jcarlos' pool created successfully"))

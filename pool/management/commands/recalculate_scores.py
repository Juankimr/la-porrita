"""
Management command to recalculate all scores.
"""
from django.core.management.base import BaseCommand

from pool.services.scoring import recalculate_all_scores


class Command(BaseCommand):
    help = "Recalculate all participant scores"

    def handle(self, *args, **options):
        self.stdout.write("Starting score recalculation...")

        try:
            stats = recalculate_all_scores()

            self.stdout.write(self.style.SUCCESS("Recalculation completed"))
            self.stdout.write(f"  Predictions processed: {stats['predictions_processed']}")
            self.stdout.write(f"  Matches with results: {stats['matches_with_results']}")
            self.stdout.write(f"  Participants affected: {stats['participants_affected']}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Recalculation error: {e}"))

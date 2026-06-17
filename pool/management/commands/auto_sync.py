"""
Management command to automatically sync results and recalculate scores.
Designed to run via cron job (e.g., every hour).
"""
import sys
from io import StringIO

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from pool.models import ApiSyncLog, Match


class Command(BaseCommand):
    help = "Auto-sync football data and recalculate scores (for cron jobs)"

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write(f"[{start_time.isoformat()}] Starting auto-sync...")

        # Check if there are any matches that need syncing
        now = timezone.now()
        pending_matches = Match.objects.filter(
            status__in=["SCHEDULED", "TIMED"],
            match_date__lte=now,
        ).count()

        if pending_matches == 0:
            self.stdout.write("No matches need syncing at this time.")
            return

        self.stdout.write(f"Found {pending_matches} matches that may need updating.")

        # Step 1: Sync football data (includes scorers extraction)
        self.stdout.write("Step 1: Syncing football data...")
        sync_output = StringIO()
        try:
            call_command("sync_football_data", stdout=sync_output)
            sync_result = sync_output.getvalue()
            self.stdout.write(sync_result)
        except Exception as e:
            error_msg = f"Sync error: {e}"
            self.stdout.write(self.style.ERROR(error_msg))
            self._log_sync(start_time, error_msg, success=False)
            return

        # Step 2: Recalculate scores
        self.stdout.write("Step 2: Recalculating scores...")
        recalc_output = StringIO()
        try:
            call_command("recalculate_scores", stdout=recalc_output)
            recalc_result = recalc_output.getvalue()
            self.stdout.write(recalc_result)
        except Exception as e:
            error_msg = f"Recalculate error: {e}"
            self.stdout.write(self.style.ERROR(error_msg))
            self._log_sync(start_time, error_msg, success=False)
            return

        # Log success
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        success_msg = f"Auto-sync completed in {duration:.1f}s"
        self.stdout.write(self.style.SUCCESS(success_msg))
        self._log_sync(start_time, success_msg, success=True)

    def _log_sync(self, start_time, message, success=True):
        """Log the sync result."""
        ApiSyncLog.objects.create(
            endpoint="auto_sync",
            status_code=200 if success else 500,
            response_message=message,
            records_updated=0,
        )

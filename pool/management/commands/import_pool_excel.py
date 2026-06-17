"""
Management command to import World Cup 2026 pool Excel file.
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from pool.services.excel_importer import import_excel


class Command(BaseCommand):
    help = "Import World Cup 2026 pool Excel file"

    def add_arguments(self, parser):
        parser.add_argument("excel_file", type=str, help="Path to Excel file")

    def handle(self, *args, **options):
        excel_file = options["excel_file"]

        if not Path(excel_file).exists():
            raise CommandError(f"File not found: {excel_file}")

        if not excel_file.endswith(".xlsx"):
            raise CommandError("File must be .xlsx format")

        self.stdout.write(f"Importing file: {excel_file}")

        try:
            result, log = import_excel(excel_file)

            self.stdout.write(self.style.SUCCESS("Import completed"))
            self.stdout.write(f"  Teams created: {result.teams_created}")
            self.stdout.write(f"  Participants created: {result.participants_created}")
            self.stdout.write(f"  Matches created: {result.matches_created}")
            self.stdout.write(f"  Predictions created: {result.predictions_created}")

            if result.errors:
                self.stdout.write(self.style.WARNING("Errors found:"))
                for error in result.errors:
                    self.stdout.write(f"  - {error}")

            self.stdout.write(f"\nLog saved with ID: {log.pk}")

        except Exception as e:
            raise CommandError(f"Import error: {e}")

from django.contrib import admin

from .models import (
    ApiSyncLog,
    ImportLog,
    Match,
    Participant,
    Prediction,
    ScorerStat,
    ScoringConfig,
    StandingSnapshot,
    SpecialPrediction,
    Team,
)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "abbreviation", "group", "group_position", "flag_emoji"]
    list_filter = ["group"]
    search_fields = ["name", "abbreviation"]


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "created_at"]
    search_fields = ["name", "email"]


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = [
        "home_team", "away_team", "result_str", "stage",
        "group_name", "matchday", "status", "match_date",
    ]
    list_filter = ["stage", "status", "group_name"]
    search_fields = ["home_team__name", "away_team__name"]
    date_hierarchy = "match_date"


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = [
        "participant", "match", "pred_home_goals", "pred_away_goals",
        "score", "status_badge",
    ]
    list_filter = ["participant", "match__stage"]
    search_fields = ["participant__name"]


@admin.register(SpecialPrediction)
class SpecialPredictionAdmin(admin.ModelAdmin):
    list_display = ["participant", "prediction_type", "team", "player_name", "score"]
    list_filter = ["prediction_type", "participant"]
    search_fields = ["participant__name", "player_name"]


@admin.register(ScoringConfig)
class ScoringConfigAdmin(admin.ModelAdmin):
    list_display = [
        "group_signo_puntos", "group_exacto_puntos",
        "r16_signo_puntos", "final_signo_puntos",
        "special_predictions_enabled", "is_active",
    ]
    list_filter = ["is_active", "special_predictions_enabled"]


@admin.register(StandingSnapshot)
class StandingSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        "participant", "total_points", "group_stage_points",
        "knockout_points", "exact_predictions", "snapshot_date",
    ]
    list_filter = ["participant"]
    date_hierarchy = "snapshot_date"


@admin.register(ScorerStat)
class ScorerStatAdmin(admin.ModelAdmin):
    list_display = ["player_name", "team", "goals", "assists", "is_mvp", "is_golden_boot"]
    list_filter = ["team", "is_mvp", "is_golden_boot"]
    search_fields = ["player_name"]


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ["filename", "rows_imported", "status", "imported_at"]
    list_filter = ["status"]
    date_hierarchy = "imported_at"


@admin.register(ApiSyncLog)
class ApiSyncLogAdmin(admin.ModelAdmin):
    list_display = ["endpoint", "status_code", "records_updated", "synced_at"]
    list_filter = ["status_code"]
    date_hierarchy = "synced_at"

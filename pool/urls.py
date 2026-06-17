from django.urls import path

from . import views

app_name = "pool"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("classification/", views.classification, name="classification"),
    path("matches/", views.matches, name="matches"),
    path("matches/<int:match_id>/", views.match_detail, name="match_detail"),
    path("player/<int:participant_id>/", views.player_detail, name="player_detail"),
    path("stats/", views.stats, name="stats"),
    path("manage/import/", views.import_excel_view, name="import_excel"),
    path("manage/sync/", views.sync_api, name="sync_api"),
    path("manage/recalculate/", views.recalculate, name="recalculate"),
    # HTMX endpoints
    path("htmx/classification/", views.htmx_classification, name="htmx_classification"),
    path("htmx/matches/", views.htmx_matches, name="htmx_matches"),
    path("htmx/matches/<int:match_id>/predictions/", views.htmx_match_predictions, name="htmx_match_predictions"),
]

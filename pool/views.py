import tempfile
from pathlib import Path

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from pool.models import (
    ImportLog,
    Match,
    Participant,
    Prediction,
    ScorerStat,
    StandingSnapshot,
    SpecialPrediction,
)
from pool.services.excel_importer import import_excel
from pool.services.football_api import FootballDataClient
from pool.services.scoring import recalculate_all_scores


def dashboard(request):
    """Main dashboard view."""
    matches_played = Match.objects.filter(status="FINISHED").count()
    participants_count = Participant.objects.count()
    leader = StandingSnapshot.objects.select_related("participant").first()

    recent_matches = Match.objects.filter(status="FINISHED").select_related(
        "home_team", "away_team"
    ).order_by("-match_date")[:5]

    top_classified = StandingSnapshot.objects.select_related("participant").order_by(
        "-total_points"
    )[:5]

    return render(request, "pool/dashboard.html", {
        "matches_played": matches_played,
        "participants_count": participants_count,
        "leader": leader,
        "recent_matches": recent_matches,
        "top_classified": top_classified,
    })


def classification(request):
    """Classification view."""
    phase = request.GET.get("phase", "all")
    standings = StandingSnapshot.objects.select_related("participant").order_by("-total_points")

    if phase == "groups":
        standings = standings.order_by("-group_stage_points")
    elif phase == "knockout":
        standings = standings.order_by("-knockout_points")

    return render(request, "pool/classification.html", {
        "standings": standings,
        "current_phase": phase,
    })


def matches(request):
    """Matches list view."""
    stage = request.GET.get("stage", "all")
    search = request.GET.get("search", "")

    matches_queryset = Match.objects.select_related("home_team", "away_team")

    if stage != "all":
        matches_queryset = matches_queryset.filter(stage=stage)

    if search:
        matches_queryset = matches_queryset.filter(
            home_team__name__icontains=search
        ) | matches_queryset.filter(
            away_team__name__icontains=search
        )

    return render(request, "pool/matches.html", {
        "matches": matches_queryset,
        "current_stage": stage,
        "search": search,
    })


def match_detail(request, match_id):
    """Match detail view."""
    match = get_object_or_404(
        Match.objects.select_related("home_team", "away_team"),
        pk=match_id,
    )
    predictions = Prediction.objects.filter(match=match).select_related("participant")

    return render(request, "pool/match_detail.html", {
        "match": match,
        "predictions": predictions,
    })


def player_detail(request, participant_id):
    """Player detail view."""
    participant = get_object_or_404(Participant, pk=participant_id)
    predictions = Prediction.objects.filter(participant=participant).select_related(
        "match", "match__home_team", "match__away_team"
    )
    special_predictions = SpecialPrediction.objects.filter(participant=participant)
    standing = StandingSnapshot.objects.filter(participant=participant).first()

    return render(request, "pool/player_detail.html", {
        "participant": participant,
        "predictions": predictions,
        "special_predictions": special_predictions,
        "standing": standing,
    })


def stats(request):
    """Statistics view."""
    from pool.models import Participant

    pichichi = ScorerStat.objects.order_by("-goals")[:10]
    mvp = ScorerStat.objects.filter(is_mvp=True)[:5]
    participants = Participant.objects.all().order_by("name")

    # Get selected participant's special predictions
    selected_participant_id = request.GET.get("participant")
    special_predictions = []
    if selected_participant_id:
        special_predictions = SpecialPrediction.objects.filter(
            participant_id=selected_participant_id
        ).select_related("team")

    # Return partial for HTMX requests
    if request.headers.get("HX-Request"):
        return render(request, "pool/partials/special_predictions.html", {
            "special_predictions": special_predictions,
            "selected_participant_id": selected_participant_id,
        })

    return render(request, "pool/stats.html", {
        "pichichi": pichichi,
        "mvp": mvp,
        "participants": participants,
        "selected_participant_id": selected_participant_id,
        "special_predictions": special_predictions,
    })


# === ACTION VIEWS ===


def import_excel_view(request):
    """Excel import view."""
    if request.method == "POST" and request.FILES.get("excel_file"):
        excel_file = request.FILES["excel_file"]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            for chunk in excel_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            result, log = import_excel(tmp_path)

            if request.headers.get("HX-Request"):
                return HttpResponse(f"""
                    <div class="p-4 rounded bg-green-100 text-green-800">
                        <p class="font-semibold">Import completed</p>
                        <ul class="mt-2 text-sm">
                            <li>Teams created: {result.teams_created}</li>
                            <li>Participants created: {result.participants_created}</li>
                            <li>Predictions created: {result.predictions_created}</li>
                        </ul>
                    </div>
                """)

            return render(request, "pool/import_excel.html", {
                "result": result,
                "log": log,
            })

        except Exception as e:
            if request.headers.get("HX-Request"):
                return HttpResponse(f"""
                    <div class="p-4 rounded bg-red-100 text-red-800">
                        <p class="font-semibold">Import error</p>
                        <p class="mt-2 text-sm">{str(e)}</p>
                    </div>
                """)

        finally:
            Path(tmp_path).unlink(missing_ok=True)

    return render(request, "pool/import_excel.html")


def sync_api(request):
    """Sync with football-data.org API (works on GET and POST)."""
    if request.method == "POST" or request.GET.get("action") == "sync":
        try:
            client = FootballDataClient()
            matches_data = client.get_matches()
            matches_updated = _sync_matches(matches_data)

            scorers_data = client.get_scorers()
            scorers_updated = _sync_scorers(scorers_data)

            msg = f"Sync completed: {matches_updated} matches, {scorers_updated} scorers"

            if request.headers.get("HX-Request"):
                return HttpResponse(f"""
                    <div class="p-4 rounded bg-green-100 text-green-800">
                        <p class="font-semibold">{msg}</p>
                    </div>
                """)

            return render(request, "pool/sync_api.html", {"success": msg})

        except Exception as e:
            error_msg = f"Error: {str(e)}"

            if request.headers.get("HX-Request"):
                return HttpResponse(f"""
                    <div class="p-4 rounded bg-red-100 text-red-800">
                        <p class="font-semibold">{error_msg}</p>
                    </div>
                """)

            return render(request, "pool/sync_api.html", {"error": error_msg})

    return render(request, "pool/sync_api.html")


def recalculate(request):
    """Recalculate scores (works on GET and POST)."""
    if request.method == "POST" or request.GET.get("action") == "recalculate":
        try:
            stats = recalculate_all_scores()

            msg = (
                f"Recalculation completed: {stats['predictions_processed']} predictions, "
                f"{stats['matches_with_results']} matches with results"
            )

            if request.headers.get("HX-Request"):
                return HttpResponse(f"""
                    <div class="p-4 rounded bg-green-100 text-green-800">
                        <p class="font-semibold">{msg}</p>
                    </div>
                """)

            return render(request, "pool/recalculate.html", {"success": msg, "stats": stats})

        except Exception as e:
            error_msg = f"Error: {str(e)}"

            if request.headers.get("HX-Request"):
                return HttpResponse(f"""
                    <div class="p-4 rounded bg-red-100 text-red-800">
                        <p class="font-semibold">{error_msg}</p>
                    </div>
                """)

            return render(request, "pool/recalculate.html", {"error": error_msg})

    return render(request, "pool/recalculate.html")


def _sync_matches(matches_data: dict) -> int:
    """Sync matches from API."""
    from django.utils import timezone
    from pool.models import Team

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
        "Paraguay": "Paraguay",
        "Australia": "Australia",
        "Turkey": "Turquía",
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
        "Chile": "Chile",
        "Netherlands": "Países Bajos",
        "Senegal": "Senegal",
        "Guatemala": "Guatemala",
        "Bolivia": "Bolivia",
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
    }

    matches = matches_data.get("matches", [])
    updated = 0

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

        # Get score - API uses "home" and "away", not "homeTeam" and "awayTeam"
        score = match_data.get("score", {})
        full_time = score.get("fullTime", {})
        home_goals = full_time.get("home")
        away_goals = full_time.get("away")

        # Get status and stage
        status = match_data.get("status", "SCHEDULED")
        stage = match_data.get("stage", "GROUP_STAGE")
        group = match_data.get("group", "")

        # Map API stage names to database stage names
        stage_map = {
            "LAST_32": "ROUND_OF_16",
            "LAST_16": "ROUND_OF_16",
        }
        stage = stage_map.get(stage, stage)

        match, created = Match.objects.update_or_create(
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

        if not created and (match.home_goals != home_goals or match.away_goals != away_goals):
            updated += 1

    return updated


def _sync_scorers(scorers_data: dict) -> int:
    """Sync scorers from API."""
    from pool.models import Team

    scorers = scorers_data.get("scorers", [])
    updated = 0

    for scorer_data in scorers:
        player = scorer_data.get("player", {})
        team_data = scorer_data.get("team", {})

        team = Team.objects.filter(name=team_data.get("name")).first()
        if not team:
            continue

        player_name = player.get("name", "")
        goals = scorer_data.get("goals", 0)
        assists = scorer_data.get("assists", 0)

        stat, created = ScorerStat.objects.update_or_create(
            player_name=player_name,
            team=team,
            defaults={"goals": goals, "assists": assists},
        )

        if not created:
            updated += 1

    return updated


# === HTMX ENDPOINTS ===


def htmx_classification(request):
    """HTMX endpoint for classification."""
    phase = request.GET.get("phase", "all")
    standings = StandingSnapshot.objects.select_related("participant")

    if phase == "groups":
        standings = standings.order_by("-group_stage_points")
    elif phase == "knockout":
        standings = standings.order_by("-knockout_points")
    else:
        standings = standings.order_by("-total_points")

    return render(request, "pool/partials/classification_table.html", {
        "standings": standings,
    })


def htmx_matches(request):
    """HTMX endpoint for matches list."""
    stage = request.GET.get("stage", "all")
    search = request.GET.get("search", "")

    matches_queryset = Match.objects.select_related("home_team", "away_team")

    if stage != "all":
        matches_queryset = matches_queryset.filter(stage=stage)

    if search:
        matches_queryset = matches_queryset.filter(
            home_team__name__icontains=search
        ) | matches_queryset.filter(
            away_team__name__icontains=search
        )

    return render(request, "pool/partials/matches_list.html", {
        "matches": matches_queryset,
    })


def htmx_match_predictions(request, match_id):
    """HTMX endpoint for match predictions."""
    match = get_object_or_404(Match, pk=match_id)
    predictions = Prediction.objects.filter(match=match).select_related("participant")

    return render(request, "pool/partials/predictions_list.html", {
        "match": match,
        "predictions": predictions,
    })

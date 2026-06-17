"""
Excel importer service for World Cup 2026 pool.
Parses Excel sheets: WORLDCUP, ADMIN, Teams.
"""
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

from pool.models import (
    ImportLog,
    Match,
    Participant,
    Prediction,
    ScoringConfig,
    Team,
)


@dataclass
class MatchData:
    """Match data extracted from Excel."""
    home_team_name: str
    away_team_name: str
    match_date: Optional[str] = None
    stage: str = "GROUP_STAGE"
    group_name: str = ""
    matchday: Optional[int] = None


@dataclass
class PredictionData:
    """Prediction data extracted from Excel."""
    participant_name: str
    home_team_name: str
    away_team_name: str
    pred_home_goals: int
    pred_away_goals: int


@dataclass
class ImportResult:
    """Import result data."""
    teams_created: int = 0
    participants_created: int = 0
    matches_created: int = 0
    predictions_created: int = 0
    errors: list = field(default_factory=list)


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def parse_teams_sheet(file_path: str) -> list[dict]:
    """
    Parse 'Equipos' sheet from Excel.
    Returns list of team dictionaries.
    """
    df = pd.read_excel(file_path, sheet_name="Equipos", header=None)

    teams = []
    for idx in range(1, len(df)):
        row = df.iloc[idx]
        name = row[1]
        group = row[2]
        position = row[3]

        if pd.notna(name) and pd.notna(group) and pd.notna(position):
            teams.append({
                "name": str(name).strip(),
                "group": str(group).strip(),
                "group_position": int(position),
                "abbreviation": _generate_abbreviation(str(name).strip()),
            })

    return teams


def _generate_abbreviation(name: str) -> str:
    """Generate abbreviation from team name."""
    abbreviations = {
        "México": "MEX", "Sudáfrica": "RSA", "Corea del Sur": "KOR",
        "República Checa": "CZE", "Canadá": "CAN", "Bosnia y Herzegovina": "BIH",
        "Catar": "QAT", "Suiza": "SUI", "Brasil": "BRA", "Marruecos": "MAR",
        "Haití": "HAI", "Escocia": "SCO", "Estados Unidos": "USA",
        "Paraguay": "PAR", "Australia": "AUS", "Turquía": "TUR",
        "Alemania": "GER", "Curazao": "CUW", "Costa de Marfil": "CIV",
        "Ecuador": "ECU", "Inglaterra": "ENG", "Japón": "JPN",
        "Nueva Zelanda": "NZL", "Túnez": "TUN", "Argentina": "ARG",
        "Italia": "ITA", "Uruguay": "URU", "Irán": "IRN", "España": "ESP",
        "Arabia Saudita": "KSA", "Cabo Verde": "CPV", "Chile": "CHI",
        "Países Bajos": "NED", "Senegal": "SEN", "Guatemala": "GUA",
        "Bolivia": "BOL", "Francia": "FRA", "Colombia": "COL", "Ghana": "GHA",
        "Portugal": "POR", "Nigeria": "NGA", "Cuba": "CUB", "Irak": "IRQ",
        "Bélgica": "BEL", "Egipto": "EGY", "Panamá": "PAN", "Jamaica": "JAM",
    }
    return abbreviations.get(name, name[:3].upper())


def parse_wolrd_cup_sheet(file_path: str) -> tuple[list[MatchData], dict[str, list[PredictionData]]]:
    """
    Parse 'WORLDCUP' sheet from Excel.
    Returns tuple of (matches, predictions_by_participant).
    """
    df = pd.read_excel(file_path, sheet_name="WORLDCUP", header=None, nrows=100)

    matches = []
    predictions_by_participant = {}

    participant_row = 2
    participant_start_col = 31

    participants = []
    for col in range(participant_start_col, min(participant_start_col + 20, df.shape[1])):
        name = df.iloc[participant_row, col]
        if pd.notna(name) and isinstance(name, str) and name.strip():
            participants.append((col, name.strip()))

    current_group = None
    for idx in range(3, min(100, len(df))):
        row = df.iloc[idx]

        group_letter = row[1]
        if pd.notna(group_letter) and isinstance(group_letter, str) and len(group_letter) == 1:
            current_group = group_letter

        match_date = row[22]
        home_team = row[25]
        away_team = row[30]

        if pd.notna(home_team) and pd.notna(away_team) and pd.notna(match_date):
            home_name = str(home_team).strip()
            away_name = str(away_team).strip()

            if home_name and away_name and home_name != "Casa" and away_name != "Fuera":
                match = MatchData(
                    home_team_name=home_name,
                    away_team_name=away_name,
                    match_date=str(match_date) if pd.notna(match_date) else None,
                    stage="GROUP_STAGE",
                    group_name=current_group or "",
                )
                matches.append(match)

                for col, participant_name in participants:
                    pred_home = row[col] if col < len(row) else None
                    pred_away = row[col + 1] if col + 1 < len(row) else None

                    if pd.notna(pred_home) and pd.notna(pred_away):
                        try:
                            pred_home_int = int(pred_home)
                            pred_away_int = int(pred_away)

                            if participant_name not in predictions_by_participant:
                                predictions_by_participant[participant_name] = []

                            predictions_by_participant[participant_name].append(
                                PredictionData(
                                    participant_name=participant_name,
                                    home_team_name=home_name,
                                    away_team_name=away_name,
                                    pred_home_goals=pred_home_int,
                                    pred_away_goals=pred_away_int,
                                )
                            )
                        except (ValueError, TypeError):
                            pass

    return matches, predictions_by_participant


def parse_admin_sheet(file_path: str) -> dict:
    """
    Parse 'ADMIN' sheet for scoring configuration.
    Returns configuration dictionary.
    """
    df = pd.read_excel(file_path, sheet_name="ADMIN", header=None, nrows=50)

    config = {
        "signo_puntos": 1,
        "diferencia_puntos": 2,
        "exacto_puntos": 5,
        "posicion_grupo_puntos": 3,
        "equipo_ronda_puntos": 2,
        "campeon_puntos": 10,
        "subcampeon_puntos": 5,
        "tercer_puesto_puntos": 3,
        "pichichi_puntos": 7,
        "mvp_puntos": 5,
    }

    for idx in range(5, min(20, len(df))):
        row = df.iloc[idx]
        description = str(row[2]) if pd.notna(row[2]) else ""
        points = row[3] if pd.notna(row[3]) else None

        if points is not None:
            try:
                points_int = int(points)
                if "Signo" in description or "1X2" in description:
                    config["signo_puntos"] = points_int
                elif "Diferencia" in description:
                    config["diferencia_puntos"] = points_int
                elif "Exacto" in description:
                    config["exacto_puntos"] = points_int
                elif "Posición" in description and "1º" in description:
                    config["posicion_grupo_puntos"] = points_int
            except (ValueError, TypeError):
                pass

    return config


def import_excel(file_path: str) -> tuple[ImportResult, ImportLog]:
    """
    Import World Cup 2026 pool Excel file.
    Returns tuple of (result, log).
    """
    result = ImportResult()
    log = ImportLog(filename=Path(file_path).name)

    try:
        log.file_hash = calculate_file_hash(file_path)

        existing_log = ImportLog.objects.filter(file_hash=log.file_hash).first()
        if existing_log:
            result.errors.append(f"File already imported on {existing_log.imported_at}")
            log.status = "PARTIAL"
            log.error_message = "File already imported"
            log.save()
            return result, log

        teams_data = parse_teams_sheet(file_path)
        teams = {}
        for team_data in teams_data:
            team, created = Team.objects.get_or_create(
                abbreviation=team_data["abbreviation"],
                defaults=team_data,
            )
            teams[team_data["name"]] = team
            if created:
                result.teams_created += 1

        config_data = parse_admin_sheet(file_path)
        scoring_config, _ = ScoringConfig.objects.get_or_create(
            is_active=True,
            defaults=config_data,
        )

        matches_data, predictions_data = parse_wolrd_cup_sheet(file_path)

        for participant_name, predictions in predictions_data.items():
            participant, created = Participant.objects.get_or_create(name=participant_name)
            if created:
                result.participants_created += 1

            for pred_data in predictions:
                home_team = teams.get(pred_data.home_team_name)
                away_team = teams.get(pred_data.away_team_name)

                if home_team and away_team:
                    match = Match.objects.filter(
                        home_team=home_team,
                        away_team=away_team,
                    ).first()

                    if match:
                        prediction, created = Prediction.objects.get_or_create(
                            participant=participant,
                            match=match,
                            defaults={
                                "pred_home_goals": pred_data.pred_home_goals,
                                "pred_away_goals": pred_data.pred_away_goals,
                            },
                        )
                        if created:
                            result.predictions_created += 1

        log.status = "SUCCESS"
        log.rows_imported = result.predictions_created
        log.save()

    except Exception as e:
        result.errors.append(str(e))
        log.status = "ERROR"
        log.error_message = str(e)
        log.save()

    return result, log

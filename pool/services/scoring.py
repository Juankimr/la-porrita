"""
Scoring logic service for World Cup 2026 pool.

Scoring Rules:
- Group Stage: Sign 2pts, Difference 1pt, Exact 2pts, Position 1pt, Qualifies R16 +2pts
- Round of 16: Sign 3pts, Exact 5pts
- Quarter Finals: Sign 5pts, Exact 9pts
- Semi Finals: Sign 10pts, Exact 15pts
- Third Place: Sign 15pts, Exact 30pts
- Final: Sign 25pts, Exact 40pts
- Team qualifies: R16 5pts, QF 10pts, SF 15pts, Third Place 15pts, Final 20pts
- Special: Champion 50pts, Runner Up 25pts, Third 15pts, Golden Boot 20pts, Golden Ball 20pts
"""
from decimal import Decimal
from typing import Optional

from pool.models import (
    Match,
    Prediction,
    ScoringConfig,
    SpecialPrediction,
    StandingSnapshot,
)


def calculate_prediction_score(
    prediction: Prediction,
    config: Optional[ScoringConfig] = None,
) -> tuple[Decimal, dict]:
    """
    Calculate prediction score for a match.

    Args:
        prediction: Participant prediction
        config: Scoring config (optional, uses active if not provided)

    Returns:
        Tuple of (total_score, breakdown)
    """
    if config is None:
        config = ScoringConfig.get_active()

    match = prediction.match

    if match.status != "FINISHED":
        return Decimal("0"), {}

    if match.home_goals is None or match.away_goals is None:
        return Decimal("0"), {}

    total_score = Decimal("0")
    breakdown = {}

    # Get sign points and exact points based on stage
    stage = match.stage
    if stage == "GROUP_STAGE":
        sign_pts = config.group_signo_puntos
        exact_pts = config.group_exacto_puntos
        diff_pts = config.group_diferencia_puntos
    elif stage == "ROUND_OF_16":
        sign_pts = config.r16_signo_puntos
        exact_pts = config.r16_exacto_puntos
        diff_pts = 0  # No difference points in knockout
    elif stage == "QUARTER_FINALS":
        sign_pts = config.qf_signo_puntos
        exact_pts = config.qf_exacto_puntos
        diff_pts = 0
    elif stage == "SEMI_FINALS":
        sign_pts = config.sf_signo_puntos
        exact_pts = config.sf_exacto_puntos
        diff_pts = 0
    elif stage == "THIRD_PLACE":
        sign_pts = config.tp_signo_puntos
        exact_pts = config.tp_exacto_puntos
        diff_pts = 0
    elif stage == "FINAL":
        sign_pts = config.final_signo_puntos
        exact_pts = config.final_exacto_puntos
        diff_pts = 0
    else:
        sign_pts = 0
        exact_pts = 0
        diff_pts = 0

    # 1. Calculate sign 1X2
    predicted_sign = prediction.predicted_sign
    actual_sign = match.winner_sign

    if predicted_sign == actual_sign:
        sign_score = Decimal(str(sign_pts))
        total_score += sign_score

        # 2. Calculate goal difference (only in group stage with correct sign)
        if stage == "GROUP_STAGE" and diff_pts > 0:
            predicted_diff = prediction.pred_home_goals - prediction.pred_away_goals
            actual_diff = match.home_goals - match.away_goals

            if predicted_diff == actual_diff:
                diff_score = Decimal(str(diff_pts))
                total_score += diff_score
                breakdown["sign"] = float(sign_score)
                breakdown["difference"] = float(diff_score)
            else:
                breakdown["sign"] = float(sign_score)
        else:
            breakdown["sign"] = float(sign_score)

        # 3. Calculate exact score (only if sign correct)
        if (
            prediction.pred_home_goals == match.home_goals
            and prediction.pred_away_goals == match.away_goals
        ):
            exact_score = Decimal(str(exact_pts))
            total_score += exact_score
            breakdown["exact"] = float(exact_score)

    return total_score, breakdown


def calculate_special_prediction_score(
    prediction: SpecialPrediction,
    config: Optional[ScoringConfig] = None,
) -> Decimal:
    """
    Calculate special prediction score.

    Args:
        prediction: Participant special prediction
        config: Scoring config

    Returns:
        Points earned
    """
    if config is None:
        config = ScoringConfig.get_active()

    # Special predictions only score when enabled in config
    if not config.special_predictions_enabled:
        return Decimal("0")

    # Map prediction type to config field
    score_map = {
        "CHAMPION": config.campeon_puntos,
        "RUNNER_UP": config.subcampeon_puntos,
        "THIRD_PLACE": config.tercer_puesto_puntos,
        "GOLDEN_BOOT": config.bota_oro_puntos,
        "GOLDEN_BOOT_2": config.bota_plata_puntos,
        "GOLDEN_BOOT_3": config.bota_bronce_puntos,
        "GOLDEN_BALL": config.balon_oro_puntos,
        "GOLDEN_BALL_2": config.balon_plata_puntos,
        "GOLDEN_BALL_3": config.balon_bronce_puntos,
    }

    return Decimal(str(score_map.get(prediction.prediction_type, 0)))


def recalculate_all_scores() -> dict:
    """
    Recalculate all participant scores.

    Returns:
        Dictionary with recalculation stats
    """
    config = ScoringConfig.get_active()

    predictions = Prediction.objects.select_related("match", "participant").all()

    stats = {
        "predictions_processed": 0,
        "matches_with_results": 0,
        "participants_affected": set(),
    }

    for prediction in predictions:
        score, breakdown = calculate_prediction_score(prediction, config)

        if prediction.score != score:
            prediction.score = score
            prediction.score_breakdown = breakdown
            prediction.save(update_fields=["score", "score_breakdown"])

        stats["predictions_processed"] += 1
        if prediction.match.status == "FINISHED":
            stats["matches_with_results"] += 1
        stats["participants_affected"].add(prediction.participant_id)

    special_predictions = SpecialPrediction.objects.select_related("participant").all()
    for special_pred in special_predictions:
        score = calculate_special_prediction_score(special_pred, config)
        if special_pred.score != score:
            special_pred.score = score
            special_pred.save(update_fields=["score"])

    _update_standings(config)

    return {
        "predictions_processed": stats["predictions_processed"],
        "matches_with_results": stats["matches_with_results"],
        "participants_affected": len(stats["participants_affected"]),
    }


def _update_standings(config: ScoringConfig):
    """Update all participant standings."""
    from pool.models import Participant

    for participant in Participant.objects.all():
        group_predictions = participant.predictions.filter(match__stage="GROUP_STAGE")
        knockout_predictions = participant.predictions.exclude(match__stage="GROUP_STAGE")

        group_points = sum(p.score for p in group_predictions)
        knockout_points = sum(p.score for p in knockout_predictions)

        special_points = sum(sp.score for sp in participant.special_predictions.all())

        all_predictions = participant.predictions.all()
        exact_predictions = sum(1 for p in all_predictions if p.status_badge == "exact")
        sign_predictions = sum(1 for p in all_predictions if p.status_badge in ("exact", "partial"))

        total_points = group_points + knockout_points + special_points

        StandingSnapshot.objects.update_or_create(
            participant=participant,
            defaults={
                "total_points": total_points,
                "group_stage_points": group_points,
                "knockout_points": knockout_points,
                "special_points": special_points,
                "exact_predictions": exact_predictions,
                "sign_predictions": sign_predictions,
                "total_predictions": all_predictions.count(),
            },
        )

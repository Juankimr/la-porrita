from django.db import models


class Team(models.Model):
    """Team model for World Cup 2026 participants."""

    name = models.CharField(max_length=100, verbose_name="Name")
    abbreviation = models.CharField(max_length=10, verbose_name="Abbreviation")
    group = models.CharField(max_length=2, verbose_name="Group")
    group_position = models.PositiveIntegerField(verbose_name="Group Position")
    flag_emoji = models.CharField(max_length=10, blank=True, verbose_name="Flag Emoji")
    fifa_code = models.CharField(max_length=10, blank=True, verbose_name="FIFA Code")

    class Meta:
        ordering = ["group", "group_position"]
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    def __str__(self):
        return f"{self.name} ({self.group})"


class Participant(models.Model):
    """Participant model for pool players."""

    name = models.CharField(max_length=100, verbose_name="Name")
    email = models.EmailField(blank=True, verbose_name="Email")
    avatar_url = models.URLField(blank=True, verbose_name="Avatar URL")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Participant"
        verbose_name_plural = "Participants"

    def __str__(self):
        return self.name


class Match(models.Model):
    """Match model for World Cup 2026 games."""

    STAGE_CHOICES = [
        ("GROUP_STAGE", "Group Stage"),
        ("ROUND_OF_16", "Round of 16"),
        ("QUARTER_FINALS", "Quarter Finals"),
        ("SEMI_FINALS", "Semi Finals"),
        ("THIRD_PLACE", "Third Place"),
        ("FINAL", "Final"),
    ]

    STATUS_CHOICES = [
        ("SCHEDULED", "Scheduled"),
        ("TIMED", "Timed"),
        ("IN_PLAY", "In Play"),
        ("PAUSED", "Half Time"),
        ("FINISHED", "Finished"),
        ("POSTPONED", "Postponed"),
        ("CANCELLED", "Cancelled"),
    ]

    home_team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="home_matches", verbose_name="Home Team"
    )
    away_team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="away_matches", verbose_name="Away Team"
    )
    home_goals = models.PositiveIntegerField(null=True, blank=True, verbose_name="Home Goals")
    away_goals = models.PositiveIntegerField(null=True, blank=True, verbose_name="Away Goals")

    match_date = models.DateTimeField(verbose_name="Match Date")
    stage = models.CharField(
        max_length=20, choices=STAGE_CHOICES, default="GROUP_STAGE", verbose_name="Stage"
    )
    group_name = models.CharField(max_length=5, blank=True, verbose_name="Group")
    matchday = models.PositiveIntegerField(null=True, blank=True, verbose_name="Matchday")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="SCHEDULED", verbose_name="Status"
    )

    # API fields
    api_match_id = models.PositiveIntegerField(unique=True, null=True, blank=True, verbose_name="API ID")
    thesportsdb_event_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="TheSportsDB Event ID")
    last_synced = models.DateTimeField(null=True, blank=True, verbose_name="Last Synced")
    last_goals_synced = models.DateTimeField(null=True, blank=True, verbose_name="Last Goals Synced")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["match_date"]
        verbose_name = "Match"
        verbose_name_plural = "Matches"

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"

    @property
    def winner(self):
        """Returns the match winner or None if draw."""
        if self.home_goals is None or self.away_goals is None:
            return None
        if self.home_goals > self.away_goals:
            return self.home_team
        elif self.away_goals > self.home_goals:
            return self.away_team
        return None

    @property
    def winner_sign(self):
        """Returns match sign: H (home), D (draw), A (away)."""
        if self.home_goals is None or self.away_goals is None:
            return ""
        if self.home_goals > self.away_goals:
            return "H"
        elif self.home_goals < self.away_goals:
            return "A"
        return "D"

    @property
    def result_str(self):
        """Returns result as string."""
        if self.home_goals is None or self.away_goals is None:
            return "-"
        return f"{self.home_goals}-{self.away_goals}"

    @property
    def stage_display(self):
        """Returns readable stage name."""
        return dict(self.STAGE_CHOICES).get(self.stage, self.stage)


class Prediction(models.Model):
    """Prediction model for participant match predictions."""

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="predictions", verbose_name="Participant"
    )
    match = models.ForeignKey(
        Match, on_delete=models.CASCADE, related_name="predictions", verbose_name="Match"
    )

    pred_home_goals = models.PositiveIntegerField(verbose_name="Pred. Home Goals")
    pred_away_goals = models.PositiveIntegerField(verbose_name="Pred. Away Goals")

    # Calculated score for this prediction
    score = models.DecimalField(
        max_digits=6, decimal_places=2, default=0, verbose_name="Score"
    )
    score_breakdown = models.JSONField(default=dict, verbose_name="Score Breakdown")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["participant", "match"]
        ordering = ["match__match_date"]
        verbose_name = "Prediction"
        verbose_name_plural = "Predictions"

    def __str__(self):
        return f"{self.participant}: {self.pred_home_goals}-{self.pred_away_goals} ({self.match})"

    @property
    def predicted_winner(self):
        """Returns predicted winner or None if draw."""
        if self.pred_home_goals > self.pred_away_goals:
            return self.match.home_team
        elif self.pred_away_goals > self.pred_home_goals:
            return self.match.away_team
        return None

    @property
    def predicted_sign(self):
        """Returns predicted sign: H (home), D (draw), A (away)."""
        if self.pred_home_goals > self.pred_away_goals:
            return "H"
        elif self.pred_home_goals < self.pred_away_goals:
            return "A"
        return "D"

    @property
    def status_badge(self):
        """Returns prediction status badge."""
        if self.match.status != "FINISHED":
            return "pending"
        if self.pred_home_goals == self.match.home_goals and self.pred_away_goals == self.match.away_goals:
            return "exact"
        if self.predicted_sign == self.match.winner_sign:
            return "partial"
        return "missed"


class SpecialPrediction(models.Model):
    """Special prediction model for champion, pichichi, MVP."""

    PREDICTION_TYPE_CHOICES = [
        ("CHAMPION", "Campeón"),
        ("RUNNER_UP", "Subcampeón"),
        ("THIRD_PLACE", "Tercer Puesto"),
        ("GOLDEN_BOOT", "Bota de Oro"),
        ("GOLDEN_BOOT_2", "Bota de Plata"),
        ("GOLDEN_BOOT_3", "Bota de Bronce"),
        ("GOLDEN_BALL", "Balón de Oro"),
        ("GOLDEN_BALL_2", "Balón de Plata"),
        ("GOLDEN_BALL_3", "Balón de Bronce"),
    ]

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="special_predictions", verbose_name="Participant"
    )
    prediction_type = models.CharField(
        max_length=20, choices=PREDICTION_TYPE_CHOICES, verbose_name="Type"
    )
    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="special_predictions",
        verbose_name="Team"
    )
    player_name = models.CharField(max_length=100, blank=True, verbose_name="Player Name")

    score = models.DecimalField(
        max_digits=6, decimal_places=2, default=0, verbose_name="Score"
    )

    class Meta:
        unique_together = ["participant", "prediction_type"]
        verbose_name = "Special Prediction"
        verbose_name_plural = "Special Predictions"

    def __str__(self):
        return f"{self.participant}: {self.get_prediction_type_display()}"


class ScoringConfig(models.Model):
    """Scoring configuration model."""

    # Group Stage
    group_signo_puntos = models.PositiveIntegerField(default=2, verbose_name="Group Sign 1X2 Points")
    group_diferencia_puntos = models.PositiveIntegerField(default=1, verbose_name="Group Goal Difference Points")
    group_exacto_puntos = models.PositiveIntegerField(default=2, verbose_name="Group Exact Score Points")
    group_posicion_puntos = models.PositiveIntegerField(default=1, verbose_name="Group Position Points")
    group_clasificado_puntos = models.PositiveIntegerField(default=2, verbose_name="Group Qualifies for R16 Points")

    # Round of 16
    r16_signo_puntos = models.PositiveIntegerField(default=3, verbose_name="R16 Sign Points")
    r16_exacto_puntos = models.PositiveIntegerField(default=5, verbose_name="R16 Exact Score Points")

    # Quarter Finals
    qf_signo_puntos = models.PositiveIntegerField(default=5, verbose_name="QF Sign Points")
    qf_exacto_puntos = models.PositiveIntegerField(default=9, verbose_name="QF Exact Score Points")

    # Semi Finals
    sf_signo_puntos = models.PositiveIntegerField(default=10, verbose_name="SF Sign Points")
    sf_exacto_puntos = models.PositiveIntegerField(default=15, verbose_name="SF Exact Score Points")

    # Third Place
    tp_signo_puntos = models.PositiveIntegerField(default=15, verbose_name="Third Place Sign Points")
    tp_exacto_puntos = models.PositiveIntegerField(default=30, verbose_name="Third Place Exact Score Points")

    # Final
    final_signo_puntos = models.PositiveIntegerField(default=25, verbose_name="Final Sign Points")
    final_exacto_puntos = models.PositiveIntegerField(default=40, verbose_name="Final Exact Score Points")

    # Team qualifies bonus
    clasificado_r16_puntos = models.PositiveIntegerField(default=5, verbose_name="Qualifies R16 Points")
    clasificado_qf_puntos = models.PositiveIntegerField(default=10, verbose_name="Qualifies QF Points")
    clasificado_sf_puntos = models.PositiveIntegerField(default=15, verbose_name="Qualifies SF Points")
    clasificado_tp_puntos = models.PositiveIntegerField(default=15, verbose_name="Qualifies Third Place Points")
    clasificado_final_puntos = models.PositiveIntegerField(default=20, verbose_name="Qualifies Final Points")

    # Special predictions
    campeon_puntos = models.PositiveIntegerField(default=50, verbose_name="Champion Points")
    subcampeon_puntos = models.PositiveIntegerField(default=25, verbose_name="Runner Up Points")
    tercer_puesto_puntos = models.PositiveIntegerField(default=15, verbose_name="Third Place Points")
    bota_oro_puntos = models.PositiveIntegerField(default=20, verbose_name="Golden Boot Points")
    bota_plata_puntos = models.PositiveIntegerField(default=10, verbose_name="Silver Boot Points")
    bota_bronce_puntos = models.PositiveIntegerField(default=5, verbose_name="Bronze Boot Points")
    balon_oro_puntos = models.PositiveIntegerField(default=20, verbose_name="Golden Ball Points")
    balon_plata_puntos = models.PositiveIntegerField(default=10, verbose_name="Silver Ball Points")
    balon_bronce_puntos = models.PositiveIntegerField(default=5, verbose_name="Bronze Ball Points")

    # Toggle for special predictions scoring
    special_predictions_enabled = models.BooleanField(default=False, verbose_name="Special Predictions Enabled")

    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Scoring Config"
        verbose_name_plural = "Scoring Configs"

    def __str__(self):
        return f"Config {self.pk} (Active: {self.is_active})"

    @classmethod
    def get_active(cls):
        """Returns active config or creates default."""
        config = cls.objects.filter(is_active=True).first()
        if not config:
            config = cls.objects.create()
        return config


class StandingSnapshot(models.Model):
    """Standing snapshot model for rankings."""

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="standings", verbose_name="Participant"
    )

    total_points = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="Total Points")
    group_stage_points = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="Group Stage Points")
    knockout_points = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="Knockout Points")
    special_points = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="Special Points")

    exact_predictions = models.PositiveIntegerField(default=0, verbose_name="Exact Predictions")
    sign_predictions = models.PositiveIntegerField(default=0, verbose_name="Sign Predictions")
    total_predictions = models.PositiveIntegerField(default=0, verbose_name="Total Predictions")

    snapshot_date = models.DateTimeField(auto_now_add=True, verbose_name="Snapshot Date")

    class Meta:
        ordering = ["-total_points", "-exact_predictions"]
        verbose_name = "Standing"
        verbose_name_plural = "Standings"

    def __str__(self):
        return f"{self.participant}: {self.total_points} pts"


class ScorerStat(models.Model):
    """Scorer statistics model for top scorers and MVP."""

    player_name = models.CharField(max_length=100, verbose_name="Player Name")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name="Team")
    goals = models.PositiveIntegerField(default=0, verbose_name="Goals")
    assists = models.PositiveIntegerField(default=0, null=True, blank=True, verbose_name="Assists")
    is_mvp = models.BooleanField(default=False, verbose_name="Is MVP")
    is_golden_boot = models.BooleanField(default=False, verbose_name="Is Golden Boot")
    is_golden_ball = models.BooleanField(default=False, verbose_name="Is Golden Ball")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-goals", "-assists"]
        verbose_name = "Scorer Stat"
        verbose_name_plural = "Scorer Stats"

    def __str__(self):
        return f"{self.player_name} ({self.team})"


class ImportLog(models.Model):
    """Import log model for Excel imports."""

    filename = models.CharField(max_length=255, verbose_name="Filename")
    file_hash = models.CharField(max_length=64, blank=True, verbose_name="File Hash")
    rows_imported = models.PositiveIntegerField(default=0, verbose_name="Rows Imported")
    status = models.CharField(
        max_length=20,
        choices=[("SUCCESS", "Success"), ("PARTIAL", "Partial"), ("ERROR", "Error")],
        verbose_name="Status",
    )
    error_message = models.TextField(blank=True, verbose_name="Error Message")
    imported_at = models.DateTimeField(auto_now_add=True, verbose_name="Imported At")

    class Meta:
        ordering = ["-imported_at"]
        verbose_name = "Import Log"
        verbose_name_plural = "Import Logs"

    def __str__(self):
        return f"{self.filename} - {self.status}"


class ApiSyncLog(models.Model):
    """API sync log model for tracking synchronizations."""

    endpoint = models.CharField(max_length=255, verbose_name="Endpoint")
    status_code = models.PositiveIntegerField(verbose_name="Status Code")
    response_message = models.TextField(blank=True, verbose_name="Response Message")
    records_updated = models.PositiveIntegerField(default=0, verbose_name="Records Updated")
    synced_at = models.DateTimeField(auto_now_add=True, verbose_name="Synced At")

    class Meta:
        ordering = ["-synced_at"]
        verbose_name = "API Sync Log"
        verbose_name_plural = "API Sync Logs"

    def __str__(self):
        return f"{self.endpoint} - {self.status_code}"

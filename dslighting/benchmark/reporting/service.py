from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from dslighting.benchmark.evaluation.models import EvaluationSemantics
from dslighting.benchmark.evaluation.outcome import EvaluationOutcome
from dslighting.benchmark.reporting.models import CompetitionReport


@dataclass(frozen=True)
class _Thresholds:
    gold: float
    silver: float
    bronze: float
    median: float


class CompetitionReportBuilder:
    @staticmethod
    def _thresholds_from_leaderboard(leaderboard_path: Path | None) -> _Thresholds | None:
        if leaderboard_path is None or not leaderboard_path.exists():
            return None
        try:
            leaderboard = pd.read_csv(leaderboard_path)
        except pd.errors.EmptyDataError:
            return None
        if "score" not in leaderboard.columns or leaderboard.empty:
            return None
        scores = leaderboard["score"]
        num_teams = len(scores)

        def score_at(position: int) -> float:
            position = max(1, position)
            return float(scores.iloc[position - 1])

        if 1 <= num_teams < 100:
            gold = score_at(int(num_teams * 0.1) or 1)
            silver = score_at(int(num_teams * 0.2) or 1)
            bronze = score_at(int(num_teams * 0.4) or 1)
        elif 100 <= num_teams < 250:
            gold = score_at(10)
            silver = score_at(int(num_teams * 0.2) or 1)
            bronze = score_at(int(num_teams * 0.4) or 1)
        elif 250 <= num_teams < 1000:
            gold = score_at(10 + int(num_teams * 0.002))
            silver = score_at(50)
            bronze = score_at(100)
        else:
            gold = score_at(10 + int(num_teams * 0.002))
            silver = score_at(int(num_teams * 0.05) or 1)
            bronze = score_at(int(num_teams * 0.1) or 1)

        return _Thresholds(gold=gold, silver=silver, bronze=bronze, median=float(scores.median()))

    def build(
        self,
        *,
        outcome: EvaluationOutcome,
        semantics: EvaluationSemantics,
        competition_id: str,
        submission_path: Path,
    ) -> CompetitionReport:
        thresholds = self._thresholds_from_leaderboard(semantics.leaderboard_path)
        is_lower_better = semantics.objective == "lower_is_better"

        gold = silver = bronze = above_median = False
        any_medal = False
        gold_threshold = silver_threshold = bronze_threshold = median_threshold = float("nan")

        if thresholds is not None:
            gold_threshold = thresholds.gold
            silver_threshold = thresholds.silver
            bronze_threshold = thresholds.bronze
            median_threshold = thresholds.median
            if outcome.score is not None:
                score = float(outcome.score)
                if is_lower_better:
                    gold = score <= thresholds.gold
                    silver = not gold and score <= thresholds.silver
                    bronze = not gold and not silver and score <= thresholds.bronze
                    above_median = score < thresholds.median
                else:
                    gold = score >= thresholds.gold
                    silver = not gold and score >= thresholds.silver
                    bronze = not gold and not silver and score >= thresholds.bronze
                    above_median = score > thresholds.median
                any_medal = gold or silver or bronze

        return CompetitionReport(
            competition_id=competition_id,
            score=outcome.score,
            gold_threshold=gold_threshold,
            silver_threshold=silver_threshold,
            bronze_threshold=bronze_threshold,
            median_threshold=median_threshold,
            any_medal=any_medal,
            gold_medal=gold,
            silver_medal=silver,
            bronze_medal=bronze,
            above_median=above_median,
            submission_exists=outcome.submission_exists,
            valid_submission=outcome.valid_submission,
            is_lower_better=is_lower_better,
            created_at=datetime.now(),
            submission_path=str(submission_path),
        )

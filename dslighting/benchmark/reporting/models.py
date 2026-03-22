from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CompetitionReport:
    competition_id: str
    score: float | None
    gold_threshold: float
    silver_threshold: float
    bronze_threshold: float
    median_threshold: float
    any_medal: bool
    gold_medal: bool
    silver_medal: bool
    bronze_medal: bool
    above_median: bool
    submission_exists: bool
    valid_submission: bool
    is_lower_better: bool
    created_at: datetime
    submission_path: str

    def to_dict(self) -> dict:
        return {
            "competition_id": self.competition_id,
            "score": float(self.score) if self.score is not None else None,
            "gold_threshold": float(self.gold_threshold),
            "silver_threshold": float(self.silver_threshold),
            "bronze_threshold": float(self.bronze_threshold),
            "median_threshold": float(self.median_threshold),
            "any_medal": bool(self.any_medal),
            "gold_medal": bool(self.gold_medal),
            "silver_medal": bool(self.silver_medal),
            "bronze_medal": bool(self.bronze_medal),
            "above_median": bool(self.above_median),
            "submission_exists": bool(self.submission_exists),
            "valid_submission": bool(self.valid_submission),
            "is_lower_better": bool(self.is_lower_better),
            "created_at": self.created_at.isoformat(),
            "submission_path": self.submission_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CompetitionReport":
        payload = dict(data)
        created_at = payload.get("created_at")
        if isinstance(created_at, str):
            payload["created_at"] = datetime.fromisoformat(created_at)
        return cls(**payload)

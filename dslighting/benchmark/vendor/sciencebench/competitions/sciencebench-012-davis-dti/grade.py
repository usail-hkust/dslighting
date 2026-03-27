"""Grading function for ScienceBench Task 12 (DAVIS DTI repurposing)."""

from pathlib import Path

from dslighting.benchmark.grading.models import GradingRequest

GOLD_TOP5 = [
    "Foscarnet",
    "Boceprevir",
    "Sofosbuvir",
    "Amantadine",
    "Glecaprevir",
]
REMOVED_LAST5 = [
    "Abacavir",
    "Etravirine",
    "Rilpivirine",
    "Imiquimod",
    "Pyrimidine",
]


def _read_submission_lines(path: Path) -> list[str]:
    if not path.exists():
        print(f"Submission file missing: {path}")
        return []
    with path.open("r", encoding="utf-8") as handle:
        lines = [line.strip() for line in handle if line.strip()]
    return lines


def grade(request: GradingRequest) -> float:
    """Return 1.0 when ordering matches the reference criteria, else 0.0."""
    submission_path = request.submission.root

    lines = _read_submission_lines(submission_path)
    if not lines:
        return 0.0

    # Ensure disqualified drugs are absent
    data_correctness = all(rem not in "".join(lines) for rem in REMOVED_LAST5)
    if not data_correctness:
        print("Found disqualified antiviral in submission list")
        return 0.0

    if len(lines) < 5:
        print("Submission contains fewer than 5 entries")
        return 0.0

    top5_matches = all(GOLD_TOP5[i] in lines[i] for i in range(5))
    if not top5_matches:
        print("Top five antiviral ordering does not match reference")
        return 0.0

    return 1.0

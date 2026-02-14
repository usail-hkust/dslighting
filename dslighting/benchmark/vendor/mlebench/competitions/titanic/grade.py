import pandas as pd


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """
    Titanic accuracy grader.

    Expected columns:
    - `PassengerId` (int)
    - `Survived` (0/1)
    """
    # Basic validation
    if "PassengerId" not in submission.columns or "Survived" not in submission.columns:
        return 0.0
    if "PassengerId" not in answers.columns or "Survived" not in answers.columns:
        return 0.0

    merged = submission.merge(answers, on="PassengerId", suffixes=("_pred", "_true"))
    if merged.empty:
        return 0.0

    return float((merged["Survived_pred"] == merged["Survived_true"]).mean())


import pandas as pd
import numpy as np
from dslighting.benchmark.grading.models import GradingRequest

FLOAT_TOLERANCE = 0.01
IGNORE_ORDER    = True

def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path    = request.references.private_dir / "answer.csv"

    try:
        sub = pd.read_csv(submission_path, dtype=str)
        ans = pd.read_csv(answers_path,    dtype=str)
    except Exception:
        return 0.0

    sub.columns = [c.strip().lower() for c in sub.columns]
    ans.columns = [c.strip().lower() for c in ans.columns]

    if list(sub.columns) != list(ans.columns) or len(sub) != len(ans):
        return 0.0

    if IGNORE_ORDER:
        sub = sub.sort_values(list(sub.columns)).reset_index(drop=True)
        ans = ans.sort_values(list(ans.columns)).reset_index(drop=True)

    scores = []
    for col in ans.columns:
        a_num = pd.to_numeric(sub[col], errors="coerce")
        g_num = pd.to_numeric(ans[col], errors="coerce")
        if g_num.notna().mean() > 0.5:
            match = np.isclose(a_num.fillna(np.inf), g_num.fillna(np.inf),
                               rtol=FLOAT_TOLERANCE, equal_nan=True)
        else:
            match = sub[col].str.strip() == ans[col].str.strip()
        scores.append(float(match.mean()))

    return float(np.mean(scores)) if scores else 0.0

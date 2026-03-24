import sqlite3
import pandas as pd
import numpy as np
from dslighting.benchmark.grading.models import GradingRequest

FLOAT_TOL = 0.01

def _compare_table(agent_df, gold_df):
    agent_df = agent_df.astype(str)
    gold_df  = gold_df.astype(str)
    agent_df.columns = [c.strip().lower() for c in agent_df.columns]
    gold_df.columns  = [c.strip().lower() for c in gold_df.columns]
    if agent_df.shape != gold_df.shape:
        return 0.0
    if list(agent_df.columns) != list(gold_df.columns):
        return 0.0
    agent_df = agent_df.sort_values(list(agent_df.columns)).reset_index(drop=True)
    gold_df  = gold_df.sort_values(list(gold_df.columns)).reset_index(drop=True)
    scores = []
    for col in gold_df.columns:
        a_num = pd.to_numeric(agent_df[col], errors="coerce")
        g_num = pd.to_numeric(gold_df[col],  errors="coerce")
        if g_num.notna().mean() > 0.5:
            match = np.isclose(a_num.fillna(np.inf), g_num.fillna(np.inf),
                               rtol=FLOAT_TOL, equal_nan=True)
        else:
            match = agent_df[col].str.strip() == gold_df[col].str.strip()
        scores.append(match.mean())
    return float(np.mean(scores)) if scores else 0.0

def grade(request: GradingRequest) -> float:
    agent_db = request.submission.root
    gold_db  = request.references.private_dir / "sport.db"

    if not agent_db.exists() or not gold_db.exists():
        return 0.0

    try:
        conn_agent = sqlite3.connect(agent_db)
        conn_gold  = sqlite3.connect(gold_db)
    except Exception:
        return 0.0

    try:
        tables = [row[0] for row in conn_gold.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        table_scores = {}
        for table in tables:
            try:
                agent_df = pd.read_sql(f'SELECT * FROM "{table}"', conn_agent)
                gold_df  = pd.read_sql(f'SELECT * FROM "{table}"', conn_gold)
                table_scores[table] = _compare_table(agent_df, gold_df)
            except Exception:
                table_scores[table] = 0.0
    finally:
        conn_agent.close()
        conn_gold.close()

    return float(np.mean(list(table_scores.values()))) if table_scores else 0.0

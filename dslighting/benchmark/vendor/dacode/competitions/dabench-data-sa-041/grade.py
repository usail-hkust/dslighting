import pandas as pd, math

IGNORE_ORDER = True   # bool
CONDITION_COLS = []  # list

def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    tol = 1e-2
    def norm(v):
        if pd.isna(v): return "__NA__"
        if isinstance(v, float): return round(v / tol) * tol
        if isinstance(v, str): return v.lower().strip()
        return v
    def vec_hash(col, do_sort):
        vals = [norm(x) for x in col]
        return tuple(sorted(vals, key=str) if do_sort else vals)
    def match(g, p):
        if len(g) != len(p): return False
        if IGNORE_ORDER: g, p = sorted(g, key=lambda x: str(x)), sorted(p, key=lambda x: str(x))
        for a, b in zip(g, p):
            if pd.isna(a) and pd.isna(b): continue
            if isinstance(a, (int,float)) and isinstance(b, (int,float)):
                if not math.isclose(float(a), float(b), abs_tol=tol): return False
            elif isinstance(a,str) and isinstance(b,str):
                if a.lower().strip() != b.lower().strip(): return False
            elif a != b: return False
        return True
    gold = answers.iloc[:, CONDITION_COLS] if CONDITION_COLS else answers
    t_gold = gold.transpose().values.tolist()
    t_pred = submission.transpose().values.tolist()
    pred_hashes = {vec_hash(c, IGNORE_ORDER): True for c in t_pred}
    matches = 0
    for gc in t_gold:
        h = vec_hash(gc, IGNORE_ORDER)
        if h in pred_hashes or any(match(gc, pc) for pc in t_pred):
            matches += 1
    return matches / len(t_gold) if t_gold else 0.0

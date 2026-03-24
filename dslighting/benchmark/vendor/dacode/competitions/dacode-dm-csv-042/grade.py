import pandas as pd
import math

# 任务配置
IGNORE_ORDER = False   # True = 行顺序无关，False = 严格按行顺序比较
FLOAT_TOLERANCE = 0   # 整数比较


def normalize_col(name: str) -> str:
    """列名归一化：去空格、小写"""
    return str(name).strip().lower()


def parse_cell(val) -> object:
    """单元格解析：尝试转 float，否则返回 stripped string"""
    if pd.isna(val):
        return None
    text = str(val).strip()
    # 尝试解析为 float（处理百分比格式）
    try:
        if text.endswith("%"):
            return float(text[:-1]) / 100.0
        return float(text)
    except ValueError:
        return text.lower()


def compare_cells(gold_val, pred_val) -> bool:
    """比较两个单元格"""
    gold = parse_cell(gold_val)
    pred = parse_cell(pred_val)

    if gold is None and pred is None:
        return True
    if gold is None or pred is None:
        return False

    if isinstance(gold, float) and isinstance(pred, float):
        if gold == 0.0:
            return abs(pred) < 1e-9
        return abs(gold - pred) / abs(gold) <= FLOAT_TOLERANCE

    return str(gold) == str(pred)


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """
    逐行逐列比较 agent 输出的 CSV 与标准答案。
    submission: agent 输出的 CSV DataFrame
    answers: 标准答案 CSV DataFrame
    """
    if len(submission) == 0 or len(answers) == 0:
        return 0.0

    # 列名归一化
    submission.columns = [normalize_col(c) for c in submission.columns]
    answers.columns = [normalize_col(c) for c in answers.columns]

    # 列名必须完全一致
    if list(submission.columns) != list(answers.columns):
        return 0.0

    # 行数必须一致
    if len(submission) != len(answers):
        return 0.0

    if IGNORE_ORDER:
        # 把两个 DataFrame 都排序后再比较
        sort_cols = list(answers.columns)
        try:
            submission = submission.sort_values(sort_cols).reset_index(drop=True)
            answers = answers.sort_values(sort_cols).reset_index(drop=True)
        except Exception:
            pass

    # 逐格比较
    for col in answers.columns:
        for sub_val, ans_val in zip(submission[col], answers[col]):
            if not compare_cells(ans_val, sub_val):
                return 0.0

    return 1.0
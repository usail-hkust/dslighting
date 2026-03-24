import pandas as pd
import math
import json
from pathlib import Path

# 任务配置
IGNORE_ORDER = False   # True = 行顺序无关，False = 严格按行顺序比较
FLOAT_TOLERANCE = 0.01  # 相对误差容忍度，1%


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


def load_json_data(data):
    """Load JSON from file path or dict/list, or extract from DataFrame"""
    if isinstance(data, (str, Path)):
        with open(data, 'r') as f:
            return json.load(f)
    elif isinstance(data, pd.DataFrame):
        # Try to extract JSON from DataFrame
        if len(data) > 0:
            # Case 1: DataFrame has single cell with JSON string
            if len(data.columns) == 1 and len(data) == 1:
                val = data.iloc[0, 0]
                if isinstance(val, str):
                    return json.loads(val)
                elif isinstance(val, (dict, list)):
                    return val
            # Case 2: DataFrame has JSON keys as columns
            # Try to reconstruct dict from columns
            try:
                result = {}
                for col in data.columns:
                    val = data[col].iloc[0]
                    if isinstance(val, str):
                        result[col] = json.loads(val)
                    else:
                        result[col] = val
                return result
            except:
                pass
        return None
    elif isinstance(data, (dict, list)):
        return data
    return None


def grade(submission, answers) -> float:
    """
    比较 agent 输出的 JSON 与标准答案。
    submission: JSON 文件路径、DataFrame 或 dict
    answers: JSON 文件路径、DataFrame 或 dict
    """
    answer_data = load_json_data(answers)
    submission_data = load_json_data(submission)

    if answer_data is None or submission_data is None:
        return 0.0

    # 确保是字典
    if not isinstance(answer_data, dict) or not isinstance(submission_data, dict):
        return 0.0

    # 检查键是否一致
    if set(answer_data.keys()) != set(submission_data.keys()):
        return 0.0

    # 比较每个键的值
    for key in answer_data:
        ans_vals = answer_data[key]
        sub_vals = submission_data.get(key, [])

        # 值应该是列表
        if not isinstance(ans_vals, list) or not isinstance(sub_vals, list):
            return 0.0

        if len(ans_vals) != len(sub_vals):
            return 0.0

        for a, s in zip(ans_vals, sub_vals):
            if isinstance(a, (int, float)) and isinstance(s, (int, float)):
                if not math.isclose(a, s, rel_tol=FLOAT_TOLERANCE):
                    return 0.0
            elif a != s:
                return 0.0

    return 1.0
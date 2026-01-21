"""
Titanic 比赛评估器

评估 Titanic 比赛的提交结果
"""

import pandas as pd
from pathlib import Path


def grade(submission_path: str, answer_path: str = None) -> dict:
    """
    评估 Titanic 提交结果

    Args:
        submission_path: 提交文件路径
        answer_path: 答案文件路径（如果为 None，使用 dataset 配置）

    Returns:
        包含评估指标的字典
    """
    # 读取提交和答案
    submission = pd.read_csv(submission_path)

    if answer_path:
        answers = pd.read_csv(answer_path)
    else:
        raise ValueError("answer_path is required for grading")

    # 合并数据（确保顺序一致）
    merged = submission.merge(answers, on='PassengerId', suffixes=('_pred', '_true'))

    # 计算准确率
    accuracy = (merged['Survived_pred'] == merged['Survived_true']).mean()

    return {
        'accuracy': accuracy,
        'score': accuracy,  # DSLighting 使用 'score' 作为主要指标
        'num_samples': len(merged),
        'valid_submission': True
    }


if __name__ == "__main__":
    # 测试评估器
    import sys

    if len(sys.argv) > 1:
        submission_file = sys.argv[1]
    else:
        # 使用默认路径
        submission_file = "data/competitions/titanic/prepared/public/sampleSubmission.csv"

    if len(sys.argv) > 2:
        answer_file = sys.argv[2]
    else:
        answer_file = "data/competitions/titanic/prepared/private/test_answer.csv"

    result = grade(submission_file, answer_file)
    print(f"准确率: {result['accuracy']:.4f}")
    print(f"样本数: {result['num_samples']}")

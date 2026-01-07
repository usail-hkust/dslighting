import pandas as pd
import numpy as np


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """
    使用 RMSE 评分房价预测提交

    Args:
        submission: 提交的预测，列 [house_id, predicted_price]
        answers: 真实答案，列 [house_id, actual_price]

    Returns:
        float: RMSE 分数（越低越好）。
               如果提交无效，返回 inf
    """
    try:
        # 验证列名
        required_sub_cols = {'house_id', 'predicted_price'}
        required_ans_cols = {'house_id', 'actual_price'}

        if not required_sub_cols.issubset(submission.columns):
            print(f"❌ 提交文件缺少列: {required_sub_cols - set(submission.columns)}")
            return float('inf')

        if not required_ans_cols.issubset(answers.columns):
            print(f"❌ 答案文件缺少列: {required_ans_cols - set(answers.columns)}")
            return float('inf')

        # 按 house_id 合并
        merged = submission.merge(
            answers,
            on='house_id',
            how='inner',
            suffixes=('_sub', '_ans')
        )

        # 检查是否所有房屋都有预测
        if len(merged) != len(answers):
            missing_count = len(answers) - len(merged)
            print(f"⚠️  警告：提交缺少 {missing_count} 个房屋的预测")
            return float('inf')

        # 检查预测值是否有效
        if merged['predicted_price'].isna().any():
            print("❌ 预测包含 NaN 值")
            return float('inf')

        if (merged['predicted_price'] < 0).any():
            print("❌ 预测包含负值")
            return float('inf')

        # 计算 RMSE
        rmse = np.sqrt(
            np.mean(
                (merged['predicted_price'] - merged['actual_price']) ** 2
            )
        )

        print(f"✓ RMSE: {rmse:.2f}")
        return float(rmse)

    except Exception as e:
        print(f"❌ 评分过程出错: {e}")
        return float('inf')


if __name__ == "__main__":
    """测试评分函数"""
    # 创建测试数据
    test_submission = pd.DataFrame({
        'house_id': [1, 2, 3],
        'predicted_price': [250000.0, 350000.0, 420000.0]
    })

    test_answers = pd.DataFrame({
        'house_id': [1, 2, 3],
        'actual_price': [245000.0, 360000.0, 410000.0]
    })

    print("测试评分函数:")
    print("=" * 60)
    score = grade(test_submission, test_answers)
    print(f"测试 RMSE: {score:.2f}")

    # 测试无效提交
    print("\n测试无效提交（缺少房屋）:")
    print("=" * 60)
    invalid_submission = pd.DataFrame({
        'house_id': [1, 2],  # 缺少 house_id=3
        'predicted_price': [250000.0, 350000.0]
    })
    score = grade(invalid_submission, test_answers)
    print(f"无效提交 RMSE: {score}")

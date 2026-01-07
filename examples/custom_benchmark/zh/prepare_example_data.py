"""
生成示例房价数据

用于创建 custom-house-price-prediction 任务的原始数据
"""

import pandas as pd
import numpy as np
from pathlib import Path


def generate_house_data(n_samples=100, seed=42):
    """
    生成模拟房价数据

    Args:
        n_samples: 生成的样本数量
        seed: 随机种子

    Returns:
        DataFrame: 包含房屋特征和价格的数据框
    """
    np.random.seed(seed)

    # 生成特征
    data = {
        'house_id': range(1, n_samples + 1),
        'area': np.random.randint(800, 3500, n_samples),  # 居住面积（平方英尺）
        'bedrooms': np.random.randint(1, 6, n_samples),  # 卧室数量
        'age': np.random.randint(0, 50, n_samples),  # 房屋年龄
        'location_score': np.random.randint(1, 11, n_samples),  # 位置评分（1-10）
    }

    df = pd.DataFrame(data)

    # 模拟价格：基于特征的线性组合 + 随机噪声
    df['price'] = (
        df['area'] * 100 +  # 面积影响
        df['bedrooms'] * 15000 +  # 房间数影响
        df['location_score'] * 20000 +  # 位置影响
        -df['age'] * 500 +  # 房龄折旧
        np.random.normal(0, 20000, n_samples)  # 随机噪声
    )

    # 确保价格为正值
    df['price'] = df['price'].clip(lower=50000)

    return df


def main():
    """主函数：生成并保存数据"""
    # 创建目录
    raw_dir = Path(__file__).parent / "data" / "custom-house-price-prediction" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # 生成数据
    print("正在生成房价数据...")
    df = generate_house_data(n_samples=100)

    # 保存到 CSV
    output_file = raw_dir / "houses.csv"
    df.to_csv(output_file, index=False)

    # 显示统计信息
    print(f"\n✓ 成功生成 {len(df)} 条房价数据")
    print(f"✓ 保存到: {output_file}")
    print(f"\n数据统计:")
    print("=" * 60)
    print(df.describe())
    print(f"\n价格范围: ${df['price'].min():.2f} - ${df['price'].max():.2f}")
    print(f"平均价格: ${df['price'].mean():.2f}")


if __name__ == "__main__":
    main()

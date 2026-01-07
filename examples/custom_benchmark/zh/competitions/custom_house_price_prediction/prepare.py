from pathlib import Path
import pandas as pd


def prepare(raw: Path, public: Path, private: Path):
    """
    准备房价预测数据集

    将原始数据划分为：
    - 训练集（80%）→ public/train.csv
    - 测试集（20%）→ private/answer.csv
    - 样本提交文件 → public/sample_submission.csv

    Args:
        raw: 原始数据目录（包含 houses.csv）
        public: 公开数据目录（参赛者可见）
        private: 私有数据目录（评分用）
    """
    # 加载原始数据
    data_file = raw / "houses.csv"
    if not data_file.exists():
        raise FileNotFoundError(f"原始数据文件不存在: {data_file}")

    print(f"加载原始数据: {data_file}")
    df = pd.read_csv(data_file)
    print(f"✓ 共 {len(df)} 条数据")

    # 划分训练集和测试集（80/20）
    train_size = int(len(df) * 0.8)
    train_df = df.iloc[:train_size].copy()
    test_df = df.iloc[train_size:].copy()

    print(f"✓ 训练集: {len(train_df)} 条")
    print(f"✓ 测试集: {len(test_df)} 条")

    # 1. 保存训练数据到 public/ (包含价格)
    train_file = public / "train.csv"
    train_df.to_csv(train_file, index=False)
    print(f"✓ 训练数据已保存: {train_file}")

    # 2. 创建样本提交文件（占位符）
    sample_submission = pd.DataFrame({
        'house_id': test_df['house_id'],
        'predicted_price': [0.0] * len(test_df)  # 占位符
    })
    sample_file = public / "sample_submission.csv"
    sample_submission.to_csv(sample_file, index=False)
    print(f"✓ 样本提交文件已创建: {sample_file}")

    # 3. 保存答案到 private/ (测试集的真实价格)
    answers = test_df[['house_id', 'price']].rename(columns={'price': 'actual_price'})
    answer_file = private / "answer.csv"
    answers.to_csv(answer_file, index=False)
    print(f"✓ 答案文件已保存: {answer_file}")

    # 验证
    assert train_file.exists(), "训练文件创建失败"
    assert sample_file.exists(), "样本提交文件创建失败"
    assert answer_file.exists(), "答案文件创建失败"

    print("\n" + "=" * 60)
    print("✅ 数据准备完成")
    print("=" * 60)
    print(f"训练集: {train_file}")
    print(f"样本提交: {sample_file}")
    print(f"答案文件: {answer_file}")


if __name__ == "__main__":
    # 测试准备脚本
    import sys
    from pathlib import Path

    # 设置路径
    base_dir = Path(__file__).parent.parent.parent
    raw_dir = base_dir / "data" / "custom-house-price-prediction" / "raw"
    public_dir = base_dir / "data" / "custom-house-price-prediction" / "prepared" / "public"
    private_dir = base_dir / "data" / "custom-house-price-prediction" / "prepared" / "private"

    # 创建目录
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    # 运行准备
    try:
        prepare(raw_dir, public_dir, private_dir)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

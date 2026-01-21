#!/usr/bin/env python3
"""
DSLighting 项目初始化工具

帮助用户快速创建 Kaggle 项目的配置文件
可以独立运行，不依赖 DSLighting 源码
"""

import argparse
import sys
from pathlib import Path
import yaml


def create_project_structure(competition_id, competition_name, metric="accuracy"):
    """创建项目目录结构"""

    print(f"🚀 创建 Kaggle 项目: {competition_name}")
    print("="*80)

    # 1. 创建目录
    dirs = [
        f"data/raw/{competition_id}",
        f"data/competitions/{competition_id}/prepared/public",
        f"data/competitions/{competition_id}/prepared/private",
        f"registry/{competition_id}",
    ]

    print("\n📁 创建目录...")
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {dir_path}")

    # 2. 创建 config.yaml
    print(f"\n⚙️  创建配置文件...")

    config = {
        'id': competition_id,
        'name': competition_name,
        'competition_type': 'simple',
        'task_type': 'kaggle',
        'awards_medals': False,
        'description': 'description.md',
        'dataset': {
            'answers': f'{competition_id}/prepared/private/test_answer.csv',
            'sample_submission': f'{competition_id}/prepared/public/sampleSubmission.csv',
        },
        'grader': {
            'name': metric,
            'grade_fn': 'grade:grade',
        }
    }

    config_path = Path(f"registry/{competition_id}/config.yaml")
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"  ✅ registry/{competition_id}/config.yaml")

    # 3. 创建 grade.py
    print(f"\n📊 创建评估器...")

    grader_code = f'''"""
{competition_name} - 评估器
"""

import pandas as pd
import numpy as np
from pathlib import Path


def grade(submission_path: str, answer_path: str) -> dict:
    """
    评估提交结果

    Args:
        submission_path: 提交文件路径
        answer_path: 答案文件路径

    Returns:
        评估结果字典
    """
    # 读取文件
    submission = pd.read_csv(submission_path)
    answers = pd.read_csv(answer_path)

    # TODO: 根据你的任务调整评估逻辑
    # 确保提交和答案的列名匹配

    # 示例：假设第一列是 ID，第二列是预测值
    merged = submission.merge(answers, on=submission.columns[0], suffixes=('_pred', '_true'))

    # 计算指标（根据任务类型选择）
    if "{metric}" == "accuracy":
        from sklearn.metrics import accuracy_score
        score = accuracy_score(
            merged.iloc[:, 1],  # 预测列
            merged.iloc[:, -1]  # 真实列
        )
    elif "{metric}" in ["rmse", "mae", "rmsle"]:
        from sklearn.metrics import mean_squared_error, mean_absolute_error

        pred_col = merged.iloc[:, 1]
        true_col = merged.iloc[:, -1]

        if "{metric}" == "rmse":
            score = np.sqrt(mean_squared_error(true_col, pred_col))
        elif "{metric}" == "mae":
            score = mean_absolute_error(true_col, pred_col)
        elif "{metric}" == "rmsle":
            score = np.sqrt(mean_squared_error(np.log1p(true_col), np.log1p(pred_col)))
    else:
        raise ValueError(f"Unknown metric: {{metric}}")

    return {{
        'score': score,
        '{metric}': score,
        'num_samples': len(merged),
        'valid_submission': True
    }}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        submission_file = sys.argv[1]
    else:
        submission_file = "data/competitions/{competition_id}/prepared/public/sampleSubmission.csv"

    if len(sys.argv) > 2:
        answer_file = sys.argv[2]
    else:
        answer_file = "data/competitions/{competition_id}/prepared/private/test_answer.csv"

    result = grade(submission_file, answer_file)
    print(f"得分: {{result['score']:.4f}}")
    print(f"样本数: {{result['num_samples']}}")
'''

    grader_path = Path(f"registry/{competition_id}/grade.py")
    with open(grader_path, 'w') as f:
        f.write(grader_code)

    print(f"  ✅ registry/{competition_id}/grade.py")

    # 4. 创建 description.md
    print(f"\n📝 创建描述文件...")

    description = f'''# {competition_name}

## 任务描述

<!-- TODO: 添加任务描述 -->

## 数据说明

### 训练集 (train.csv)
<!-- TODO: 描述训练集特征 -->

### 测试集 (test.csv)
<!-- TODO: 描述测试集特征 -->

## 评估指标

**{metric}**: <!-- TODO: 说明指标含义 -->

## 提交格式

<!-- TODO: 说明提交格式 -->

## I/O 指令

<!-- TODO: 添加具体指令 -->

## 注意事项

<!-- TODO: 添加注意事项 -->
'''

    desc_path = Path(f"registry/{competition_id}/description.md")
    with open(desc_path, 'w') as f:
        f.write(description)

    print(f"  ✅ registry/{competition_id}/description.md")

    # 5. 创建数据准备脚本
    print(f"\n🔧 创建数据准备脚本...")

    prepare_script = f'''#!/usr/bin/env python3
"""
{competition_name} - 数据准备脚本

自动下载和准备 Kaggle 数据
"""

import subprocess
import zipfile
from pathlib import Path
import pandas as pd


def download_data():
    """下载 Kaggle 数据"""
    raw_dir = Path("data/raw/{competition_id}")
    raw_dir.mkdir(parents=True, exist_ok=True)

    print("📥 下载数据...")
    subprocess.run([
        "kaggle", "competitions", "download", "-c", "{competition_id}",
        "-p", str(raw_dir)
    ], check=True)

    print("✅ 下载完成")


def extract_data():
    """解压数据"""
    raw_dir = Path("data/raw/{competition_id}")

    zip_files = list(raw_dir.glob("*.zip"))
    for zip_file in zip_files:
        print(f"📦 解压: {{zip_file.name}}")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(raw_dir)
        zip_file.unlink()
        print(f"  ✅ 完成")


def prepare_data():
    """转换为 DSLighting 格式"""
    raw_dir = Path("data/raw/{competition_id}")
    prepared_public = Path("data/competitions/{competition_id}/prepared/public")

    # 读取数据（根据实际文件名调整）
    train_df = pd.read_csv(raw_dir / "train.csv")
    test_df = pd.read_csv(raw_dir / "test.csv")
    sample_submission = pd.read_csv(raw_dir / "sample_submission.csv")

    print(f"训练集: {{train_df.shape}}")
    print(f"测试集: {{test_df.shape}}")

    # 保存到标准位置
    train_df.to_csv(prepared_public / "train.csv", index=False)
    test_df.to_csv(prepared_public / "test.csv", index=False)
    sample_submission.to_csv(prepared_public / "sampleSubmission.csv", index=False)

    print("✅ 数据准备完成")

    # 注意：test_answer.csv 需要你手动创建
    print("⚠️  请手动创建 test_answer.csv（使用验证集或从 Kaggle 下载）")


def main():
    print("="*80)
    print("{competition_name} - 数据准备")
    print("="*80)
    print()

    # download_data()  # 如果已下载，注释掉
    # extract_data()   # 如果已解压，注释掉
    prepare_data()

    print()
    print("="*80)
    print("✅ 准备完成！")
    print("="*80)
    print()
    print("下一步:")
    print("1. 创建 test_answer.csv")
    print("2. 运行: python run.py")


if __name__ == "__main__":
    main()
'''

    prepare_path = Path(f"prepare_data.py")
    with open(prepare_path, 'w') as f:
        f.write(prepare_script)

    print(f"  ✅ prepare_data.py")

    # 6. 创建运行脚本
    print(f"\n▶️  创建运行脚本...")

    run_script = '''#!/usr/bin/env python3
"""
运行 DSLighting Agent
"""

import sys
from pathlib import Path

# 确保可以导入 dslighting
try:
    import dslighting
except ImportError:
    print("❌ 未找到 dslighting，请先安装:")
    print("   pip install dslighting")
    sys.exit(1)


def main():
    print("="*80)
    print("运行 DSLighting Agent")
    print("="*80)
    print()

    # 方式 1: 使用 task_id（推荐）
    print("方式 1: 使用 task_id")
    print("-"*80)

    try:
        data = dslighting.load_data("{competition_id}")
        print(f"✅ 数据加载: {{data}}")
        print()

        # 显示数据信息
        print(data.show())
        print()

        # 运行 Agent
        print("正在运行 Agent...")
        agent = dslighting.Agent()

        result = agent.run(
            data,
            model="openai/gpt-4",  # 或 "gpt-3.5-turbo"
            workflow="aide",
            max_iterations=10,
        )

        print()
        print("="*80)
        print("🎯 结果")
        print("="*80)
        print(f"分数: {{result.score}}")
        print(f"提交文件: {{result.output_path}}")

    except Exception as e:
        print(f"❌ 错误: {{e}}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
'''

    run_path = Path(f"run.py")
    with open(run_path, 'w') as f:
        f.write(run_script)

    print(f"  ✅ run.py")

    # 7. 创建 README
    print(f"\n📖 创建 README...")

    readme = f'''# {competition_name}

使用 DSLighting 参加 Kaggle {competition_name} 比赛

## 快速开始

### 1. 安装依赖

```bash
pip install dslighting kaggle
```

### 2. 配置 Kaggle API

```bash
mkdir -p ~/.kaggle
# 下载 kaggle.json 后移动到 ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

### 3. 准备数据

```bash
# 下载数据
kaggle competitions download -c {competition_id} -d data/raw/{competition_id}

# 解压
unzip data/raw/{competition_id}/*.zip -d data/raw/{competition_id}/

# 准备格式
python prepare_data.py
```

### 4. 运行 DSLighting

```bash
python run.py
```

## 项目结构

```
.
├── data/
│   ├── raw/{competition_id}/           # 原始下载的数据
│   └── competitions/{competition_id}/  # DSLighting 格式
│       └── prepared/
│           ├── public/                 # 训练和测试数据
│           └── private/                # 答案数据
├── registry/{competition_id}/          # Registry 配置
│   ├── config.yaml
│   ├── grade.py
│   └── description.md
├── prepare_data.py                     # 数据准备脚本
├── run.py                              # 运行脚本
└── README.md                           # 本文件
```

## 自定义

### 修改评估指标

编辑 `registry/{competition_id}/grade.py`

### 调整 Agent 参数

编辑 `run.py`，修改 `model`、`workflow`、`max_iterations` 等参数

## 提交到 Kaggle

```bash
kaggle competitions submit -c {competition_id} \\
  -f <submission_file> \\
  -m "Generated by DSLighting"
```

## 更多信息

- DSLighting 文档: https://github.com/usail-hkust/dslighting
- Kaggle 比赛页面: https://www.kaggle.com/c/{competition_id}
'''

    readme_path = Path("README.md")
    with open(readme_path, 'w') as f:
        f.write(readme)

    print(f"  ✅ README.md")

    # 8. 创建 .gitignore
    print(f"\n🔒 创建 .gitignore...")

    gitignore = '''# Data
data/raw/*
data/competitions/*/prepared/private/*

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# DSLighting runs
runs/
'''

    gitignore_path = Path(".gitignore")
    with open(gitignore_path, 'w') as f:
        f.write(gitignore)

    print(f"  ✅ .gitignore")

    # 完成
    print()
    print("="*80)
    print("🎉 项目创建完成！")
    print("="*80)
    print()
    print("📁 项目结构:")
    print(f"  📂 data/")
    print(f"  📂 registry/{competition_id}/")
    print(f"  📄 prepare_data.py")
    print(f"  📄 run.py")
    print(f"  📄 README.md")
    print()
    print("🚀 下一步:")
    print("  1. 配置 Kaggle API:")
    print("     mkdir -p ~/.kaggle")
    print("     # 下载 kaggle.json 并移动到 ~/.kaggle/")
    print()
    print("  2. 下载并准备数据:")
    print("     python prepare_data.py")
    print()
    print("  3. 创建 test_answer.csv（用于本地验证）")
    print("     # 可以使用交叉验证或从 Kaggle Discussion 下载")
    print()
    print("  4. 运行 DSLighting:")
    print("     python run.py")
    print()
    print("  5. 提交到 Kaggle:")
    print(f"     kaggle competitions submit -c {competition_id} -f <submission.csv>")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="DSLighting Kaggle 项目初始化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python dslighting_init.py --id titanic --name "Titanic Competition"
  python dslighting_init.py --id house-prices --name "House Prices" --metric rmse
        """
    )

    parser.add_argument(
        "--id",
        required=True,
        help="Kaggle competition ID (slug from URL)"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Competition display name"
    )
    parser.add_argument(
        "--metric",
        default="accuracy",
        choices=["accuracy", "rmse", "mae", "rmsle", "f1", "auc", "logloss"],
        help="Evaluation metric (default: accuracy)"
    )

    args = parser.parse_args()

    create_project_structure(args.id, args.name, args.metric)


if __name__ == "__main__":
    main()

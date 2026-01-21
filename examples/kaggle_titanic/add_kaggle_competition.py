#!/usr/bin/env python3
"""
添加新的 Kaggle 比赛到 DSLighting

这个脚本自动为新的 Kaggle 比赛创建必要的配置文件和数据结构
"""

import sys
import os
import argparse
from pathlib import Path
import pandas as pd
import yaml

def create_registry_config(competition_id, competition_name, metric="accuracy"):
    """创建 registry 配置文件"""

    registry_dir = Path("dslighting/registry") / competition_id
    registry_dir.mkdir(parents=True, exist_ok=True)

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

    config_path = registry_dir / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"✅ 创建配置: {config_path}")
    return config_path

def create_grader(competition_id):
    """创建 grader 文件"""

    registry_dir = Path("dslighting/registry") / competition_id

    grader_code = f'''"""
{competition_id} 比赛评估器

评估 {competition_id} 的提交结果
"""

import pandas as pd
from pathlib import Path


def grade(submission_path: str, answer_path: str = None) -> dict:
    """
    评估 {competition_id} 提交结果

    Args:
        submission_path: 提交文件路径
        answer_path: 答案文件路径

    Returns:
        包含评估指标的字典
    """
    # 读取提交和答案
    submission = pd.read_csv(submission_path)

    if answer_path:
        answers = pd.read_csv(answer_path)
    else:
        raise ValueError("answer_path is required for grading")

    # TODO: 实现你的评估逻辑
    # 示例：假设预测列名为 'target'
    merged = submission.merge(answers, on='id', suffixes=('_pred', '_true'))

    # 计算指标（根据任务类型修改）
    # 分类问题: accuracy, f1, auc
    # 回归问题: rmse, mae, rmsle
    from sklearn.metrics import accuracy_score
    score = accuracy_score(merged['target_pred'], merged['target_true'])

    return {{
        'score': score,
        'num_samples': len(merged),
        'valid_submission': True
    }}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        submission_file = sys.argv[1]
    else:
        submission_file = f"data/competitions/{competition_id}/prepared/public/sampleSubmission.csv"

    if len(sys.argv) > 2:
        answer_file = sys.argv[2]
    else:
        answer_file = f"data/competitions/{competition_id}/prepared/private/test_answer.csv"

    result = grade(submission_file, answer_file)
    print(f"得分: {{result['score']:.4f}}")
    print(f"样本数: {{result['num_samples']}}")
'''

    grader_path = registry_dir / "grade.py"
    with open(grader_path, 'w') as f:
        f.write(grader_code)

    print(f"✅ 创建 grader: {grader_path}")
    return grader_path

def create_description(competition_id, competition_name):
    """创建 description.md 文件"""

    registry_dir = Path("dslighting/registry") / competition_id

    description = f'''# {competition_name}

## 任务描述

<!-- TODO: 添加任务描述 -->

## 数据说明

### 训练集 (train.csv)
<!-- TODO: 描述训练集特征 -->

### 测试集 (test.csv)
<!-- TODO: 描述测试集特征 -->

## 评估指标

<!-- TODO: 说明评估指标 -->

## 提交格式

<!-- TODO: 说明提交格式 -->

## I/O 指令

<!-- TODO: 添加 I/O 指令 -->

## 注意事项

<!-- TODO: 添加注意事项 -->
'''

    desc_path = registry_dir / "description.md"
    with open(desc_path, 'w') as f:
        f.write(description)

    print(f"✅ 创建 description: {desc_path}")
    return desc_path

def create_data_directories(competition_id):
    """创建数据目录结构"""

    dirs = [
        f"data/raw/{{competition_id}}",
        f"data/competitions/{{competition_id}}/prepared/public",
        f"data/competitions/{{competition_id}}/prepared/private",
    ]

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {dir_path}")

def create_prepare_script(competition_id):
    """创建数据准备脚本模板"""

    script_content = f'''#!/usr/bin/env python3
"""
{competition_id} 数据准备脚本
"""

import pandas as pd
from pathlib import Path

def prepare_competition_data():
    """准备 {competition_id} 比赛数据"""

    # 目录配置
    raw_dir = Path("data/raw/{competition_id}")
    prepared_public = Path("data/competitions/{competition_id}/prepared/public")
    prepared_private = Path("data/competitions/{competition_id}/prepared/private")

    # 读取原始数据
    train_df = pd.read_csv(raw_dir / "train.csv")
    test_df = pd.read_csv(raw_dir / "test.csv")
    sample_submission = pd.read_csv(raw_dir / "sample_submission.csv")

    print(f"训练集: {{train_df.shape}}")
    print(f"测试集: {{test_df.shape}}")
    print(f"列名: {{list(train_df.columns)}}")

    # 保存到 prepared/public/
    train_df.to_csv(prepared_public / "train.csv", index=False)
    test_df.to_csv(prepared_public / "test.csv", index=False)
    sample_submission.to_csv(prepared_public / "sampleSubmission.csv", index=False)

    print(f"✅ 保存完成")

    # 注意：test_answer.csv 需要你自己创建
    # 可以通过以下方式：
    # 1. 使用交叉验证
    # 2. 从训练集分割
    # 3. 从 Kaggle Discussion 获取基准答案
    print(f"⚠️  请手动创建 test_answer.csv")

if __name__ == "__main__":
    prepare_competition_data()
'''

    script_path = Path(f"examples/{{competition_id}}/prepare_data.py")
    script_path.parent.mkdir(parents=True, exist_ok=True)

    with open(script_path, 'w') as f:
        f.write(script_content)

    print(f"✅ 创建准备脚本: {script_path}")
    return script_path

def main():
    parser = argparse.ArgumentParser(description="添加新的 Kaggle 比赛到 DSLighting")
    parser.add_argument("--id", required=True, help="比赛 ID (Kaggle competition slug)")
    parser.add_argument("--name", required=True, help="比赛名称")
    parser.add_argument("--metric", default="accuracy", help="评估指标 (accuracy, rmse, f1, etc.)")

    args = parser.parse_args()

    competition_id = args.id
    competition_name = args.name
    metric = args.metric

    print("="*80)
    print(f"添加 Kaggle 比赛: {{competition_name}}")
    print("="*80)
    print()

    # 1. 创建 registry 配置
    print("步骤 1: 创建 registry 配置")
    create_registry_config(competition_id, competition_name, metric)
    print()

    # 2. 创建 grader
    print("步骤 2: 创建 grader")
    create_grader(competition_id)
    print()

    # 3. 创建 description
    print("步骤 3: 创建 description")
    create_description(competition_id, competition_name)
    print()

    # 4. 创建数据目录
    print("步骤 4: 创建数据目录")
    create_data_directories(competition_id)
    print()

    # 5. 创建准备脚本
    print("步骤 5: 创建数据准备脚本")
    create_prepare_script(competition_id)
    print()

    print("="*80)
    print("✅ 完成！")
    print("="*80)
    print()
    print("下一步:")
    print(f"1. 下载比赛数据: kaggle competitions download -c {{competition_id}}")
    print(f"2. 解压数据到: data/raw/{{competition_id}}/")
    print(f"3. 运行准备脚本: python examples/{{competition_id}}/prepare_data.py")
    print(f"4. 自定义 grader: dslighting/registry/{{competition_id}}/grade.py")
    print(f"5. 运行 Agent: import dslighting; result = dslighting.run_agent(task_id='{{competition_id}}')")

if __name__ == "__main__":
    main()

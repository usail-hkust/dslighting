#!/usr/bin/env python3
"""
批量转换 DABench 任务到 MLE-Bench 格式

使用方法:
    python convert_dabench_to_mlebench.py --task-ids 0 5 6
    python convert_dabench_to_mlebench.py --all  # 转换所有任务
"""
import json
import re
from pathlib import Path
import argparse
from typing import Dict, List, Any


# 路径配置
DABENCH_DIR = Path('/path/to/DABench')
MLEBENCH_COMPETITIONS_DIR = Path('/path/to/data_science_agent_toolkit/mlebench/competitions')
DSFLOW_DATA_DIR = Path('/path/to/mlebench-data')


def load_dabench_data():
    """加载 DABench 的问题和答案"""
    questions_file = DABENCH_DIR / 'da-dev-questions.jsonl'
    labels_file = DABENCH_DIR / 'da-dev-labels.jsonl'

    questions = {}
    with open(questions_file, 'r') as f:
        for line in f:
            q = json.loads(line)
            questions[q['id']] = q

    labels = {}
    with open(labels_file, 'r') as f:
        for line in f:
            l = json.loads(line)
            labels[l['id']] = l

    return questions, labels


def format_answer(common_answers: List[List[str]]) -> str:
    """将 common_answers 格式化为答案字符串"""
    parts = []
    for key, value in common_answers:
        parts.append(f"@{key}[{value}]")
    return " ".join(parts)


def generate_sample_answer(common_answers: List[List[str]]) -> str:
    """生成示例答案（全部填0或默认值）"""
    parts = []
    for key, value in common_answers:
        # 尝试判断值的类型
        try:
            float(value)
            default_value = "0.00"
        except:
            default_value = "unknown"
        parts.append(f"@{key}[{default_value}]")
    return " ".join(parts)


def create_competition_id(task_id: int, question: str) -> str:
    """生成比赛 ID"""
    # 从问题中提取关键词
    words = re.findall(r'\b[a-z]+\b', question.lower())
    keywords = [w for w in words if len(w) > 3 and w not in ['calculate', 'create', 'perform', 'apply', 'check']]
    suffix = '-'.join(keywords[:3]) if keywords else 'task'
    return f"dabench-{task_id}-{suffix}"


def create_config_yaml(comp_id: str, task_name: str) -> str:
    """生成 config.yaml 内容"""
    return f"""id: {comp_id}
name: "DABench Task - {task_name}"
competition_type: code
awards_medals: false
prizes: null
description: mlebench/competitions/{comp_id}/description.md

dataset:
  answers: {comp_id}/prepared/private/answer.csv
  sample_submission: {comp_id}/prepared/public/sample_submission.csv

grader:
  name: exact_match
  grade_fn: mlebench.competitions.{comp_id}.grade:grade

preparer: mlebench.competitions.{comp_id}.prepare:prepare
"""


def create_description_md(question_data: Dict) -> str:
    """生成 description.md 内容"""
    concepts_str = ", ".join(question_data['concepts'])

    return f"""# DABench Task {question_data['id']} - {question_data['question']}

## Task Description

{question_data['question']}

## Concepts

{concepts_str}

## Data Description

Dataset file: `{question_data['file_name']}`

The data is available in the `train.csv` file in the public directory.

## Constraints

{question_data['constraints']}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

{question_data['format']}

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

{question_data['level'].capitalize()}
"""


def create_grade_py(common_answers: List[List[str]]) -> str:
    """生成 grade.py 内容"""
    # 提取所有的 key 名称
    keys = [key for key, _ in common_answers]

    return f"""import pandas as pd
import re


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    \"\"\"
    Grade the DABench submission.

    Args:
        submission: DataFrame with columns ['id', 'answer']
        answers: DataFrame with columns ['id', 'answer']

    Returns:
        float: 1.0 if exact match, 0.0 otherwise
    \"\"\"
    try:
        # Both should have exactly one row
        if len(submission) != 1 or len(answers) != 1:
            return 0.0

        # Get the submission and answer strings
        submission_str = str(submission.iloc[0]['answer']).strip()
        answer_str = str(answers.iloc[0]['answer']).strip()

        # Parse all key-value pairs
        # Expected keys: {keys}
        pattern = r'@(\\w+)\\[([^\\]]+)\\]'

        submission_dict = dict(re.findall(pattern, submission_str))
        answer_dict = dict(re.findall(pattern, answer_str))

        if not submission_dict or not answer_dict:
            print(f"Failed to parse: submission='{{submission_str}}', answer='{{answer_str}}'")
            return 0.0

        # Check if all keys match
        if set(submission_dict.keys()) != set(answer_dict.keys()):
            print(f"Key mismatch: submission has {{set(submission_dict.keys())}}, answer has {{set(answer_dict.keys())}}")
            return 0.0

        # Compare values
        all_match = True
        for key in answer_dict:
            submission_value = submission_dict[key]
            answer_value = answer_dict[key]

            # Try to compare as numbers
            try:
                sub_float = float(submission_value)
                ans_float = float(answer_value)
                if abs(sub_float - ans_float) >= 0.01:
                    print(f"Value mismatch for {{key}}: submission={{sub_float}}, answer={{ans_float}}")
                    all_match = False
                    break
            except ValueError:
                # Compare as strings (case-insensitive)
                if submission_value.lower() != answer_value.lower():
                    print(f"Value mismatch for {{key}}: submission='{{submission_value}}', answer='{{answer_value}}'")
                    all_match = False
                    break

        return 1.0 if all_match else 0.0

    except Exception as e:
        print(f"Error in grading: {{e}}")
        return 0.0
"""


def create_prepare_py(task_id: int, file_name: str, answer_str: str) -> str:
    """生成 prepare.py 内容"""
    # Escape single quotes in answer_str and use double quotes for the string
    answer_str_escaped = answer_str.replace('\\', '\\\\').replace('"', '\\"')

    return f"""from pathlib import Path
import pandas as pd


def prepare(raw: Path, public: Path, private: Path):
    \"\"\"
    Prepare the DABench task {task_id} dataset.

    Args:
        raw: Path to raw data directory (should contain {file_name})
        public: Path to public directory (for participants)
        private: Path to private directory (for grading)
    \"\"\"
    # Load the data
    data_file = raw / "{file_name}"
    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {{data_file}}")

    df = pd.read_csv(data_file)

    # Save the full dataset to public directory
    train_file = public / "train.csv"
    df.to_csv(train_file, index=False)
    print(f"Saved training data to {{train_file}} ({{len(df)}} rows)")

    # Create sample submission file
    sample_submission = pd.DataFrame({{
        'id': [{task_id}],
        'answer': ['@placeholder[0.00]']  # Placeholder answer
    }})
    sample_submission_file = public / "sample_submission.csv"
    sample_submission.to_csv(sample_submission_file, index=False)
    print(f"Created sample submission: {{sample_submission_file}}")

    # Create answer file (ground truth)
    answer = pd.DataFrame({{
        'id': [{task_id}],
        'answer': ["{answer_str_escaped}"]
    }})
    answer_file = private / "answer.csv"
    answer.to_csv(answer_file, index=False)
    print(f"Created answer file: {{answer_file}}")

    # Verify
    assert train_file.exists(), "Training file not created"
    assert sample_submission_file.exists(), "Sample submission not created"
    assert answer_file.exists(), "Answer file not created"

    print(f"✓ DABench task {task_id} prepared successfully")
"""


def create_leaderboard_csv() -> str:
    """生成 leaderboard.csv 内容"""
    return """scoreNullable,teamId,hasTeamName,submissionDate,score,hasScore
1.0000,1,True,2024-01-01 00:00:00,1.0000,True
0.0000,2,True,2024-01-01 00:00:00,0.0000,True
"""


def create_checksums_yaml(comp_id: str) -> str:
    """生成 checksums.yaml 内容"""
    return f"""# Checksums for {comp_id} dataset
zip: ""
"""


def create_dataset_prepare_py(comp_id: str) -> str:
    """生成数据集目录的 prepare.py 脚本"""
    return f"""#!/usr/bin/env python3
\"\"\"
数据准备脚本 - {comp_id}

使用：
    cd /path/to/mlebench-data/{comp_id}
    python prepare.py
\"\"\"
import sys
from pathlib import Path
import importlib.util

# 添加框架路径
sys.path.insert(0, '/path/to/data_science_agent_toolkit')

# 导入框架的 prepare 函数
prepare_file = Path('/path/to/data_science_agent_toolkit/mlebench/competitions/{comp_id}/prepare.py')
spec = importlib.util.spec_from_file_location("prepare_module", prepare_file)
prepare_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare_module)
prepare_fn = prepare_module.prepare

# 定义路径
current_dir = Path(__file__).parent
raw_dir = current_dir / 'raw'
public_dir = current_dir / 'prepared' / 'public'
private_dir = current_dir / 'prepared' / 'private'

# 创建目录
public_dir.mkdir(parents=True, exist_ok=True)
private_dir.mkdir(parents=True, exist_ok=True)

if __name__ == '__main__':
    print("=" * 60)
    print("Preparing {comp_id}...")
    print("=" * 60)
    print(f"  Raw:     {{raw_dir}}")
    print(f"  Public:  {{public_dir}}")
    print(f"  Private: {{private_dir}}")
    print()

    # 调用框架的 prepare 函数
    prepare_fn(raw_dir, public_dir, private_dir)

    print()
    print("=" * 60)
    print("✓ Dataset prepared successfully!")
    print("=" * 60)

    # 验证生成的文件
    print("\\nGenerated files:")
    print("  Public:")
    for file in sorted(public_dir.glob("*")):
        size = file.stat().st_size / 1024  # KB
        print(f"    - {{file.name}} ({{size:.2f}} KB)")

    print("  Private:")
    for file in sorted(private_dir.glob("*")):
        size = file.stat().st_size / 1024  # KB
        print(f"    - {{file.name}} ({{size:.2f}} KB)")
"""


def convert_task(task_id: int, questions: Dict, labels: Dict, dry_run: bool = False, auto_prepare: bool = False):
    """转换单个任务"""
    if task_id not in questions:
        print(f"❌ Task {task_id} not found in questions")
        return False

    if task_id not in labels:
        print(f"❌ Task {task_id} not found in labels")
        return False

    question_data = questions[task_id]
    label_data = labels[task_id]

    # 生成比赛 ID
    comp_id = create_competition_id(task_id, question_data['question'])
    print(f"\\n{'=' * 60}")
    print(f"Converting Task {task_id} -> {comp_id}")
    print(f"{'=' * 60}")

    # 格式化答案
    answer_str = format_answer(label_data['common_answers'])
    print(f"Answer: {answer_str}")

    if dry_run:
        print("  [DRY RUN] Skipping file creation")
        return True

    # 创建比赛注册目录
    comp_dir = MLEBENCH_COMPETITIONS_DIR / comp_id
    comp_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created competition directory: {comp_dir}")

    # 创建所有文件
    (comp_dir / 'config.yaml').write_text(create_config_yaml(comp_id, question_data['question'][:50]))
    (comp_dir / 'description.md').write_text(create_description_md(question_data))
    (comp_dir / 'grade.py').write_text(create_grade_py(label_data['common_answers']))
    (comp_dir / 'prepare.py').write_text(create_prepare_py(task_id, question_data['file_name'], answer_str))
    (comp_dir / 'leaderboard.csv').write_text(create_leaderboard_csv())
    (comp_dir / 'checksums.yaml').write_text(create_checksums_yaml(comp_id))
    print(f"✓ Created all competition files")

    # 创建数据集目录
    data_dir = DSFLOW_DATA_DIR / comp_id
    raw_dir = data_dir / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)

    # 复制数据文件
    source_file = DABENCH_DIR / 'da-dev-tables' / question_data['file_name']
    dest_file = raw_dir / question_data['file_name']
    if source_file.exists():
        import shutil
        shutil.copy(source_file, dest_file)
        print(f"✓ Copied data file: {dest_file}")
    else:
        print(f"⚠ Warning: Data file not found: {source_file}")

    # 创建便捷准备脚本
    (data_dir / 'prepare.py').write_text(create_dataset_prepare_py(comp_id))
    print(f"✓ Created dataset prepare script")

    # 自动准备数据（如果启用）
    if auto_prepare:
        print(f"\\n📦 Auto-preparing data for {comp_id}...")
        try:
            import subprocess
            import sys
            result = subprocess.run(
                [sys.executable, str(data_dir / 'prepare.py')],
                cwd=str(data_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print(f"✅ Data prepared successfully!")
                # 验证数据文件是否存在
                public_dir = data_dir / 'prepared' / 'public'
                private_dir = data_dir / 'prepared' / 'private'
                if (public_dir / 'train.csv').exists() and (private_dir / 'answer.csv').exists():
                    print(f"✓ Verified: All data files created")
                else:
                    print(f"⚠ Warning: Some data files may be missing")
            else:
                print(f"❌ Failed to prepare data:")
                print(result.stderr)
                return False
        except subprocess.TimeoutExpired:
            print(f"❌ Data preparation timed out (>60s)")
            return False
        except Exception as e:
            print(f"❌ Error during data preparation: {e}")
            return False

    print(f"✅ Task {task_id} converted successfully!")
    return True


def main():
    parser = argparse.ArgumentParser(description='Convert DABench tasks to MLE-Bench format')
    parser.add_argument('--task-ids', type=int, nargs='+', help='Task IDs to convert')
    parser.add_argument('--all', action='store_true', help='Convert all tasks')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (do not create files)')
    parser.add_argument('--auto-prepare', action='store_true', help='Automatically prepare data after conversion')
    parser.add_argument('--list', action='store_true', help='List all available tasks')

    args = parser.parse_args()

    # 加载数据
    questions, labels = load_dabench_data()

    if args.list:
        print("\\nAvailable DABench tasks:")
        print(f"{'=' * 80}")
        for task_id in sorted(questions.keys()):
            q = questions[task_id]
            print(f"Task {task_id:3d} [{q['level']:6s}]: {q['question'][:60]}...")
        print(f"{'=' * 80}")
        print(f"Total: {len(questions)} tasks")
        return

    # 确定要转换的任务
    if args.all:
        task_ids = sorted(questions.keys())
    elif args.task_ids:
        task_ids = args.task_ids
    else:
        print("Error: Please specify --task-ids or --all")
        parser.print_help()
        return

    # 转换任务
    print(f"\\nConverting {len(task_ids)} task(s)...")
    if args.auto_prepare:
        print(f"⚡ Auto-prepare mode enabled - data will be prepared automatically")
    success_count = 0
    for task_id in task_ids:
        if convert_task(task_id, questions, labels, dry_run=args.dry_run, auto_prepare=args.auto_prepare):
            success_count += 1

    print(f"\\n{'=' * 60}")
    print(f"Conversion complete: {success_count}/{len(task_ids)} tasks successful")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
使用 Kaggle API 自动创建 DSLighting 项目

这个工具会：
1. 调用 Kaggle API 获取比赛信息
2. 下载所需数据文件
3. 自动检测数据格式
4. 转换为 DSLighting 标准格式
5. 生成所有配置文件

用法:
    python kaggle_auto_setup.py --competition titanic
    python kaggle_auto_setup.py --competition house-prices-advanced-regression-techniques
"""

import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import yaml
from kaggle.api.kaggle_api_extended import KaggleApi


class KaggleAPI:
    """Kaggle API 封装"""

    def __init__(self):
        """初始化 Kaggle API"""
        self.api = KaggleApi()
        try:
            self.api.authenticate()
        except Exception as e:
            print(f"❌ Kaggle API 认证失败: {e}")
            print("请确保已配置 KAGGLE_API_TOKEN 环境变量或 ~/.kaggle/kaggle.json 文件")
            sys.exit(1)

    def get_competition_info(self, competition_id: str) -> Dict:
        """获取比赛信息"""
        print(f"📡 获取比赛信息: {competition_id}")

        try:
            # 从比赛列表中获取
            competitions = self.api.competitions_list(search=competition_id)
            for comp in competitions:
                # 只检查 ref 属性
                if hasattr(comp, 'ref') and comp.ref == competition_id:
                    info = {
                        "id": comp.ref,
                        "title": comp.title,
                        "description": comp.description if hasattr(comp, 'description') else "",
                        "reward": comp.rewardAmount if hasattr(comp, 'rewardAmount') else "",
                        "deadline": comp.deadline if hasattr(comp, 'deadline') else "",
                    }

                    return info

            # 如果没有精确匹配，尝试模糊匹配
            for comp in competitions:
                if hasattr(comp, 'ref') and competition_id.lower() in comp.ref.lower():
                    info = {
                        "id": comp.ref,
                        "title": comp.title,
                        "description": comp.description if hasattr(comp, 'description') else "",
                        "reward": comp.rewardAmount if hasattr(comp, 'rewardAmount') else "",
                        "deadline": comp.deadline if hasattr(comp, 'deadline') else "",
                    }

                    return info

            return {"id": competition_id, "title": competition_id, "description": "", "full_description": ""}
        except Exception as e:
            print(f"⚠️  无法获取比赛信息: {e}")
            return {"id": competition_id, "title": competition_id, "description": "", "full_description": ""}

    def list_files(self, competition_id: str) -> List[Dict]:
        """列出比赛文件"""
        print(f"📋 列出数据文件: {competition_id}")

        try:
            files_response = self.api.competition_list_files(competition_id)
            # 转换为字典列表
            files = []
            for f in files_response:
                files.append({
                    "name": f.name,
                    "size": f.totalBytes if hasattr(f, 'totalBytes') else 0,
                    "creationDate": str(f.creationDate) if hasattr(f, 'creationDate') else ""
                })
            return files
        except Exception as e:
            print(f"⚠️  无法列出文件: {e}")
            return []

    def download_files(self, competition_id: str, dest_dir: Path):
        """下载所有文件"""
        print(f"📥 下载数据文件: {competition_id}")

        dest_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.api.competition_download_files(
                competition_id,
                path=str(dest_dir),
                quiet=False
            )
            print(f"✅ 下载完成: {dest_dir}")
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            sys.exit(1)


class DataAnalyzer:
    """数据分析器"""

    def analyze_file(self, file_path: Path) -> Dict:
        """分析数据文件"""
        try:
            if file_path.suffix == '.csv':
                return self._analyze_csv(file_path)
            elif file_path.suffix in ['.xlsx', '.xls']:
                return self._analyze_excel(file_path)
            elif file_path.suffix == '.parquet':
                return self._analyze_parquet(file_path)
            else:
                return {"type": "unknown", "error": "Unsupported format"}
        except Exception as e:
            return {"type": "error", "error": str(e)}

    def _analyze_csv(self, file_path: Path) -> Dict:
        """分析 CSV 文件"""
        df = pd.read_csv(file_path, nrows=1000)

        # 检测是否为训练集（包含标签列）
        label_cols = self._detect_label_columns(df)

        # 检测是否为测试集
        is_test = 'test' in file_path.name.lower()

        # 检测是否为提交示例
        is_submission = any(word in file_path.name.lower()
                          for word in ['sample', 'submission'])

        return {
            "type": "csv",
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "label_columns": label_cols,
            "is_test": is_test,
            "is_submission": is_submission,
            "has_id": self._has_id_column(df),
        }

    def _detect_label_columns(self, df: pd.DataFrame) -> List[str]:
        """检测可能的标签列"""
        label_cols = []

        # 常见的标签列名
        common_labels = ['target', 'label', 'class', 'price', 'survived',
                        'sales', 'demand', 'count', 'prediction']

        for col in df.columns:
            if col.lower() in common_labels:
                label_cols.append(col)

        # 检查是否为分类任务
        for col in df.columns:
            if df[col].nunique() < 20 and df[col].dtype in ['int64', 'object']:
                if col not in label_cols:
                    label_cols.append(col)

        return label_cols

    def _has_id_column(self, df: pd.DataFrame) -> bool:
        """检查是否有 ID 列"""
        id_keywords = ['id', 'ID', 'Id']
        return any(col in df.columns for col in id_keywords)

    def _analyze_excel(self, file_path: Path) -> Dict:
        """分析 Excel 文件"""
        df = pd.read_excel(file_path, nrows=1000)
        return {
            "type": "excel",
            "shape": df.shape,
            "columns": list(df.columns),
        }

    def _analyze_parquet(self, file_path: Path) -> Dict:
        """分析 Parquet 文件"""
        df = pd.read_parquet(file_path)
        return {
            "type": "parquet",
            "shape": df.shape,
            "columns": list(df.columns),
        }


class DSLightingSetup:
    """DSLighting 项目设置器"""

    def __init__(self, competition_id: str, project_dir: Path = None):
        self.competition_id = competition_id
        self.project_dir = project_dir or Path.cwd()
        self.kaggle_api = KaggleAPI()
        self.analyzer = DataAnalyzer()

    def setup(self):
        """完整设置流程"""
        print("="*80)
        print(f"🚀 DSLighting + Kaggle 自动设置")
        print(f"比赛: {self.competition_id}")
        print("="*80)
        print()

        # 1. 获取比赛信息
        comp_info = self.kaggle_api.get_competition_info(self.competition_id)
        competition_name = comp_info.get('title', self.competition_id)

        # 2. 列出文件
        files = self.kaggle_api.list_files(self.competition_id)
        print(f"找到 {len(files)} 个文件")
        for file in files:
            print(f"  - {file.get('name', 'unknown')}")
        print()

        # 3. 下载文件
        raw_dir = self.project_dir / "data" / "raw" / self.competition_id
        self.kaggle_api.download_files(self.competition_id, raw_dir)

        # 4. 解压文件
        extracted_files = self._extract_files(raw_dir)

        # 5. 分析文件并分类
        file_analysis = self._analyze_files(extracted_files)

        # 6. 检测评估指标
        metric = self._detect_metric(comp_info, file_analysis)

        # 7. 准备标准格式
        self._prepare_standard_format(file_analysis, metric)

        # 8. 生成配置文件
        self._generate_configs(competition_name, metric, file_analysis, comp_info)

        # 9. 生成运行脚本
        self._generate_scripts()

        # 10. 创建 README
        self._generate_readme(competition_name, comp_info)

        print()
        print("="*80)
        print("✅ 设置完成！")
        print("="*80)
        print()
        self._print_next_steps()

    def _extract_files(self, raw_dir: Path) -> List[Path]:
        """解压下载的文件"""
        print()
        print("📦 解压文件...")

        extracted_files = []

        # 处理 zip 文件
        for zip_file in raw_dir.glob("*.zip"):
            print(f"  解压: {zip_file.name}")
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(raw_dir)
            zip_file.unlink()

        # 列出所有数据文件
        for ext in ['*.csv', '*.xlsx', '*.xls', '*.parquet']:
            extracted_files.extend(raw_dir.glob(ext))

        print(f"✅ 解压完成，找到 {len(extracted_files)} 个数据文件")
        return extracted_files

    def _analyze_files(self, files: List[Path]) -> Dict[str, List[Dict]]:
        """分析文件并分类"""
        print()
        print("🔍 分析文件...")

        train_files = []
        test_files = []
        submission_files = []
        other_files = []

        for file_path in files:
            print(f"  分析: {file_path.name}")
            analysis = self.analyzer.analyze_file(file_path)

            file_info = {
                "path": file_path,
                "analysis": analysis
            }

            if analysis.get('is_submission'):
                submission_files.append(file_info)
            elif analysis.get('is_test'):
                test_files.append(file_info)
            elif analysis.get('label_columns'):
                train_files.append(file_info)
            else:
                other_files.append(file_info)

        print()
        print(f"✅ 分析结果:")
        print(f"  训练集: {len(train_files)} 个")
        print(f"  测试集: {len(test_files)} 个")
        print(f"  提交示例: {len(submission_files)} 个")
        print(f"  其他文件: {len(other_files)} 个")

        return {
            "train": train_files,
            "test": test_files,
            "submission": submission_files,
            "other": other_files
        }

    def _detect_metric(self, comp_info: Dict, file_analysis: Dict) -> str:
        """检测评估指标"""
        print()
        print("📊 检测评估指标...")

        # 从比赛描述检测
        description = comp_info.get('description', '').lower()

        # 关键词映射
        metric_keywords = {
            'accuracy': ['accuracy', 'classification', 'classify'],
            'rmse': ['rmse', 'root mean squared', 'regression'],
            'mae': ['mae', 'mean absolute', 'regression'],
            'rmsle': ['rmsle', 'root mean squared log'],
            'f1': ['f1', 'f-score'],
            'auc': ['auc', 'roc', 'area under curve'],
            'logloss': ['logloss', 'log loss'],
        }

        # 搜索关键词
        for metric, keywords in metric_keywords.items():
            if any(keyword in description for keyword in keywords):
                print(f"✅ 检测到指标: {metric}")
                return metric

        # 默认使用 accuracy
        print("⚠️  无法自动检测，使用默认指标: accuracy")
        return "accuracy"

    def _prepare_standard_format(self, file_analysis: Dict, metric: str):
        """准备 DSLighting 标准格式"""
        print()
        print("📁 准备 DSLighting 标准格式...")

        prepared_public = self.project_dir / "data" / "competitions" / self.competition_id / "prepared" / "public"
        prepared_private = self.project_dir / "data" / "competitions" / self.competition_id / "prepared" / "private"

        prepared_public.mkdir(parents=True, exist_ok=True)
        prepared_private.mkdir(parents=True, exist_ok=True)

        # 1. 处理训练集：分割成 train + validation (for test_answer)
        if file_analysis["train"]:
            train_file = file_analysis["train"][0]["path"]
            print(f"  📊 分割训练集...")

            # 读取训练数据
            train_df = pd.read_csv(train_file)

            # 分割：80% 训练，20% 验证
            from sklearn.model_selection import train_test_split
            train_split, val_split = train_test_split(
                train_df,
                test_size=0.2,
                random_state=42
            )

            # 保存新的训练集
            new_train_path = prepared_public / "train.csv"
            train_split.to_csv(new_train_path, index=False)
            print(f"  ✅ 训练集: train.csv ({len(train_split)} 行)")

            # 2. 从验证集创建 test_answer.csv
            if file_analysis["submission"]:
                submission_file = file_analysis["submission"][0]["path"]
                sample_sub = pd.read_csv(submission_file)

                # 获取 ID 列名（通常是第一列）
                id_col = sample_sub.columns[0]

                # 获取目标列名（通常是最后一列，除了 ID 列）
                target_col = sample_sub.columns[-1]

                # 从验证集创建 test_answer
                val_ids = val_split[id_col].values
                val_labels = val_split[target_col].values

                # 按照 sampleSubmission 的格式创建 test_answer
                test_answer = pd.DataFrame({
                    id_col: val_ids,
                    target_col: val_labels
                })

                test_answer_path = prepared_private / "test_answer.csv"
                test_answer.to_csv(test_answer_path, index=False)
                print(f"  ✅ 答案文件: test_answer.csv ({len(test_answer)} 行，从训练集分割)")
        else:
            # 没有训练集，创建占位符
            print(f"  ⚠️  未找到训练集，创建占位符")
            answer_placeholder = prepared_private / "test_answer.csv"
            if file_analysis["submission"]:
                sample_df = pd.read_csv(file_analysis["submission"][0]["path"])
                sample_df.iloc[:, 1:] = 0  # 占位符值
                sample_df.to_csv(answer_placeholder, index=False)
                print(f"  ⚠️  创建 test_answer 占位符")

        # 3. 复制测试集（Kaggle 原始测试集，用于最终预测）
        if file_analysis["test"]:
            test_file = file_analysis["test"][0]["path"]
            dest = prepared_public / "test.csv"
            self._convert_to_csv(test_file, dest)
            print(f"  ✅ 测试集: test.csv (Kaggle 原始测试集，无标签)")

        # 4. 复制提交示例
        if file_analysis["submission"]:
            submission_file = file_analysis["submission"][0]["path"]
            dest = prepared_public / "sampleSubmission.csv"
            self._convert_to_csv(submission_file, dest)
            print(f"  ✅ 提交示例: sampleSubmission.csv")

        print(f"\n✅ 数据准备完成: {prepared_public}")
        print(f"  📁 原始文件保存在: {file_analysis['train'][0]['path'].parent.parent if file_analysis['train'] else 'N/A'}")

    def _convert_to_csv(self, src: Path, dest: Path):
        """转换为 CSV 格式"""
        if src.suffix == '.csv':
            # 直接复制
            import shutil
            shutil.copy(src, dest)
        elif src.suffix in ['.xlsx', '.xls']:
            # Excel 转 CSV
            pd.read_excel(src).to_csv(dest, index=False)
        elif src.suffix == '.parquet':
            # Parquet 转 CSV
            pd.read_parquet(src).to_csv(dest, index=False)

    def _generate_configs(self, competition_name: str, metric: str, file_analysis: Dict, comp_info: Dict):
        """生成配置文件"""
        print()
        print("⚙️  生成配置文件...")

        registry_dir = self.project_dir / "registry" / self.competition_id
        registry_dir.mkdir(parents=True, exist_ok=True)

        # config.yaml
        config = {
            'id': self.competition_id,
            'name': competition_name,
            'competition_type': 'simple',
            'task_type': 'kaggle',
            'awards_medals': False,
            'description': 'description.md',
            'dataset': {
                'answers': f'{self.competition_id}/prepared/private/test_answer.csv',
                'sample_submission': f'{self.competition_id}/prepared/public/sampleSubmission.csv',
            },
            'grader': {
                'name': metric,
                'grade_fn': 'grade:grade',
            }
        }

        config_path = registry_dir / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        print(f"  ✅ config.yaml")

        # grade.py
        grade_code = f'''"""
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

    # 合并数据
    # 根据你的数据调整列名
    id_col = submission.columns[0]  # 假设第一列是 ID
    merged = submission.merge(answers, on=id_col, suffixes=('_pred', '_true'))

    # 计算指标
    metric = "{metric}"

    if metric == "accuracy":
        from sklearn.metrics import accuracy_score
        pred_col = submission.columns[1]
        true_col = answers.columns[1]
        score = accuracy_score(merged[true_col], merged[pred_col])
    elif metric == "rmse":
        from sklearn.metrics import mean_squared_error
        pred_col = submission.columns[1]
        true_col = answers.columns[1]
        score = np.sqrt(mean_squared_error(merged[true_col], merged[pred_col]))
    elif metric == "mae":
        from sklearn.metrics import mean_absolute_error
        pred_col = submission.columns[1]
        true_col = answers.columns[1]
        score = mean_absolute_error(merged[true_col], merged[pred_col])
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
        submission_file = "data/competitions/{self.competition_id}/prepared/public/sampleSubmission.csv"

    if len(sys.argv) > 2:
        answer_file = sys.argv[2]
    else:
        answer_file = "data/competitions/{self.competition_id}/prepared/private/test_answer.csv"

    result = grade(submission_file, answer_file)
    print(f"得分: {{result['score']:.4f}}")
'''

        grade_path = registry_dir / "grade.py"
        with open(grade_path, 'w') as f:
            f.write(grade_code)
        print(f"  ✅ grade.py")

        # description.md
        # 使用从 Kaggle API 获取的真实信息
        comp_desc = comp_info.get('description', '').strip()

        description = f'''# {competition_name}

{comp_desc if comp_desc else 'Predict outcomes for this competition.'}
'''

        desc_path = registry_dir / "description.md"
        with open(desc_path, 'w') as f:
            f.write(description)
        print(f"  ✅ description.md")

    def _generate_scripts(self):
        """生成运行脚本"""
        print()
        print("🔧 生成运行脚本...")

        # run.py
        run_script = f'''#!/usr/bin/env python3
"""
运行 DSLighting Agent
"""

import sys
from pathlib import Path

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

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

    try:
        # 加载数据（显式指定数据路径和注册表路径）
        data = dslighting.load_data(
            "data/competitions/{self.competition_id}",
            registry_dir="registry/{self.competition_id}"
        )

        # 显示数据信息
        print(data.show())
        print()

        # 运行 Agent
        print("正在运行 Agent...")
        agent = dslighting.Agent(
            model="openai/gpt-4",  # 或 "gpt-3.5-turbo"
            workflow="aide",
            max_iterations=10,
        )
        result = agent.run(data)

        print()
        print("="*80)
        print("🎯 结果")
        print("="*80)
        print(f"分数: {{result.score}}")
        print(f"提交文件: {{result.output}}")
        if result.workspace_path:
            print(f"工作空间: {{result.workspace_path}}")
        if result.artifacts_path:
            print(f"产物目录: {{result.artifacts_path}}")

    except Exception as e:
        print(f"❌ 错误: {{e}}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
'''

        run_path = self.project_dir / "run.py"
        with open(run_path, 'w') as f:
            f.write(run_script)
        print(f"  ✅ run.py")

    def _generate_readme(self, competition_name: str, comp_info: Dict):
        """生成 README"""
        readme_path = self.project_dir / "README.md"

        content = f'''# {competition_name}

使用 DSLighting 参加 Kaggle [{competition_name}] 比赛。

## 📊 比赛信息

- **比赛 ID**: {self.competition_id}
- **比赛名称**: {competition_name}
- **奖励**: {comp_info.get('reward', 'N/A')}
- **团队数**: {comp_info.get('teamCount', 'N/A')}
- **参赛者数**: {comp_info.get('userRanksTotal', 'N/A')}

## 🚀 快速开始

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

### 3. 数据已准备好

数据已经通过 Kaggle API 自动下载并转换为 DSLighting 格式。

### 4. 配置环境变量

复制 `.env.example` 为 `.env` 并填写你的 API 配置：

```bash
cp .env.example .env
# 编辑 .env 填写 API_KEY、API_BASE 等配置
```

### 5. 运行 DSLighting

```bash
python run.py
```

## 📁 项目结构

```
.
├── data/
│   ├── raw/{self.competition_id}/      # 原始下载的数据
│   └── competitions/{self.competition_id}/  # DSLighting 格式
│       └── prepared/
│           ├── public/                 # 训练和测试数据
│           └── private/                # 答案数据
├── registry/{self.competition_id}/     # Registry 配置
│   ├── config.yaml
│   ├── grade.py
│   └── description.md
├── run.py                              # 运行脚本
├── .env.example                        # 环境变量模板
├── .env                                # 环境变量（需要创建）
└── README.md                           # 本文件
```

## ⚠️ 重要提示

**test_answer.csv**: 这个文件是占位符，用于本地验证。你需要：

1. 从 Kaggle Discussion 获取基准答案
2. 或使用交叉验证
3. 或从训练集分割出验证集

## 📤 提交到 Kaggle

```bash
kaggle competitions submit -c {self.competition_id} \\
  -f <submission_file> \\
  -m "Generated by DSLighting"
```

## 🔗 相关链接

- [Kaggle 比赛页面](https://www.kaggle.com/c/{self.competition_id})
- [DSLighting 文档](https://github.com/usail-hkust/dslighting)

---

使用 DSLighting + Kaggle API 自动生成 🚀
'''

        with open(readme_path, 'w') as f:
            f.write(content)
        print(f"  ✅ README.md")

        # .env.example
        env_example = self.project_dir / ".env.example"
        with open(env_example, 'w') as f:
            f.write("""# API 配置
API_KEY=your-api-key-here
API_BASE=https://api.openai.com/v1
LLM_MODEL=openai/gpt-4
""")
        print(f"  ✅ .env.example")
        print(f"  ⚠️  请复制 .env.example 为 .env 并填写你的 API 配置")

    def _print_next_steps(self):
        """打印下一步操作"""
        print("📋 下一步:")
        print()
        print("1. 复制 .env.example 为 .env 并填写 API 配置")
        print("2. 查看 README.md 了解比赛信息")
        print("3. 运行: python run.py")
        print("4. 提交结果到 Kaggle")
        print()
        print("💡 提示: 你可以修改 run.py 中的参数来调整 Agent 行为")


def main():
    parser = argparse.ArgumentParser(
        description="使用 Kaggle API 自动创建 DSLighting 项目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python kaggle_auto_setup.py --competition titanic
  python kaggle_auto_setup.py --competition house-prices-advanced-regression-techniques
  python kaggle_auto_setup.py --competition digit-recognizer --dir ./my-project
        """
    )

    parser.add_argument(
        "--competition", "-c",
        required=True,
        help="Kaggle competition ID (slug from URL)"
    )
    parser.add_argument(
        "--dir", "-d",
        default=None,
        help="项目目录（默认为当前目录）"
    )

    args = parser.parse_args()

    # 检查 Kaggle API 配置（支持 kaggle.json 或环境变量）
    import os
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    has_api_token = os.environ.get("KAGGLE_API_TOKEN") is not None

    if not kaggle_json.exists() and not has_api_token:
        print("❌ 未找到 Kaggle API 配置")
        print()
        print("请选择以下任一方式配置:")
        print()
        print("方式1: 使用环境变量（推荐）")
        print("1. 访问: https://www.kaggle.com/")
        print("2. 登录 → 账户设置 → API → Create New API Token")
        print("3. 复制 API Token")
        print("4. 运行: export KAGGLE_API_TOKEN=你的Token")
        print()
        print("方式2: 使用配置文件")
        print("1. 访问: https://www.kaggle.com/")
        print("2. 登录 → 账户设置 → API → Create New API Token")
        print("3. 下载 kaggle.json")
        print("4. 运行: mkdir -p ~/.kaggle")
        print("5. 运行: mv ~/Downloads/kaggle.json ~/.kaggle/")
        print("6. 运行: chmod 600 ~/.kaggle/kaggle.json")
        sys.exit(1)

    if has_api_token:
        print("✅ 使用环境变量 KAGGLE_API_TOKEN")
    else:
        print("✅ 使用配置文件 ~/.kaggle/kaggle.json")

    # 创建项目目录
    project_dir = Path(args.dir) if args.dir else Path.cwd()

    # 运行设置
    setup = DSLightingSetup(args.competition, project_dir)
    setup.setup()


if __name__ == "__main__":
    main()

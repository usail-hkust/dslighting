#!/usr/bin/env python3
"""
Titanic 数据准备脚本

这个脚本自动完成以下任务：
1. 下载 Titanic 数据集
2. 解压数据
3. 转换为 DSLighting 标准格式
4. 创建必要的目录结构
"""

import os
import subprocess
import zipfile
from pathlib import Path
import pandas as pd
import sys

def run_command(cmd, description=""):
    """运行 shell 命令"""
    if description:
        print(f"📌 {description}")
    print(f"▶ 运行: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ 错误: {result.stderr}")
        sys.exit(1)
    else:
        print(f"✅ 成功")
        if result.stdout:
            print(result.stdout)

def main():
    print("="*80)
    print("DSLighting - Titanic 数据准备脚本")
    print("="*80)
    print()

    # 项目根目录
    project_root = Path.cwd().parent.parent
    print(f"📁 项目根目录: {project_root}")

    # 1. 创建目录结构
    print("\n" + "="*80)
    print("步骤 1: 创建目录结构")
    print("="*80)

    dirs_to_create = [
        "data/raw/titanic",
        "data/competitions/titanic/prepared/public",
        "data/competitions/titanic/prepared/private",
    ]

    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {dir_path}")

    # 2. 检查 kaggle.json
    print("\n" + "="*80)
    print("步骤 2: 检查 Kaggle API 配置")
    print("="*80)

    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if not kaggle_json.exists():
        print("❌ 未找到 Kaggle API Token")
        print("\n请按以下步骤配置:")
        print("1. 访问: https://www.kaggle.com/")
        print("2. 登录 → 账户设置 → API → Create New API Token")
        print("3. 下载 kaggle.json")
        print("4. 运行: mkdir -p ~/.kaggle")
        print("5. 运行: mv ~/Downloads/kaggle.json ~/.kaggle/")
        print("6. 运行: chmod 600 ~/.kaggle/kaggle.json")
        sys.exit(1)
    else:
        print(f"✅ 找到 Kaggle 配置: {kaggle_json}")

    # 3. 下载 Titanic 数据
    print("\n" + "="*80)
    print("步骤 3: 下载 Titanic 数据集")
    print("="*80)

    raw_dir = project_root / "data/raw/titanic"
    run_command(
        f"cd {raw_dir} && kaggle competitions download -c titanic",
        "下载 Titanic 数据..."
    )

    # 4. 解压数据
    print("\n" + "="*80)
    print("步骤 4: 解压数据")
    print("="*80)

    zip_file = raw_dir / "titanic.zip"
    if zip_file.exists():
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(raw_dir)
        print(f"✅ 解压完成: {zip_file}")
        os.remove(zip_file)
        print(f"✅ 删除 zip 文件")
    else:
        print("⚠️  未找到 titanic.zip，可能已经解压过了")

    # 5. 准备标准格式
    print("\n" + "="*80)
    print("步骤 5: 转换为 DSLighting 标准格式")
    print("="*80)

    # 读取数据
    train_df = pd.read_csv(raw_dir / "train.csv")
    test_df = pd.read_csv(raw_dir / "test.csv")
    gender_submission = pd.read_csv(raw_dir / "gender_submission.csv")

    print(f"✅ 读取训练集: {train_df.shape}")
    print(f"✅ 读取测试集: {test_df.shape}")

    # 保存到 prepared/public/
    prepared_public = project_root / "data/competitions/titanic/prepared/public"

    train_df.to_csv(prepared_public / "train.csv", index=False)
    print(f"✅ 保存: train.csv")

    test_df.to_csv(prepared_public / "test.csv", index=False)
    print(f"✅ 保存: test.csv")

    gender_submission.to_csv(prepared_public / "sampleSubmission.csv", index=False)
    print(f"✅ 保存: sampleSubmission.csv")

    # 6. 创建测试答案（使用 gender_submission 作为示例）
    print("\n" + "="*80)
    print("步骤 6: 创建测试答案（用于本地验证）")
    print("="*80)

    prepared_private = project_root / "data/competitions/titanic/prepared/private"

    # 注意：实际比赛中我们不知道测试集答案
    # 这里使用 gender_submission 作为占位符
    # 实际使用时，你可以：
    # 1. 使用交叉验证
    # 2. 从训练集分割出验证集
    # 3. 从 Kaggle Discussion 找基准答案

    # 为了示例，我们创建一个假的答案文件
    # 实际使用时需要替换为真实答案
    test_answer = gender_submission.copy()
    test_answer.to_csv(prepared_private / "test_answer.csv", index=False)
    print(f"✅ 保存: test_answer.csv (占位符)")
    print("⚠️  注意: test_answer.csv 是占位符，实际使用需要替换为真实答案")

    # 7. 创建数据摘要
    print("\n" + "="*80)
    print("步骤 7: 数据摘要")
    print("="*80)

    print(f"\n训练集形状: {train_df.shape}")
    print(f"测试集形状: {test_df.shape}")
    print(f"\n训练集列名:\n{list(train_df.columns)}")
    print(f"\n训练集前5行:\n{train_df.head()}")
    print(f"\n缺失值统计:\n{train_df.isnull().sum()}")

    # 8. 验证格式
    print("\n" + "="*80)
    print("步骤 8: 验证数据格式")
    print("="*80)

    required_files = [
        "data/competitions/titanic/prepared/public/train.csv",
        "data/competitions/titanic/prepared/public/test.csv",
        "data/competitions/titanic/prepared/public/sampleSubmission.csv",
        "data/competitions/titanic/prepared/private/test_answer.csv",
    ]

    all_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            all_exist = False

    if all_exist:
        print("\n" + "="*80)
        print("🎉 数据准备完成！")
        print("="*80)
        print("\n下一步:")
        print("1. 运行示例: python run_titanic.py")
        print("2. 或使用 API: import dslighting; result = dslighting.run_agent(task_id='titanic')")
    else:
        print("\n❌ 数据准备失败，请检查错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()

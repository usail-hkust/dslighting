<div align="center">

# DSLIGHTING 日本語ガイド

個人向けの数学・科学エキスパートアシスタント。データ準備から評価まで、全工程のデータサイエンス実行を重視します。

[クイックスタート](#クイックスタート) · [ワークフロー](#ワークフロー) · [データ構成](#データ構成) · [設定](#設定)

</div>

## 概要

DSLIGHTING は統一された実行入口と拡張可能なワークフローを提供し、
データ準備・モデリング・評価・結果整理までの一連の流れをカバーします。

## 主な特長

- データサイエンスの全工程を統一 CLI で実行
- AIDE / AutoMind / DSAgent / AFlow などのワークフロー
- 実行ログと成果物の自動保存
- タスク登録とデータ準備の拡張が可能

## ワークフロー

- `aide`: 生成・実行・レビューのループ
- `automind`: 計画 + 記憶 + 分解
- `dsagent`: 構造化された計画/実行フロー
- `data_interpreter`: 迅速な実行とデバッグ
- `autokaggle`: SOP ベースの Kaggle フロー
- `aflow`: ワークフローのメタ最適化
- `deepanalyze`: 分析指向の実行

## クイックスタート

### 1. 環境構築

```bash
git clone <repository_url>
cd dslighting
python -m venv dsat
source dsat/bin/activate
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. API Key の設定

```bash
cp .env.example .env
```

### 4. 実行例

```bash
python run_benchmark.py \
  --workflow aide \
  --benchmark mle \
  --data-dir data/competitions \
  --task-id bike-sharing-demand
```

## データ構成

```
data/competitions/
  <competition-id>/
    config.yaml
    prepared/
      public/
      private/
```

ScienceBench も同じ構成を利用します。

## 設定

`config.yaml` で以下を設定できます。

- `competitions`: MLEBench の既定タスク
- `sciencebench_competitions`: ScienceBench の既定タスク
- `custom_model_pricing`: LiteLLM の料金上書き
- `run`: 実行ログの設定

---

[English](../README.md) · [中文](README_CN.md) · [Français](README_FR.md)

<div align="center">

<img src="../assets/dslighting.png" alt="DSLIGHTING Logo" width="180" style="border-radius: 15px;">

# DSLIGHTING：フルスタック・データサイエンス ワークフローアシスタント

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/PyPI-2.7.8-blue?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/dslighting/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/dslighting?style=flat-square&logo=pypi)](https://pypi.org/project/dslighting/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue?style=flat-square)](../LICENSE)

<p align="center">
  <a href="#quick-start"><img src="https://img.shields.io/badge/🚀-Quick_Start-green?style=for-the-badge" alt="Quick Start"></a>
  &nbsp;&nbsp;
  <a href="#core-features"><img src="https://img.shields.io/badge/⚡-Features-blue?style=for-the-badge" alt="Core Features"></a>
  &nbsp;&nbsp;
  <a href="https://luckyfan-cs.github.io/dslighting-web/"><img src="https://img.shields.io/badge/📚-Docs-orange?style=for-the-badge" alt="Documentation"></a>
  &nbsp;&nbsp;
  <a href="https://luckyfan-cs.github.io/dslighting-web/guide/getting-started.html"><img src="https://img.shields.io/badge/📖-User_Guide-purple?style=for-the-badge" alt="User Guide"></a>
  &nbsp;&nbsp;
  <a href="https://github.com/usail-hkust/dslighting/stargazers"><img src="https://img.shields.io/github/stars/usail-hkust/dslighting?style=for-the-badge" alt="Stars"></a>
  &nbsp;&nbsp;
  <img src="https://komarev.com/ghpvc/?username=usail-hkust&repo=dslighting&style=for-the-badge" alt="Profile views">
</p>

[🇨🇳 中文](../README.md) · [English](README_EN.md) · [Français](README_FR.md)

</div>

<div align="center">

🎯 **インテリジェント Agent ワークフロー** &nbsp;•&nbsp; 📊 **対話型データ可視化**<br>
🤖 **自動コード生成** &nbsp;•&nbsp; 📈 **エンドツーエンド評価**

[⭐ Star をお願いします](https://github.com/usail-hkust/dslighting/stargazers) &nbsp;•&nbsp; [💬 Discussions](https://github.com/usail-hkust/dslighting/discussions)

</div>

---

## 📸 Web UI プレビュー

### メインダッシュボード
![Main Dashboard](../assets/web_ui_main_page.png)

### 探索的データ分析 (EDA)
![EDA](../assets/web_ui_eda.png)

### カスタムタスク
![Custom Tasks](../assets/web_ui_user_custome_task.png)

### モデル学習
![Model Training](../assets/web_ui_model_training.png)

### レポート生成
![Report Generation](../assets/web_ui_report.png)

---

## 📖 概要

DSLIGHTING は、Agent スタイルのワークフローと再利用可能なデータレイアウトを備えたフルスタックのデータサイエンス支援システムです。タスクの実行・評価・反復をエンドツーエンドで支援します。

### ✨ 主な特徴

- 🤖 **複数の Agent ワークフロー**: aide、automind、dsagent などを統合
- 🔄 **メタ最適化フレームワーク**: AFlow による最適ワークフロー選択
- 📊 **Web 可視化インターフェース**: Next.js + FastAPI のダッシュボード
- 📝 **完全なログ**: 実行ごとの artifacts と要約を保存
- 🧩 **拡張可能アーキテクチャ**: 柔軟なタスク登録とデータ準備フロー
- 📦 **スマートなパッケージコンテキスト** (v1.4.0+): 利用可能パッケージを自動検出し互換性のないコードを回避
- 🎯 **内蔵データセット** (v1.8.1+): 事前準備なしで即実行できるサンプルデータ

---

## 🆕 クイック体験

### Step 1: DSLighting のインストール

```bash
# 仮想環境の作成（推奨）
python3 -m venv dslighting-env
source dslighting-env/bin/activate  # Windows: dslighting-env\Scripts\activate

# インストール
pip install dslighting
```

### Step 2: API キーの設定

`.env` を作成してキーを設定します:

```bash
# .env
API_KEY=sk-your-api-key-here
API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

**対応プロバイダ**:
- **OpenAI**: https://openai.com/ - API Base: `https://api.openai.com/v1`
- **Zhipu AI**（中国向け推奨）: https://bigmodel.cn/ - API Base: `https://open.bigmodel.cn/api/paas/v4`
- **SiliconFlow**: https://siliconflow.cn/ - API Base: `https://api.siliconflow.cn/v1`

### Step 3: 利用方法を選ぶ

---

**🌱 初心者モード（推奨）**

#### Option 1: 内蔵データセット（ゼロ準備）

**データ準備なし、1 行で実行！**

```python
# run_builtin.py
from dotenv import load_dotenv
load_dotenv()

import dslighting

# 内蔵データセットを使用（データパス不要）
result = dslighting.run_agent(task_id="bike-sharing-demand")

print(f"✅ 完了！Score: {result.score}")
```

**内蔵データセット**:
- `bike-sharing-demand` - 自転車需要予測
- ✅ 学習/テスト/回答ファイル一式を含む
- ✅ すぐに実行可能
- ✅ 体験・テストに最適

#### Option 2: オープンエンド API（初心者に推奨）

**分析・処理・モデリングの 3 つの機能**

```python
import dslighting

# Analyze - データ探索（2 回反復、ワークスペース保持）
result = dslighting.analyze(
    data="./data/titanic",
    description="乗客データの分布を分析",
    model="gpt-4o"
)

# Process - データクレンジング（3 回反復、ワークスペース保持）
result = dslighting.process(
    data="./data/titanic",
    description="欠損値と外れ値を処理",
    model="gpt-4o"
)

# Model - モデル学習（4 回反復、ワークスペース保持）
result = dslighting.model(
    data="./data/titanic",
    description="生存予測モデルを学習",
    model="gpt-4o"
)
```

**特長**:
- 🎯 **シンプルで直感的**: 3 つの API が代表的タスクに対応
- 🔄 **自動反復**: タスク種別ごとに適切な回数を設定
- 📁 **結果保持**: ワークスペースと成果物を自動保存

📖 **詳細チュートリアル**: [examples/open_ended_demo/README.md](../examples/open_ended_demo/README.md)

---

**🚀 高度モード（上級者向け）**

#### Option 3: グローバル設定

**一度設定すれば再利用可能**

```python
import dslighting

# データディレクトリとレジストリを設定
dslighting.setup(
    data_parent_dir="/path/to/data/competitions",
    registry_parent_dir="/path/to/registry"
)

# task_id だけで実行
agent = dslighting.Agent()
result = agent.run(task_id="my-custom-task")
```

**利点**:
- 🔧 **集中管理**: 複数タスクを一括管理
- 📊 **バッチ処理**: 多数の競合タスクに対応
- ⚡ **効率向上**: 設定の繰り返しを削減

#### Option 4: カスタム Agent の定義（エキスパート）

**Operator / Workflow / Factory を定義して完全カスタム**

**例: カスタム Agent を構築**

```python
from dslighting.operators.custom import SimpleOperator

# 1. Operator 定義（再利用可能な能力）
async def summarize(text: str) -> dict:
    return {"summary": text[:200]}

summarize_op = SimpleOperator(func=summarize, name="Summarize")

# 2. Workflow 定義（Operator を連結）
class MyWorkflow:
    def __init__(self, operators):
        self.ops = operators

    async def solve(self, description, io_instructions, data_dir, output_path):
        _ = await self.ops["summarize"](text=description)

# 3. Factory 定義（Workflow を構築）
class MyWorkflowFactory:
    def __init__(self, model="openai/gpt-4o"):
        self.model = model

    def create_agent(self):
        operators = {"summarize": summarize_op}
        return MyWorkflow(operators)

# 4. カスタム Agent を使用
agent = MyWorkflowFactory(model="openai/deepseek-ai/DeepSeek-V3.1-Terminus").create_agent()
```

**主要概念**:
- **Operator**: 再利用可能な原子能力（分析・モデリング・可視化）
- **Workflow**: Operator を連結してタスクを解く
- **Factory**: Agent を構築・設定

**利用シーン**:
- 🎯 特定タスクの実行ロジックが必要
- 🔬 新しい Agent アーキテクチャの研究
- 🧩 複数能力の組み合わせ
- 📈 特定領域の最適化

**ベストプラクティス**:
- ✅ 出力を柔軟に（レポート、図、モデル）
- ✅ サンドボックス実行で安全確保
- ✅ 小さく再利用可能な Operator を優先

📖 **詳細チュートリアル**: [AdvancedDSAgent examples](https://github.com/usail-hkust/dslighting/tree/main/examples/advanced_custom_agent)

---

## 🚀 Quick Start

### システム要件

- **Python**: 3.10 以上
  ```bash
  # Python バージョン確認
  python --version
  # または
  python3 --version
  ```
- **Node.js**: 18.x 以上
  ```bash
  # Node.js バージョン確認
  node --version
  ```
- **npm**: 9.x 以上（Node.js に同梱）
  ```bash
  # npm バージョン確認
  npm --version
  ```
- **Git**: 版管理用

### 1. 環境準備

```bash
git clone https://github.com/usail-hkust/dslighting.git
cd dslighting
python3.10 -m venv dslighting
source dslighting/bin/activate  # Windows: dslighting\Scripts\activate
```

### 2. 依存関係のインストール

**標準インストール**（推奨）:
```bash
pip install -r requirements.txt
```

**代替オプション**（標準が失敗する場合）:
```bash
pip install -r requirements_local.txt
```

> 💡 **注記**:
> - `requirements.txt`: 固定バージョン（本番向け）
> - `requirements_local.txt`: 非固定で柔軟（開発向け）

### 3. API キーの設定

```bash
cp .env.example .env
# .env を編集して API キーを設定
```

DSLighting は複数の LLM プロバイダに対応:

**中国向けプロバイダ**（中国ユーザーに推奨）:
- **Zhipu AI** (https://bigmodel.cn/) - GLM シリーズ
  - API Base: `https://open.bigmodel.cn/api/paas/v4`
  - キー取得: https://open.bigmodel.cn/usercenter/apikeys
- **SiliconFlow** (https://siliconflow.cn/) - DeepSeek, Qwen など
  - API Base: `https://api.siliconflow.cn/v1`
  - キー取得: https://siliconflow.cn/account/ak

**国際プロバイダ**:
- **OpenAI** (https://openai.com/) - GPT シリーズ
  - API Base: `https://api.openai.com/v1`
  - キー取得: https://platform.openai.com/api-keys

`API_KEY` / `API_BASE` か、`LLM_MODEL_CONFIGS` でモデルごとの設定が可能です。

> 💡 **設定例**: `.env.example` に複数モデルの設定例、キーのローテーション、温度設定が含まれています。

### 4. データ準備

DSLighting は複数のデータソースに対応しています。以下のいずれかを選択:

#### 方法 1: MLE-Bench からダウンロード（推奨）

[MLE-Bench](https://github.com/openai/mle-bench) は OpenAI 提供の機械学習評価ベンチマークです。

```bash
# 1. MLE-Bench をクローン
git clone https://github.com/openai/mle-bench.git
cd mle-bench

# 2. 依存関係のインストール
pip install -e .

# 3. 全データセットをダウンロード
python scripts/prepare.py --competition all

# 4. DSLighting にリンク
# MLE-Bench データは ~/mle-bench/data/ に保存
ln -s ~/mle-bench/data/competitions /path/to/dslighting/data/competitions
```

> 📖 **詳細**: [MLE-Bench GitHub](https://github.com/openai/mle-bench)

#### 方法 2: カスタムデータセット

DSLighting のデータレイアウトに従って配置します:

```
data/competitions/
  <competition-id>/
    config.yaml           # 競技設定
    prepared/
      public/            # 公開データ
      private/           # 非公開データ
```

> 💡 **注記**: より多くのデータタイプや事前学習モデルを順次対応予定です。

> 📖 **データ準備ガイド**: [DATA_PREPARATION.md](DATA_PREPARATION.md)

### 5. タスク実行

```bash
python run_benchmark.py \
  --workflow aide \
  --benchmark mle \
  --data-dir data/competitions \
  --task-id bike-sharing-demand \
  --llm-model gpt-4
```

### 6. Web UI（推奨）

Next.js + FastAPI の Web インターフェースを提供しています。

#### 6.1 バックエンド設定

```bash
source dslighting/bin/activate
# バックエンド依存の追加
pip install -r web_ui/backend/requirements.txt
```

#### 6.2 バックエンド起動

```bash
cd web_ui/backend
python main.py
```

または uvicorn:

```bash
cd web_ui/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

> 📖 **詳細**: [Backend README](../../web_ui/backend/README.md)

> 💡 **ヒント**: デフォルトはポート **8003**。使用中の場合は `main.py` を変更してください。

#### 6.3 フロントエンド起動

```bash
cd web_ui/frontend
npm install
npm run dev
```

> 📖 **詳細**: [Frontend README](../../web_ui/frontend/README.md)

#### 6.4 ダッシュボードへのアクセス

ブラウザで [http://localhost:3000](http://localhost:3000) を開きます。

---

## 🏗️ Core Features

### Agent ワークフロー

- **`aide`**: 反復的なコード生成とレビュー
- **`automind`**: 記憶・分解を含む計画+推論
- **`dsagent`**: 構造化オペレータによる計画/実行
- **`data_interpreter`**: 迅速な実行とデバッグ
- **`autokaggle`**: SOP 形式の Kaggle ワークフロー
- **`aflow`**: ワークフローのメタ最適化
- **`deepanalyze`**: 分析特化の実行フロー

### データレイアウト

```
data/competitions/
  <competition-id>/
    config.yaml           # 競技設定
    prepared/
      public/            # 公開データ
      private/           # 非公開データ
```

### 設定

`config.yaml` はベンチマーク実行と LLM サービスで読み込まれます:

- `competitions`: MLEBench のデフォルト競技リスト
- `sciencebench_competitions`（任意）: ScienceBench のデフォルトリスト
- `custom_model_pricing`: LiteLLM のモデル単価上書き
- `run`: トレースログの切り替え

### カスタムモデル価格

**デフォルト動作**:
- DSLighting は LiteLLM のデフォルト価格を利用
- `config.yaml` がなくても正常動作（エラーなし）
- 価格設定は任意で、上書きが必要な場合のみ

**カスタム価格**:

特定モデルの価格を設定するには、プロジェクト直下に `config.yaml` を作成します:

**配置例**:
```bash
# pip インストールの場合
/path/to/your/project/config.yaml

# テストプロジェクト例
/Users/liufan/Applications/Github/dslighting_test_project/config.yaml
```

> 📖 **参考**: [config.yaml.example](../config.yaml.example)

**例**:
```yaml
custom_model_pricing:
  openai/Qwen/Qwen3-Coder-480B-A35B-Instruct:
    input_cost_per_token: 6.0e-07
    output_cost_per_token: 1.8e-06
  openai/Qwen/Qwen3-Coder-30B-A3B-Instruct:
    input_cost_per_token: 6.0e-07
    output_cost_per_token: 1.8e-06
  o4-mini-2025-04-16:
    input_cost_per_token: 1.1e-06
    output_cost_per_token: 4.4e-06
  openai/deepseek-ai/DeepSeek-V3.1-Terminus:
    input_cost_per_token: 5.55e-07
    output_cost_per_token: 1.67e-06
```

**パラメータ**:
- `input_cost_per_token`: 入力トークン価格（リクエスト単位）
- `output_cost_per_token`: 出力トークン価格（レスポンス単位）
- 単位: USD/token（科学表記が一般的）

**注記**:
- 💡 価格設定は任意（未設定でもエラーなし）
- 💡 必要なモデルのみ上書き
- 💡 コスト計算と予算管理に影響

---

## 📂 ログと成果物

デフォルトのログ出力先:

```
runs/benchmark_results/<workflow>_on_<benchmark>/<model_name>/
```

`--log-path` でベースディレクトリを変更できます。

---

## ❓ FAQ

詳細は `FAQ.md` を参照してください。

---

## ⭐ Star History

<div align="center">

<p>
  <a href="https://github.com/usail-hkust/dslighting/stargazers"><img src="../assets/roster/stargazers.svg" alt="Stargazers"/></a>
  &nbsp;&nbsp;
  <a href="https://github.com/usail-hkust/dslighting/network/members"><img src="../assets/roster/forkers.svg" alt="Forkers"/></a>
</p>

<a href="https://www.star-history.com/#usail-hkust/dslighting&type=timeline&legend=top-left">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=usail-hkust/dslighting&type=timeline&theme=dark&legend=top-left" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=usail-hkust/dslighting&type=timeline&legend=top-left" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=usail-hkust/dslighting&type=timeline&legend=top-left" />
  </picture>
</a>

</div>

---

## 💬 WeChat コミュニティ

WeChat グループに参加して、他のユーザーや開発者と交流しましょう！

<div align="center">

<img src="../assets/wechat_group.jpg" alt="WeChat Group" width="300" style="border-radius: 10px; border: 2px solid #e0e0e0;">

**上記の QR コードをスキャンして参加**

</div>

グループでは以下が可能です:
- 🤝 使い方の共有と交流
- 💡 機能提案とフィードバック
- 🐛 バグ報告とサポート
- 📢 最新情報の受け取り

---

## 🤝 コントリビュート

<div align="center">

DSLIGHTING をコミュニティへの贈り物にしたいと考えています。 🎁

<a href="https://github.com/usail-hkust/dslighting/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=usail-hkust/dslighting" />
</a>

**主要コントリビューター**:
- [luckyfan-cs](https://github.com/luckyfan-cs)（プロジェクトリード、フロントエンド&バックエンド）
- [canchengliu](https://github.com/canchengliu)（ワークフロー貢献）

`CONTRIBUTING.md` を参照してください。

</div>

---

## 🔗 コミュニティ

<div align="center">

**[DSLIGHTING Community](https://github.com/luckyfan-cs)**

[💬 WeChat Group](#-wechat-コミュニティ) · [⭐ Star](https://github.com/usail-hkust/dslighting/stargazers) · [🐛 Issue](https://github.com/usail-hkust/dslighting/issues) · [💬 Discussions](https://github.com/usail-hkust/dslighting/discussions)

</div>

---

## 📄 ライセンス

本プロジェクトは AGPL-3.0 ライセンスで提供されます。

---

## 🙏 謝辞

DSLIGHTING に関心をお寄せいただきありがとうございます！

---

## 📊 プロジェクト統計

![](https://komarev.com/ghpvc/?username=usail-hkust&repo=dslighting&style=for-the-badge)
![](https://img.shields.io/github/issues/usail-hkust/dslighting?style=for-the-badge)
![](https://img.shields.io/github/forks/usail-hkust/dslighting?style=for-the-badge)
![](https://img.shields.io/github/stars/usail-hkust/dslighting?style=for-the-badge)

---

## 📚 Citation

研究で DSLIGHTING を利用する場合は、以下を引用してください:

```bibtex
@software{dslighting2025,
  title = {DSLIGHTING: An End-to-End Data Science Intelligent Assistant System},
  author = {Liu, F. and Liu, C. and others},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/usail-hkust/dslighting},
  version = {1.0.0}
}
```

またはプレーンテキスト:

```
Liu, F., Liu, C., et al. (2025). DSLIGHTING: An End-to-End Data Science Intelligent Assistant System.
GitHub repository. https://github.com/usail-hkust/dslighting
```

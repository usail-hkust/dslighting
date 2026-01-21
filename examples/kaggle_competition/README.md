# DSLighting + Kaggle 快速开始

使用 DSLighting 快速参加 Kaggle 比赛！

## 3 步开始

### 1. 配置 Kaggle API

```bash
pip install dslighting kaggle
```

**方式 1：环境变量（推荐 ⭐）**
```bash
# 访问 https://www.kaggle.com/ → Account → API → Create New API Token
# 复制 Token（格式：KGAT_xxx）

export KAGGLE_API_TOKEN=你的Token

# 永久保存
echo 'export KAGGLE_API_TOKEN=你的Token' >> ~/.zshrc
source ~/.zshrc
```

**方式 2：配置文件**
```bash
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

✅ 验证：`kaggle competitions list`

### 2. 创建项目（一条命令）

```bash
python kaggle_auto_setup.py --competition titanic
```

自动完成：
- 下载比赛数据
- 分割训练集（80% 训练 + 20% 验证）
- 生成 test_answer.csv
- 生成配置文件

### 3. 配置环境变量

在项目目录创建 `.env` 文件：

```bash
cd titanic
cat > .env << EOF
# API 配置
API_KEY=your-api-key-here
API_BASE=https://api.openai.com/v1
LLM_MODEL=openai/gpt-4
EOF
```

### 4. 运行

```bash
python run.py
```

## 常见用法

```bash
# 指定目录
python kaggle_auto_setup.py --competition titanic --dir ./my-project

# 查看帮助
python kaggle_auto_setup.py --help
```

## 获取 competition-id

从 Kaggle URL: `https://www.kaggle.com/c/[competition-id]`

例如：`https://www.kaggle.com/c/titanic` → `titanic`

## 任何比赛都可以！

支持所有 Kaggle 比赛，自动识别数据格式和评估指标。

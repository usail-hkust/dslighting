# DSLighting 环境配置完整指南

本文档提供详细的步骤说明，帮助您从头开始配置DSLighting的开发环境。

## 目录

1. [系统要求](#系统要求)
2. [Python环境配置](#python环境配置)
3. [主项目依赖安装](#主项目依赖安装)
4. [Web UI后端配置](#web-ui后端配置)
5. [Web UI前端配置](#web-ui前端配置)
6. [启动服务](#启动服务)
7. [验证安装](#验证安装)
8. [常见问题](#常见问题)

---

## 系统要求

### 必需软件

- **Python**: 3.10 或更高版本
  ```bash
  # 检查Python版本
  python --version
  # 或
  python3 --version

  # 如果版本低于3.10，请安装Python 3.10+
  # macOS: brew install python@3.10
  # Ubuntu: sudo apt-get install python3.10
  # Windows: 从 https://www.python.org/downloads/ 下载安装
  ```
- **Node.js**: 18.x 或更高版本
  ```bash
  # 检查Node.js版本
  node --version
  ```
- **npm**: 9.x 或更高版本（随Node.js一起安装）
  ```bash
  # 检查npm版本
  npm --version
  ```
- **Git**: 用于版本控制
  ```bash
  # 检查Git版本
  git --version
  ```

### 推荐软件

- **VS Code**: 推荐的IDE
- **Postman**: API测试工具

---

## Python环境配置

### 1. 创建虚拟环境

```bash
# 克隆项目
git clone https://github.com/luckyfan-cs/dslighting.git
cd dslighting

# 创建Python虚拟环境（使用Python 3.10）
python3.10 -m venv dslighting

# 激活虚拟环境
# macOS/Linux:
source dslighting/bin/activate

# Windows:
dslighting\Scripts\activate
```

**验证虚拟环境已激活**：
```bash
which python  # 应显示: 项目根目录/dslighting/bin/python
```

---

## 数据准备

DSLighting支持多种数据来源。选择以下任一方式准备数据：

### 方式1：通过MLE-Bench下载（推荐）

[MLE-Bench](https://github.com/openai/mle-bench)是OpenAI提供的机器学习评估基准数据集，包含多个Kaggle风格的竞赛任务。

**完整步骤**：

```bash
# 1. 进入项目根目录
cd /path/to/dslighting

# 2. 激活虚拟环境
source dslighting/bin/activate

# 3. 克隆MLE-Bench仓库（与dslighting同级目录）
cd ..
git clone https://github.com/openai/mle-bench.git
cd mle-bench

# 4. 安装MLE-Bench依赖
pip install -e .

# 5. 下载所有数据集
python scripts/prepare.py --competition all

# 数据将被下载到 ~/mle-bench/data/competitions/
```

**数据链接到DSLighting**：

```bash
# 方案A：创建符号链接（推荐，节省空间）
cd /path/to/dslighting/data
ln -s ~/mle-bench/data/competitions competitions

# 方案B：复制数据（占用更多空间）
# cp -r ~/mle-bench/data/competitions /path/to/dslighting/data/
```

**验证数据**：

```bash
# 检查数据目录
ls /path/to/dslighting/data/competitions/
# 应该看到：bike-sharing-demand/, titanic/, 等竞赛目录

# 检查单个竞赛的数据结构
ls /path/to/dslighting/data/competitions/bike-sharing-demand/prepared/
# 应该看到：public/, private/
```

> 📖 **详细信息**: 访问 [MLE-Bench GitHub](https://github.com/openai/mle-bench) 查看完整数据集列表和说明。

### 方式2：自定义数据集

如果您有自己的数据集，按照以下结构组织：

```
data/competitions/
  <your-competition-id>/
    config.yaml           # 竞赛配置（必需）
    description.md        # 任务描述（可选）
    prepared/
      public/            # 训练数据
        train.csv
        sample_submission.csv
        test.csv
      private/           # 评分数据
        answer.csv
```

**config.yaml示例**：

```yaml
id: your-competition-id
name: Your Competition Name
competition_type: kaggle
grader:
  name: accuracy  # 或 rmse, f1 等
  grade_fn: path.to.grade:grade
preparer: path.to.prepare:prepare
```

### 方式3：Web UI上传（便捷）

使用Web UI界面上传数据（推荐用于快速测试）：

1. 启动后端和前端（见下方"启动服务"章节）
2. 访问 http://localhost:3000
3. 在界面上传数据集文件
4. 系统自动处理并组织数据

### 数据类型说明

当前支持：
- ✅ **Kaggle风格竞赛**: 通过MLE-Bench提供的数据集
- ✅ **自定义数据集**: 按照DSLighting格式组织的CSV/JSON数据
- ✅ **Web UI上传**: 支持拖拽上传和在线预览

即将支持：
- 🔜 **更多预训练模型权重**
- 🔜 **多模态数据集（图像、文本、语音）**
- 🔜 **时序数据和强化学习任务**
- 🔜 **企业级私有数据集集成**

> 💡 **提示**: 更多数据类型和预训练模型支持正在陆续开放中，敬请期待！

> 📖 **详细指南**: 查看 [数据准备文档](docs/DATA_PREPARATION.md) 了解更多数据格式和自定义方法。

---

## 主项目依赖安装

### 方案A：标准安装（推荐）

```bash
pip install -r requirements.txt
```

### 方案B：本地版本（如果方案A失败）

```bash
pip install -r requirements_local.txt
```

### 验证安装

```bash
python -c "import fastapi; import torch; print('✅ 核心依赖安装成功')"
```

---

## Web UI后端配置

### 1. 安装后端依赖

**完整命令流程**：

```bash
# 1. 确认在项目根目录
cd /path/to/dslighting

# 2. 激活虚拟环境
source dslighting/bin/activate  # macOS/Linux
# dslighting\Scripts\activate     # Windows

# 3. 验证虚拟环境已激活
which python  # 应显示: 项目根目录/dslighting/bin/python

# 4. 安装后端依赖
pip install -r web_ui/backend/requirements.txt
```

### 2. 配置环境变量

**完整命令流程**：

```bash
# 1. 确认在项目根目录
cd /path/to/dslighting

# 2. 激活虚拟环境（如果还没激活）
source dslighting/bin/activate

# 3. 复制环境变量模板
cp .env.example .env

# 4. 编辑.env文件
nano .env  # 或使用你喜欢的编辑器
```

**在.env文件中设置**：

DSLighting支持多种LLM提供商，您可以根据需求选择：

#### 方式1：基础配置（单个模型）

```bash
# LLM配置（必需）
API_KEY=your_api_key_here
API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7
```

#### 方式2：多模型配置（推荐）

使用 `LLM_MODEL_CONFIGS` 可以配置多个模型，系统会根据 `--llm-model` 参数自动选择对应的配置。

**支持的提供商**：

1. **智谱AI**（国内推荐 - https://bigmodel.cn/）
   ```bash
   LLM_MODEL_CONFIGS='{
     "glm-4.7": {
       "provider": "openai",
       "api_key": "your-zhipu-api-key",
       "api_base": "https://open.bigmodel.cn/api/paas/v4",
       "temperature": 1.0
     }
   }'
   ```

2. **硅基流动**（国内推荐 - https://siliconflow.cn/）
   ```bash
   LLM_MODEL_CONFIGS='{
     "openai/deepseek-ai/DeepSeek-V3.1-Terminus": {
       "api_key": [
         "sk-siliconflow-key-1",
         "sk-siliconflow-key-2"
       ],
       "api_base": "https://api.siliconflow.cn/v1",
       "temperature": 1.0
     }
   }'
   ```

3. **OpenAI**（国际 - https://openai.com/）
   ```bash
   LLM_MODEL_CONFIGS='{
     "gpt-4o": {
       "api_key": "sk-openai-key",
       "api_base": "https://api.openai.com/v1",
       "temperature": 0.7
     }
   }'
   ```

**⚠️ 重要说明**：

- **配置格式1**（使用provider字段）：
  ```json
  "model-name": {
    "provider": "openai",
    "api_key": "...",
    "api_base": "..."
  }
  ```

- **配置格式2**（使用openai/前缀）：
  ```json
  "openai/model-name": {
    "api_key": "...",
    "api_base": "..."
  }
  ```
  **注意**: 使用格式2时，不要添加 `provider` 字段！

- 两种格式不能混用，否则会冲突！

**获取API密钥**：
- 智谱AI: https://open.bigmodel.cn/usercenter/apikeys
- 硅基流动: https://siliconflow.cn/account/ak
- OpenAI: https://platform.openai.com/api-keys

**其他配置**（可选）：

```bash
# 数据目录（可选，已有默认值）
DATA_DIR=data/competitions
LOGS_DIR=runs
```

### 3. 验证后端配置

```bash
# 确认虚拟环境已激活
source dslighting/bin/activate

# 测试导入（从项目根目录）
python -c "from web_ui.backend.app.main import app; print('✅ 后端配置成功')"
```

---

## Web UI前端配置

### 1. 进入前端目录

```bash
cd web_ui/frontend
```

### 2. 安装NPM依赖

```bash
npm install
```

**可能遇到的问题**：

如果安装失败，尝试：
```bash
# 清理缓存
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### 3. 配置API地址

编辑 `config/api.ts`，确认后端地址：

```typescript
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

如果后端使用其他端口，修改为对应地址。

### 4. 验证前端配置

```bash
# 启动开发服务器（不阻塞）
npm run dev &

# 等待几秒后测试
curl http://localhost:3000
# 应该返回HTML内容
```

---

## 启动服务

### 终端1：启动后端

```bash
# 1. 进入项目根目录
cd /path/to/dslighting

# 2. 激活虚拟环境（如果还没激活）
source dslighting/bin/activate  # macOS/Linux
# dslighting\Scripts\activate     # Windows

# 3. 进入后端目录
cd web_ui/backend

# 4. 启动后端（默认端口8003）
python main.py
```

**成功标志**：
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8003
```

### 终端2：启动前端

```bash
# 1. 打开新终端，进入项目根目录
cd /path/to/dslighting

# 2. 激活虚拟环境（可选，前端不需要）
# source dslighting/bin/activate

# 3. 进入前端目录
cd web_ui/frontend

# 4. 启动前端
npm run dev
```

**成功标志**：
```
✓ Ready in 512ms
○ Local:        http://localhost:3000
```

---

## 验证安装

### 1. 检查后端API

访问：http://localhost:8003/docs

应该看到FastAPI自动生成的API文档页面。

### 2. 检查前端界面

访问：http://localhost:3000

应该看到DSLighting的Dashboard界面。

### 3. 测试API连接

在前端界面中：
1. 检查浏览器控制台（F12）
2. 查看是否有连接错误
3. 检查Network标签，确认API请求成功

---

## 常见问题

### Q0: Python版本不满足要求

**错误信息**：
```
SyntaxError: Python 3.10+ is required
```

**检查Python版本**：
```bash
python --version
# 或
python3 --version
```

**解决方案**：

如果版本低于3.10，需要安装Python 3.10或更高版本：

**macOS**：
```bash
# 使用Homebrew安装
brew install python@3.10

# 验证安装
python3.10 --version
```

**Ubuntu/Debian**：
```bash
# 添加deadsnakes PPA
sudo apt-get update
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update

# 安装Python 3.10
sudo apt-get install python3.10 python3.10-venv python3.10-dev

# 验证安装
python3.10 --version
```

**Windows**：
1. 访问 https://www.python.org/downloads/
2. 下载Python 3.10或更高版本的安装包
3. 运行安装程序，勾选"Add Python to PATH"
4. 验证安装：打开命令提示符，运行 `python --version`

**使用特定Python版本创建虚拟环境**：
```bash
# 使用python3.10创建虚拟环境
python3.10 -m venv dslighting

# 激活虚拟环境
source dslighting/bin/activate  # macOS/Linux
# dslighting\Scripts\activate   # Windows

# 验证虚拟环境的Python版本
python --version  # 应该显示3.10.x
```

### Q1: 端口被占用错误

**错误信息**：
```
Error: [Errno 48] Address already in use
```

**解决方案**：
```bash
# 查找占用端口的进程
lsof -i :8003  # macOS/Linux
netstat -ano | findstr :8003  # Windows

# 杀死进程
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# 或修改main.py中的端口号
```

### Q2: 模块导入错误

**错误信息**：
```
ModuleNotFoundError: No module named 'xxx'
```

**解决方案**：
```bash
# 确认虚拟环境已激活
source dslighting/bin/activate
which python

# 重新安装依赖
pip install -r requirements.txt

# 或使用本地版本
pip install -r requirements_local.txt
```

### Q3: 前端构建失败

**错误信息**：
```
Failed to compile
```

**解决方案**：
```bash
# 清理并重新安装
rm -rf .next node_modules package-lock.json
npm cache clean --force
npm install
npm run dev
```

### Q4: CORS错误

**错误信息**：
```
Access to XMLHttpRequest blocked by CORS policy
```

**解决方案**：
确认后端CORS配置正确（已在`app/main.py`中配置）。

### Q5: API密钥错误

**错误信息**：
```
401 Unauthorized
```

**解决方案**：
```bash
# 检查.env文件
cat .env

# 确认API_KEY和API_BASE正确设置
```

---

## 开发工作流

### 日常启动流程

1. **启动后端**（终端1）：
   ```bash
   cd /path/to/dslighting
   source dslighting/bin/activate  # 如果还没激活
   cd web_ui/backend
   python main.py
   ```

2. **启动前端**（终端2）：
   ```bash
   cd /path/to/dslighting/web_ui/frontend
   npm run dev
   ```

3. **访问Dashboard**：
   - 打开浏览器访问 http://localhost:3000
   - 后端API运行在 http://localhost:8003

### 代码修改

- **后端修改**：保存后自动重载
- **前端修改**：保存后自动热更新

---

## 性能优化建议

### 后端

1. 使用Gunicorn生产服务器（多worker）
2. 启用响应压缩
3. 实施请求缓存

### 前端

1. 使用生产构建（`npm run build`）
2. 启用CDN加速
3. 优化图片和静态资源

---

## 安全建议

1. **不要提交.env文件**到版本控制
2. **生产环境**使用HTTPS
3. **限制CORS来源**
4. **实施速率限制**
5. **定期更新依赖**

---

## 下一步

环境配置完成后，您可以：

1. 阅读 [主README](../README.md) 了解项目功能
2. 查看 [前端README](web_ui/frontend/README.md) 学习前端开发
3. 查看 [后端README](web_ui/backend/README.md) 学习API开发
4. 查看 [FAQ文档](docs/FAQ.md) 解决常见问题

---

## 获取帮助

如果遇到问题：

1. 查看日志文件：`runs/` 目录
2. 检查GitHub Issues：https://github.com/luckyfan-cs/dslighting/issues
3. 提交新的Issue并附上错误日志

祝您使用愉快！🎉

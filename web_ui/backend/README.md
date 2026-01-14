# DSLighting Backend

基于 FastAPI 的后端服务，提供数据上传、任务执行和Agent交互功能。

## 技术栈

- **FastAPI 0.109** - 现代Web框架
- **Uvicorn** - ASGI服务器
- **Python 3.10+** - 编程语言
- **Pydantic** - 数据验证

## 系统要求

- **Python**: 3.10 或更高版本
  ```bash
  # 检查Python版本
  python --version
  # 或
  python3 --version
  ```
- **Node.js**: 18.x 或更高版本（用于前端开发）
- **npm**: 9.x 或更高版本

## 环境要求

后端依赖主项目dslighting环境，需要先安装主项目依赖。

### 步骤1：安装主项目依赖

**从项目根目录执行**：

```bash
# 1. 进入项目根目录
cd /path/to/dslighting

# 2. 激活Python虚拟环境（如果还没激活）
source dsat/bin/activate

# 3. 安装主项目依赖（选择一种方式）
# 方式A：标准安装（推荐）
pip install -r requirements.txt

# 方式B：本地版本（如果方式A失败）
pip install -r requirements_local.txt
```

### 步骤2：安装后端依赖

**从项目根目录执行**：

```bash
# 确认在项目根目录
pwd  # 应该显示项目根目录路径

# 确认虚拟环境已激活
which python  # 应该显示: .../dsat/bin/python

# 安装后端依赖
pip install -r web_ui/backend/requirements.txt
```

### 步骤3：验证安装

```bash
# 测试导入
python -c "from app.main import app; print('✅ 后端配置成功')"
```

## 启动服务

### 方式一：使用main.py启动（推荐）

**完整命令流程**：

```bash
# 1. 确认在项目根目录
cd /path/to/dslighting

# 2. 激活虚拟环境（如果还没激活）
source dslighting/bin/activate

# 3. 进入后端目录
cd web_ui/backend

# 4. 启动后端服务
python main.py
```

这会启动在默认端口 **8003**，并启用自动重载。

### 方式二：使用uvicorn直接启动

```bash
# 完整命令流程
cd /path/to/dslighting
source dslighting/bin/activate
cd web_ui/backend

# 使用uvicorn启动（默认端口8003）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8003

# 或使用其他端口（例如8001）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 生产模式

```bash
cd /path/to/dslighting
source dslighting/bin/activate
cd web_ui/backend

uvicorn app.main:app --host 0.0.0.0 --port 8003 --workers 4
```

### 修改端口

编辑 `web_ui/backend/main.py` 文件：

```bash
# 从项目根目录
cd /path/to/dslighting/web_ui/backend

# 编辑main.py
nano main.py  # 或使用你喜欢的编辑器
```

修改端口号：

```python
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=YOUR_PORT, reload=True)
```

## 项目结构

```
backend/
├── app/
│   ├── main.py           # FastAPI应用入口
│   ├── core/             # 核心配置
│   │   ├── config.py     # 配置设置
│   │   └── utils.py      # 工具函数
│   ├── models/           # 数据模型
│   │   └── schemas.py    # Pydantic模型
│   ├── services/         # 业务逻辑
│   │   ├── chat_service.py      # 聊天服务
│   │   ├── llm_factory.py       # LLM工厂
│   │   ├── task_service.py      # 任务服务
│   │   └── data_analyzer.py     # 数据分析
│   └── routes/           # API路由（如有）
└── requirements.txt      # 后端依赖
```

## API端点

### 任务管理
- `POST /tasks/{task_id}/upload` - 上传数据集
- `GET /tasks/{task_id}` - 获取任务信息
- `GET /tasks` - 获取所有任务

### 聊天交互
- `POST /tasks/{task_id}/chat` - 发送聊天消息
- `GET /tasks/{task_id}/chat_status` - 获取聊天状态

### 工作流
- `POST /run` - 启动工作流
- `POST /tasks/{task_id}/stop` - 停止任务

### 报告
- `GET /tasks/{task_id}/report` - 获取报告
- `POST /tasks/{task_id}/report/update` - 更新报告

### 代码历史
- `GET /tasks/{task_id}/code-history` - 获取代码历史
- `GET /tasks/{task_id}/code-history/file/{filename}` - 获取特定文件

## 配置说明

### 环境变量

创建 `.env` 文件：

```bash
# LLM配置
API_KEY=your_api_key_here
API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4

# 数据目录
DATA_DIR=data/competitions
LOGS_DIR=runs
```

### CORS配置

默认允许所有来源访问，生产环境建议限制：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 限制前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 日志

日志输出到：
- 控制台（开发模式）
- `runs/` 目录（任务运行日志）

## 常见问题

### Q: 后端无法连接前端？
A: 检查CORS配置和前端API_URL设置

### Q: 任务执行失败？
A: 查看 `runs/` 目录中的日志文件

### Q: 如何调试API？
A: 访问 http://localhost:8003/docs 查看自动生成的API文档

## 性能优化

- 使用异步IO (`async/await`)
- 启用后台任务处理长时间运行的操作
- 合理配置worker数量

## 安全建议

1. 生产环境使用HTTPS
2. 配置API密钥管理
3. 限制CORS来源
4. 实施速率限制
5. 验证用户输入

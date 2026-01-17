# DSLighting PyPI 文档

本目录包含 DSLighting PyPI 包的所有官方文档。

## 📚 文档目录

### 核心文档
- **README_PIP.md** - PyPI 主页文档（项目介绍、快速上手、API 使用）
- **QUICK_GUIDE.md** - 快速上手指南（4 种使用方式）
- **API_GUIDE.md** - 完整 API 使用指南
- **DATA_TASK_MODULE.md** - 数据与任务模块详解

### 发布说明
- **RELEASE_NOTES_v1.8.2.md** - v1.8.2 发布说明
- **RELEASE_NOTES_v1.8.1.md** - v1.8.1 发布说明
- **RELEASE_NOTES_v1.8.0.md** - v1.8.0 发布说明

## 🚀 快速开始

### 安装

```bash
pip install dslighting python-dotenv
```

### 基本使用

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

# 方式1：全局配置（推荐）
dslighting.setup(
    data_parent_dir="/path/to/data/competitions",
    registry_parent_dir="/path/to/registry"
)
agent = dslighting.Agent()
result = agent.run(task_id="bike-sharing-demand")

# 方式2：直接路径
result = agent.run(
    task_id="bike-sharing-demand",
    data_dir="/path/to/data/competitions/bike-sharing-demand",
    registry_dir="/path/to/registry/bike-sharing-demand"
)

# 方式3：内置数据集
result = dslighting.run_agent(task_id="bike-sharing-demand")

# 方式4：先加载数据
data = dslighting.load_data(
    "/path/to/data/competitions/bike-sharing-demand",
    registry_dir="/path/to/registry/bike-sharing-demand"
)
result = agent.run(data)
```

## 📖 更多信息

- **完整文档**: https://luckyfan-cs.github.io/dslighting-web/api/getting-started.html
- **GitHub**: https://github.com/usail-hkust/dslighting
- **PyPI**: https://pypi.org/project/dslighting/

---

**版本**: 1.8.2
**最后更新**: 2026-01-17

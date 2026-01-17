# DSLighting v1.8.2 发布说明

## 📝 更新内容

### PyPI 主页更新
- 更新 PyPI 项目主页，使用优化的 README_PIP.md
- 添加完整的使用文档和示例
- 添加数据系统文档链接
- 优化项目描述和特性说明

### 内置数据修复
- 包含 v1.8.1 的修复：`bike-sharing-demand` 数据集的 `sampleSubmission.csv` 修复

---

## 📦 安装

```bash
pip install --upgrade dslighting==1.8.2
```

---

## 🔗 链接

- **PyPI**: https://pypi.org/project/dslighting/1.8.2/
- **完整文档**: https://luckyfan-cs.github.io/dslighting-web/api/getting-started.html
- **GitHub**: https://github.com/usail-hkust/dslighting

---

## ✨ 主要特性

### 1. 统一的 API 设计

DSLighting 提供了 **4 种清晰的使用方式**，满足不同场景需求：

**方式 1：全局配置（推荐用于多任务项目）**
```python
import dslighting

# 配置一次，全局生效
dslighting.setup(
    data_parent_dir="/path/to/data/competitions",
    registry_parent_dir="/path/to/registry"
)

# 运行任务（只需 task_id）
agent = dslighting.Agent()
result = agent.run(task_id="bike-sharing-demand")
```

**方式 2：直接路径（明确清晰）**
```python
import dslighting

agent = dslighting.Agent()
result = agent.run(
    task_id="bike-sharing-demand",
    data_dir="/path/to/data/competitions/bike-sharing-demand",
    registry_dir="/path/to/registry/bike-sharing-demand"
)
```

**方式 3：内置数据集（最简单）**
```python
import dslighting

# 无需配置，直接使用
result = dslighting.run_agent(task_id="bike-sharing-demand")
```

**方式 4：先加载数据（灵活检查）**
```python
import dslighting

# 先加载数据并检查
data = dslighting.load_data(
    "/path/to/data/competitions/bike-sharing-demand",
    registry_dir="/path/to/registry/bike-sharing-demand"
)

# 检查数据结构
print(data.show())

# 确认无误后运行
agent = dslighting.Agent()
result = agent.run(data)
```

### 2. 数据系统

DSLighting 提供统一的数据管理系统：

- **LoadedData**：核心数据容器，封装数据集和任务配置
- **TaskDetection**：自动识别任务类型（kaggle, open_ended, datasci）
- **Registry**：管理任务配置和评分规则

### 3. 灵活的模型配置

支持多种 LLM 模型：
- OpenAI (GPT-4, GPT-3.5)
- 智谱 AI (GLM-4)
- SiliconFlow (DeepSeek, Qwen, Kimi 等)
- 任何兼容 OpenAI API 的服务

---

## 📚 文档

详细文档请访问：
- **[快速上手指南](https://luckyfan-cs.github.io/dslighting-web/api/getting-started.html)**
- **[数据系统文档](https://luckyfan-cs.github.io/dslighting-web/api/data-system.html)**

---

## 🎉 总结

DSLighting v1.8.2 是一个持续改进版本，提供了：
- ✅ 更新的 PyPI 主页和文档
- ✅ 完整的使用示例和最佳实践
- ✅ 清晰的 API 设计（4 种使用方式）
- ✅ 修复的数据集问题

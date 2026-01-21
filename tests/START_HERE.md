# DSLighting 2.0 文档导航

## 🎯 快速找到你需要的文档

### 📍 你是谁？

---

## 👶 我是新手 - 我想快速上手

### 推荐阅读顺序：

1. **[5_MINUTE_QUICKSTART.md](5_MINUTE_QUICKSTART.md)** ⭐ **从这里开始！**
   - 5分钟快速入门
   - 了解三种使用方式
   - 选择适合你的方式

2. **[my_first_custom_agent.py](my_first_custom_agent.py)** 🔥 **跟着做！**
   - 完整可运行的示例
   - 从零开始创建 Agent
   - 代码有详细注释

3. **实际运行**
   ```bash
   python my_first_custom_agent.py
   ```

---

## 🎓 我想深入理解

### 推荐阅读顺序：

1. **[CLEAR_ARCHITECTURE_GUIDE.md](CLEAR_ARCHITECTURE_GUIDE.md)** 📐 **理解架构**
   - 三层架构详解
   - 每一层的职责
   - 如何选择使用哪一层

2. **[5_MINUTE_QUICKSTART.md](5_MINUTE_QUICKSTART.md)** ⚡ **快速上手**
   - 核心概念
   - 实际例子
   - 快速开始

3. **[example_custom_operators_and_prompts.py](example_custom_operators_and_prompts.py)** 💡 **进阶示例**
   - 自定义 Operator
   - 自定义 Prompt
   - 完整的工作流

---

## 🚀 我想创建自定义 Agent

### 推荐阅读顺序：

1. **[my_first_custom_agent.py](my_first_custom_agent.py)** 🎯 **从零开始**
   - 完整的示例代码
   - 可以直接运行
   - 修改成你自己的

2. **[HOW_TO_ADD_OPERATORS_AND_PROMPTS.md](HOW_TO_ADD_OPERATORS_AND_PROMPTS.md)** 🔧 **扩展功能**
   - 创建自定义 Operator
   - 创建自定义 Prompt
   - 高级用法

3. **[CLEAR_ARCHITECTURE_GUIDE.md](CLEAR_ARCHITECTURE_GUIDE.md)** 📐 **理解架构**
   - 深入理解架构
   - 如何组织代码
   - 最佳实践

---

## 🔬 我想参考具体示例

### 推荐阅读：

| 文档 | 用途 | 难度 |
|------|------|------|
| **[my_first_custom_agent.py](my_first_custom_agent.py)** | 简单单次执行 Agent | ⭐ |
| **[example_custom_operators_and_prompts.py](example_custom_operators_and_prompts.py)** | 使用自定义 Operator/Prompt | ⭐⭐⭐ |
| **[test_builtin_custom_agent.py](test_builtin_custom_agent.py)** | 注册并使用自定义 Agent | ⭐⭐ |

---

## 📚 所有文档列表

### 📖 快速开始
- **[5_MINUTE_QUICKSTART.md](5_MINUTE_QUICKSTART.md)** - 5分钟快速入门
- **[my_first_custom_agent.py](my_first_custom_agent.py)** - 第一个自定义 Agent

### 📐 架构理解
- **[CLEAR_ARCHITECTURE_GUIDE.md](CLEAR_ARCHITECTURE_GUIDE.md)** - 清晰架构指南
- **[FINAL_BASE_AGENT_SOLUTION.md](FINAL_BASE_AGENT_SOLUTION.md)** - BaseAgent 解决方案
- **[FINAL_COMPLETE_SOLUTION.md](FINAL_COMPLETE_SOLUTION.md)** - 完整解决方案

### 🔧 扩展开发
- **[HOW_TO_ADD_OPERATORS_AND_PROMPTS.md](HOW_TO_ADD_OPERATORS_AND_PROMPTS.md)** - 添加 Operators 和 Prompts
- **[example_custom_operators_and_prompts.py](example_custom_operators_and_prompts.py)** - 完整扩展示例

### 📝 其他参考
- **[BASE_AGENT_ALIAS.md](BASE_AGENT_ALIAS.md)** - BaseAgent 别名说明
- **[DSLINGTON_2_INHERITS_DSAT.md](DSLINGTON_2_INHERITS_DSAT.md)** - DSLighting 2.0 继承 DSAT
- **[CREATE_CUSTOM_AGENT_GUIDE.md](CREATE_CUSTOM_AGENT_GUIDE.md)** - 创建自定义 Agent 指南

---

## 🎯 学习路径推荐

### 路径 A: 快速上手（30分钟）
```
1. 5_MINUTE_QUICKSTART.md (10分钟)
2. my_first_custom_agent.py (10分钟)
3. 运行并修改代码 (10分钟)
```

### 路径 B: 深入理解（2小时）
```
1. 5_MINUTE_QUICKSTART.md (10分钟)
2. CLEAR_ARCHITECTURE_GUIDE.md (30分钟)
3. my_first_custom_agent.py (20分钟)
4. example_custom_operators_and_prompts.py (30分钟)
5. 实践：创建自己的 Agent (30分钟)
```

### 路径 C: 完全掌握（1天）
```
1. 阅读所有快速开始文档 (1小时)
2. 理解架构和设计 (2小时)
3. 学习如何扩展 (2小时)
4. 实践：创建复杂 Agent (3小时)
5. 阅读 DSAT 架构文档（可选）(2小时)
```

---

## 💡 常见问题速查

### Q: 我该从哪里开始？
**A**: 从 `[5_MINUTE_QUICKSTART.md](5_MINUTE_QUICKSTART.md)` 开始

### Q: 我只想使用，不想写代码
**A**: 直接运行：
```python
import dslighting
result = dslighting.run_agent(task_id="bike-sharing-demand")
```

### Q: 我想创建自己的 Agent
**A**: 看 `[my_first_custom_agent.py](my_first_custom_agent.py)` 并跟着做

### Q: 我需要理解底层架构
**A**: 看 `[CLEAR_ARCHITECTURE_GUIDE.md](CLEAR_ARCHITECTURE_GUIDE.md)`

### Q: 我想自定义 Operator/Prompt
**A**: 看 `[HOW_TO_ADD_OPERATORS_AND_PROMPTS.md](HOW_TO_ADD_OPERATORS_AND_PROMPTS.md)`

### Q: 我需要更多示例
**A**: 看 `[example_custom_operators_and_prompts.py](example_custom_operators_and_prompts.py)`

---

## 🚀 立即开始

### 方式 1: 零代码
```bash
pip install dslighting
python -c "import dslighting; print(dslighting.run_agent(task_id='bike-sharing-demand'))"
```

### 方式 2: 运行示例
```bash
python my_first_custom_agent.py
```

### 方式 3: 阅读文档
```bash
open 5_MINUTE_QUICKSTART.md
```

---

## 📞 获取帮助

- **文档**: 见上面列表
- **GitHub**: https://github.com/usail-hkust/dslighting
- **在线文档**: https://luckyfan-cs.github.io/dslighting-web/

---

## ✅ 核心要点

**记住这3件事**：

1. **BaseAgent** - 所有 Agent 的基类
2. **Services** - 提供功能（LLM、沙箱、状态）
3. **Operators** - 执行操作（生成、执行、审查）

**所有导入都从 `dslighting`**：
```python
from dslighting import BaseAgent, LLMService, ...
```

**不需要 `import dsat`！**

---

**🎉 开始你的 DSLighting 之旅吧！**

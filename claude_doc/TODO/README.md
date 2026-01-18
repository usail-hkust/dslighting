# DSLighting TODO 文档索引

**创建时间：** 2026-01-18
**版本：** v1.9.7
**状态：** 活跃维护中

---

## 📚 文档列表

本目录包含 DSLighting 项目的改进计划和任务清单。

### 1. [IMPROVEMENT_PLAN.md](./IMPROVEMENT_PLAN.md) ⭐ 推荐首先阅读
**完整的改进计划文档（26KB）**

**内容：**
- 📊 总体评价（优点与问题）
- 🔴 高优先级问题（4 个）
- 🟡 中优先级问题（5 个）
- 🟢 低优先级改进（4 个）
- 📋 详细改进计划（6 个阶段）
- 📊 优先级矩阵
- 🎯 执行时间表

**适合：** 了解全貌，制定整体策略

---

### 2. [QUICK_FIX_CHECKLIST.md](./QUICK_FIX_CHECKLIST.md) ⚡ 快速行动指南
**快速修复清单（12KB）**

**内容：**
- ⚡ 立即可执行的任务（< 1 小时）
- 📅 本周任务（1-3 天）
- 🗓️ 第 2 周任务（2-5 天）
- 📝 文档改进任务
- 🎯 验证清单

**适合：** 快速开始修复，按步骤执行

---

### 3. [PRIORITIZED_TASKS.md](./PRIORITIZED_TASKS.md) 🎯 任务优先级
**按优先级排序的任务清单（9.4KB）**

**内容：**
- 🔴 P0 - 紧急修复（3 个任务）
- 🟡 P1 - 高优先级（3 个任务）
- 🟢 P2 - 中优先级（3 个任务）
- ⚪ P3 - 低优先级（4 个任务）
- 📊 优先级决策矩阵
- 🎯 里程碑计划（v1.9.8, v1.10.0, v1.11.0）
- 📋 工作分配模板

**适合：** 按优先级执行任务，跟踪进度

---

## 🚀 快速导航

### 我想...

**立即修复问题：**
1. 打开 [QUICK_FIX_CHECKLIST.md](./QUICK_FIX_CHECKLIST.md)
2. 从 "移除 DEBUG print 语句" 开始

**了解全貌：**
1. 打开 [IMPROVEMENT_PLAN.md](./IMPROVEMENT_PLAN.md)
2. 阅读总体评价部分

**按优先级执行：**
1. 打开 [PRIORITIZED_TASKS.md](./PRIORITIZED_TASKS.md)
2. 从 P0 任务开始

**分配任务给团队：**
1. 打开 [PRIORITIZED_TASKS.md](./PRIORITIZED_TASKS.md)
2. 查看 "工作分配模板" 部分

**规划发布里程碑：**
1. 打开 [PRIORITIZED_TASKS.md](./PRIORITIZED_TASKS.md)
2. 查看 "里程碑计划" 部分

---

## 📊 当前状态总览

### 🔴 紧急问题（需要立即处理）
1. **生产代码中的 DEBUG prints** - 26 处
   - 位置：`dslighting/core/agent.py:335-591`
   - 工作量：30 分钟
   - 影响：代码质量、用户体验

2. **缺少测试框架**
   - 工作量：0.5 天
   - 影响：代码质量保障

3. **错误处理不统一**
   - 工作量：1 小时
   - 影响：可维护性

### 🟡 高优先级（2 周内）
1. 核心模块单元测试（3-5 天）
2. enable_rag 功能测试（2 天）
3. 轻量依赖选项（1 天）

### 🟢 中优先级（1 个月内）
1. 统一文档语言（2 天）
2. 补全类型提示（2 天）
3. 重构路径处理（1 天）

### ⚪ 低优先级（可选）
1. 增强 CLI 功能（2 天）
2. 生成 API 文档（1-2 天）
3. 添加进度条（1 天）
4. 配置文件支持（2 天）

---

## 🎯 推荐执行顺序

### 第 1 周：紧急修复
- [ ] Day 1: 移除 DEBUG prints
- [ ] Day 2: 创建异常类
- [ ] Day 3-5: 建立 pytest 框架

### 第 2 周：测试覆盖
- [ ] Day 1-3: 核心模块单元测试
- [ ] Day 4-5: enable_rag 测试

### 第 3 周：优化改进
- [ ] Day 1: 轻量依赖选项
- [ ] Day 2: 重构路径处理
- [ ] Day 3-4: 补全类型提示

### 第 4 周：完善文档
- [ ] Day 1-2: 统一文档语言
- [ ] Day 3: API 文档
- [ ] Day 4-5: 更新用户文档

---

## 📝 使用指南

### 如何使用这些文档？

**如果你是维护者：**
1. 首先阅读 `IMPROVEMENT_PLAN.md` 了解全貌
2. 参考 `PRIORITIZED_TASKS.md` 规划里程碑
3. 使用 `QUICK_FIX_CHECKLIST.md` 快速开始修复

**如果你是开发者：**
1. 查看 `PRIORITIZED_TASKS.md` 领取任务
2. 参考 `QUICK_FIX_CHECKLIST.md` 的具体步骤
3. 完成后更新文档中的checkbox

**如果你是新贡献者：**
1. 先阅读 `IMPROVEMENT_PLAN.md` 的总体评价
2. 从 `QUICK_FIX_CHECKLIST.md` 的简单任务开始
3. 逐步挑战更复杂的任务

---

## 🔄 更新日志

### 2026-01-18
- ✅ 创建完整的改进计划文档
- ✅ 创建快速修复清单
- ✅ 创建优先级任务清单
- ✅ 创建本索引文件

### 下次更新
- 计划每周五更新进度
- 根据实际情况调整优先级

---

## 📧 反馈与贡献

**如何反馈：**
- 发现新的问题：添加到对应文档
- 完成任务：更新 checkbox 状态
- 建议调整：在文档中添加备注

**文档维护：**
- 保持文档同步更新
- 完成任务后标记完成
- 定期回顾和调整优先级

---

## 🔗 相关链接

- **项目主页：** https://github.com/usail-hkust/dslighting
- **PyPI：** https://pypi.org/project/dslighting/
- **在线文档：** https://luckyfan-cs.github.io/dslighting-web/
- **主 README：** ../../README.md
- **PyPI 文档：** ../../PIP_DOC/README_PIP.md

---

**最后更新：** 2026-01-18
**下次审查：** 2026-01-25（一周后）
**文档维护者：** DSLighting Team

# DSLighting Frontend

基于 Next.js + React + TailwindCSS 的Web前端界面。

## 技术栈

- **Next.js 16** - React框架
- **React 19** - UI库
- **TailwindCSS 3.4** - CSS框架
- **TypeScript** - 类型安全
- **Lucide Icons** - 图标库

## 开发环境设置

### 1. 安装依赖

```bash
npm install
```

### 2. 配置API地址

编辑 `config/api.ts`，确保后端地址正确：

```typescript
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000)

## 构建生产版本

```bash
npm run build
npm start
```

## 项目结构

```
frontend/
├── app/              # Next.js App Router
│   ├── page.tsx      # 主页
│   ├── layout.tsx    # 布局
│   └── globals.css   # 全局样式
├── components/       # React组件
│   ├── ModularChatPanel.tsx    # 聊天面板
│   ├── modules/                  # 功能模块
│   │   ├── DataPrepModule.tsx   # 数据准备
│   │   ├── EDAModule.tsx        # 探索性分析
│   │   ├── ModelTrainingModule.tsx  # 模型训练
│   │   └── ReportGenerationModule.tsx  # 报告生成
│   └── ...
├── config/           # 配置文件
│   ├── api.ts        # API配置
│   └── modules.ts    # 模块配置
├── lib/              # 工具库
├── types/            # TypeScript类型定义
└── package.json
```

## 核心功能模块

### 1. 数据准备模块 (DataPrepModule)
- 上传数据集
- 配置数据准备蓝图
- 执行数据预处理

### 2. 探索性分析模块 (EDAModule)
- 交互式数据分析
- 代码生成和执行
- 可视化结果展示

### 3. 模型训练模块 (ModelTrainingModule)
- 工作流配置
- 模型选择和训练
- 实时日志查看
- 代码历史管理

### 4. 报告生成模块 (ReportGenerationModule)
- 报告模板选择
- AI辅助报告撰写
- 报告编辑和导出

## 开发指南

### 添加新的聊天模式

1. 在 `ModularChatPanel.tsx` 中添加新的模式类型
2. 在 `config/modules.ts` 中配置模式特定的建议
3. 在后端 `chat_service.py` 中实现对应的处理逻辑

### 样式规范

- 使用 TailwindCSS utility classes
- 组件样式采用 `className` 属性
- 遵循统一的颜色主题（蓝色主色调）

### 状态管理

- 使用 React hooks (useState, useEffect)
- 本地组件状态优先
- 必要时使用 localStorage 持久化

## 常见问题

### Q: 如何修改后端API地址？
A: 编辑 `config/api.ts` 中的 `API_URL`，或设置环境变量 `NEXT_PUBLIC_API_URL`

### Q: 前端构建失败怎么办？
A: 尝试删除 `.next` 目录和 `node_modules`，然后重新安装依赖：
```bash
rm -rf .next node_modules
npm install
npm run dev
```

### Q: 如何添加新的页面？
A: 在 `app/` 目录下创建新的文件，如 `app/about/page.tsx`

## 性能优化

- 使用 Next.js Image 组件优化图片加载
- 动态导入大型组件
- 利用 React.memo 避免不必要的重渲染

## 浏览器支持

- Chrome (推荐)
- Firefox
- Safari
- Edge

最小版本要求：支持 ES2020+

# DSLighting Documentation Website

这是 DSLighting 项目的官方文档网站，使用 [VitePress](https://vitepress.dev/) 构建。

## 🌐 访问网站

文档网站部署在 GitHub Pages 上：

**https://usail-hkust.github.io/dslighting/**

## 🛠️ 本地开发

### 前置要求

- Node.js 18.x 或更高版本
- npm 9.x 或更高版本

### 安装依赖

\`\`\`bash
cd website
npm install
\`\`\`

### 启动开发服务器

\`\`\`bash
npm run docs:dev
\`\`\`

访问 http://localhost:5173 查看网站

### 构建生产版本

\`\`\`bash
npm run docs:build
\`\`\`

构建后的文件在 `docs/.vitepress/dist` 目录

## 📝 文档结构

\`\`\`
website/
├── docs/
│   ├── .vitepress/
│   │   └── config.mts      # VitePress 配置文件
│   ├── guide/              # 用户指南
│   │   ├── getting-started.md
│   │   ├── features.md
│   │   ├── data-preparation.md
│   │   ├── configuration.md
│   │   └── faq.md
│   ├── api/                # API 文档
│   │   ├── overview.md
│   │   ├── agents.md
│   │   └── benchmark.md
│   ├── public/             # 静态资源
│   │   └── logo.png
│   └── index.md            # 首页
├── package.json
└── README.md
\`\`\`

## 🚀 自动部署

文档网站通过 GitHub Actions 自动部署到 GitHub Pages。当你推送更改到 `main` 分支时，会自动触发部署流程。

部署条件：
- 修改了 `website/` 目录下的文件
- 修改了 `.github/workflows/deploy-website.yml`

## 🎨 自定义

### 修改配置

编辑 `docs/.vitepress/config.mts` 文件来修改：
- 网站标题和描述
- 导航菜单
- 侧边栏结构
- 社交链接

### 添加新页面

1. 在 `docs/guide/` 或 `docs/api/` 目录创建新的 `.md` 文件
2. 在 `config.mts` 的相应侧边栏配置中添加链接

### 修改样式

VitePress 使用 CSS 变量进行样式定制。可以在 `.vitepress/theme/style.css` 中添加自定义样式。

## 📚 资源

- [VitePress 官方文档](https://vitepress.dev/)
- [DSLIGHTING 主仓库](https://github.com/usail-hkust/dslighting)

## 📄 许可证

AGPL-3.0

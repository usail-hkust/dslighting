import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'DSLIGHTING',
  description: '全流程数据科学智能助手 - End-to-End Data Science Intelligent Assistant',
  lang: 'zh-CN',
  base: '/dslighting/',
  ignoreDeadLinks: true,
  head: [
    ['link', { rel: 'icon', href: '/dslighting/logo.png' }]
  ],

  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '快速开始', link: '/guide/getting-started' },
      { text: '核心功能', link: '/guide/features' },
      { text: 'API 文档', link: '/api/overview' },
      {
        text: 'GitHub',
        link: 'https://github.com/usail-hkust/dslighting'
      }
    ],

    sidebar: {
      '/guide/': [
        {
          text: '指南',
          items: [
            { text: '快速开始', link: '/guide/getting-started' },
            { text: '核心功能', link: '/guide/features' },
            { text: '数据准备', link: '/guide/data-preparation' },
            { text: '配置说明', link: '/guide/configuration' },
            { text: '常见问题', link: '/guide/faq' }
          ]
        }
      ],
      '/api/': [
        {
          text: 'API 文档',
          items: [
            { text: '概览', link: '/api/overview' },
            { text: 'Agent 工作流', link: '/api/agents' },
            { text: 'Benchmark API', link: '/api/benchmark' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/usail-hkust/dslighting' }
    ],

    footer: {
      message: '基于 AGPL-3.0 许可证发布',
      copyright: 'Copyright © 2025-present USAIL Lab'
    },

    search: {
      provider: 'local'
    }
  }
})

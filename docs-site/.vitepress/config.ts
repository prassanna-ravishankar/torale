import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(
  defineConfig({
  title: 'Torale Docs',
  description: 'Grounded search monitoring platform for automated web monitoring',
  base: '/',

  ignoreDeadLinks: true,

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/logo.svg' }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '32x32', href: '/logo-32.png' }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '64x64', href: '/logo-64.png' }],
    ['meta', { name: 'theme-color', content: '#203345' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'Torale Documentation' }],
    ['meta', { property: 'og:description', content: 'Automated web monitoring with intelligent condition evaluation' }],
  ],

  themeConfig: {
    logo: '/logo.svg',

    nav: [
      { text: 'Getting Started', link: '/getting-started/', activeMatch: '/getting-started/' },
      { text: 'User Guide', link: '/user-guide/dashboard', activeMatch: '/user-guide/' },
      { text: 'SDK', link: '/sdk/quickstart', activeMatch: '/sdk/' },
      { text: 'CLI', link: '/cli/quickstart', activeMatch: '/cli/' },
      { text: 'API', link: '/api/overview', activeMatch: '/api/' },
      {
        text: 'Self-Hosted',
        items: [
          { text: 'Docker Compose', link: '/self-hosted/docker-compose' },
          { text: 'Kubernetes', link: '/self-hosted/kubernetes' },
          { text: 'Architecture', link: '/self-hosted/architecture' }
        ]
      },
      { text: 'App', link: 'https://torale.ai' }
    ],

    sidebar: {
      '/getting-started/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Overview', link: '/getting-started/' },
            { text: 'Web Dashboard', link: '/getting-started/web-dashboard' },
            { text: 'CLI', link: '/getting-started/cli' },
            { text: 'Python SDK', link: '/getting-started/sdk' },
            { text: 'Self-Hosted', link: '/getting-started/self-hosted' }
          ]
        }
      ],

      '/user-guide/': [
        {
          text: 'User Guide',
          items: [
            { text: 'Dashboard Overview', link: '/user-guide/dashboard' },
            { text: 'Creating Tasks', link: '/user-guide/creating-tasks' },
            { text: 'Task Templates', link: '/user-guide/templates' },
            { text: 'Managing Tasks', link: '/user-guide/managing-tasks' },
            { text: 'Viewing Results', link: '/user-guide/results' },
            { text: 'Notifications', link: '/user-guide/notifications' }
          ]
        }
      ],

      '/sdk/': [
        {
          text: 'Python SDK',
          items: [
            { text: 'Quickstart', link: '/sdk/quickstart' },
            { text: 'Authentication', link: '/sdk/authentication' },
            { text: 'Tasks', link: '/sdk/tasks' },
            { text: 'Preview', link: '/sdk/preview' },
            { text: 'Async Client', link: '/sdk/async' },
            { text: 'Error Handling', link: '/sdk/errors' }
          ]
        }
      ],

      '/cli/': [
        {
          text: 'CLI',
          items: [
            { text: 'Quickstart', link: '/cli/quickstart' },
            { text: 'Authentication', link: '/cli/authentication' },
            { text: 'Commands', link: '/cli/commands' },
            { text: 'Configuration', link: '/cli/configuration' }
          ]
        }
      ],

      '/api/': [
        {
          text: 'API Reference',
          items: [
            { text: 'Overview', link: '/api/overview' },
            { text: 'Authentication', link: '/api/authentication' },
            { text: 'Tasks', link: '/api/tasks' },
            { text: 'Executions', link: '/api/executions' },
            { text: 'Notifications', link: '/api/notifications' },
            { text: 'Admin', link: '/api/admin' },
            { text: 'Errors', link: '/api/errors' }
          ]
        }
      ],

      '/self-hosted/': [
        {
          text: 'Self-Hosted',
          items: [
            { text: 'Docker Compose', link: '/self-hosted/docker-compose' },
            { text: 'Kubernetes', link: '/self-hosted/kubernetes' },
            { text: 'Architecture', link: '/self-hosted/architecture' },
            { text: 'Configuration', link: '/self-hosted/configuration' },
            { text: 'Migrations', link: '/self-hosted/migrations' }
          ]
        }
      ],

      '/contributing/': [
        {
          text: 'Contributing',
          items: [
            { text: 'Development Setup', link: '/contributing/setup' },
            { text: 'Testing', link: '/contributing/testing' },
            { text: 'Code Style', link: '/contributing/code-style' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/torale-ai/torale' }
    ],

    search: {
      provider: 'local',
      options: {
        detailedView: true
      }
    },

    editLink: {
      pattern: 'https://github.com/torale-ai/torale/edit/main/docs-site/:path',
      text: 'Edit this page on GitHub'
    },

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2025 Torale'
    }
  },

  markdown: {
    theme: {
      light: 'github-light',
      dark: 'github-dark'
    },
    lineNumbers: true
  },

  mermaid: {
    theme: 'base',
    themeVariables: {
      // Torale brand colors
      primaryColor: '#203345',
      primaryTextColor: '#fff',
      primaryBorderColor: '#1a2836',

      secondaryColor: '#4f9eff',
      secondaryTextColor: '#000',
      secondaryBorderColor: '#3d7ec7',

      tertiaryColor: '#e9ebef',
      tertiaryTextColor: '#000',
      tertiaryBorderColor: '#d0d3d9',

      // General styling
      background: '#ffffff',
      mainBkg: '#e9ebef',
      lineColor: '#333333',
      textColor: '#333333',
      fontFamily: 'Inter, system-ui, sans-serif',
      fontSize: '16px',

      // Flowchart
      nodeBorder: '#203345',
      clusterBkg: '#f5f6f8',
      clusterBorder: '#203345',
      defaultLinkColor: '#333333'
    }
  }
})
)

import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Torale Docs',
  description: 'Grounded search monitoring platform for automated web monitoring',
  base: '/',

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/logo.svg' }],
    ['meta', { name: 'theme-color', content: '#3b82f6' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'Torale Documentation' }],
    ['meta', { property: 'og:description', content: 'Grounded search monitoring platform for automated web monitoring' }],
  ],

  themeConfig: {
    logo: '/logo.svg',

    nav: [
      { text: 'Guide', link: '/guide/getting-started', activeMatch: '/guide/' },
      { text: 'API', link: '/api/authentication', activeMatch: '/api/' },
      { text: 'SDK', link: '/sdk/installation', activeMatch: '/sdk/' },
      { text: 'CLI', link: '/cli/installation', activeMatch: '/cli/' },
      {
        text: 'More',
        items: [
          { text: 'Architecture', link: '/architecture/overview' },
          { text: 'Deployment', link: '/deployment/self-hosted' },
          { text: 'Contributing', link: '/contributing/setup' }
        ]
      },
      { text: 'App', link: 'https://torale.ai' }
    ],

    sidebar: {
      '/guide/': [
        {
          text: 'Introduction',
          items: [
            { text: 'Getting Started', link: '/guide/getting-started' },
            { text: 'How It Works', link: '/guide/how-it-works' },
            { text: 'Use Cases', link: '/guide/use-cases' }
          ]
        },
        {
          text: 'Core Concepts',
          items: [
            { text: 'Creating Tasks', link: '/guide/creating-tasks' },
            { text: 'Task Templates', link: '/guide/task-templates' },
            { text: 'Scheduling', link: '/guide/scheduling' },
            { text: 'Notifications', link: '/guide/notifications' },
            { text: 'State Tracking', link: '/guide/state-tracking' }
          ]
        },
        {
          text: 'Advanced',
          items: [
            { text: 'Troubleshooting', link: '/guide/troubleshooting' }
          ]
        }
      ],

      '/api/': [
        {
          text: 'API Reference',
          items: [
            { text: 'Authentication', link: '/api/authentication' },
            { text: 'Tasks', link: '/api/tasks' },
            { text: 'Executions', link: '/api/executions' },
            { text: 'Notifications', link: '/api/notifications' },
            { text: 'Admin Endpoints', link: '/api/admin' },
            { text: 'Error Handling', link: '/api/errors' }
          ]
        }
      ],

      '/sdk/': [
        {
          text: 'Python SDK',
          items: [
            { text: 'Installation', link: '/sdk/installation' },
            { text: 'Quickstart', link: '/sdk/quickstart' },
            { text: 'Async Client', link: '/sdk/async-client' },
            { text: 'Examples', link: '/sdk/examples' },
            { text: 'Error Handling', link: '/sdk/error-handling' }
          ]
        }
      ],

      '/cli/': [
        {
          text: 'CLI Reference',
          items: [
            { text: 'Installation', link: '/cli/installation' },
            { text: 'Authentication', link: '/cli/authentication' },
            { text: 'Task Commands', link: '/cli/tasks' },
            { text: 'Configuration', link: '/cli/configuration' }
          ]
        }
      ],

      '/architecture/': [
        {
          text: 'Architecture',
          items: [
            { text: 'System Overview', link: '/architecture/overview' },
            { text: 'Grounded Search', link: '/architecture/grounded-search' },
            { text: 'Temporal Workflows', link: '/architecture/temporal-workflows' },
            { text: 'State Tracking', link: '/architecture/state-tracking' },
            { text: 'Database Schema', link: '/architecture/database-schema' },
            { text: 'Executor System', link: '/architecture/executors' }
          ]
        }
      ],

      '/deployment/': [
        {
          text: 'Deployment',
          items: [
            { text: 'Self-Hosted (Docker)', link: '/deployment/self-hosted' },
            { text: 'Kubernetes (GKE)', link: '/deployment/kubernetes' },
            { text: 'CI/CD Setup', link: '/deployment/ci-cd' },
            { text: 'Production Best Practices', link: '/deployment/production' },
            { text: 'Cost Optimization', link: '/deployment/cost-optimization' }
          ]
        }
      ],

      '/contributing/': [
        {
          text: 'Contributing',
          items: [
            { text: 'Development Setup', link: '/contributing/setup' },
            { text: 'Testing Guide', link: '/contributing/testing' },
            { text: 'Frontend Style Guide', link: '/contributing/frontend-style' },
            { text: 'Code Conventions', link: '/contributing/conventions' }
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
  }
})

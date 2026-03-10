import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(
  defineConfig({
  title: 'Torale Docs',
  description: 'Torale developer documentation — API reference, Python SDK, and CLI',
  base: '/',
  lang: 'en-US',
  lastUpdated: true,

  sitemap: {
    hostname: 'https://docs.torale.ai'
  },

  ignoreDeadLinks: [
    // Ignore localhost URLs in documentation
    /^http:\/\/localhost/
  ],

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/logo.svg' }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '32x32', href: '/logo-32.png' }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '64x64', href: '/logo-64.png' }],
    ['meta', { name: 'theme-color', content: '#18181b' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'Torale Documentation' }],
    ['meta', { property: 'og:description', content: 'Automated web monitoring with intelligent condition evaluation' }],
    ['meta', { property: 'og:image', content: 'https://docs.torale.ai/og-image.png' }],
    ['meta', { property: 'og:image:width', content: '1200' }],
    ['meta', { property: 'og:image:height', content: '630' }],
  ],

  themeConfig: {
    logo: '/logo.svg',

    nav: [
      { text: 'Getting Started', link: '/getting-started/', activeMatch: '/getting-started/' },
      { text: 'API', link: '/api/overview', activeMatch: '/api/' },
      { text: 'SDK', link: '/sdk/quickstart', activeMatch: '/sdk/' },
      { text: 'CLI', link: '/cli/quickstart', activeMatch: '/cli/' },
      { text: 'App', link: 'https://torale.ai' }
    ],

    sidebar: {
      '/getting-started/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Overview', link: '/getting-started/' },
            { text: 'Python SDK', link: '/getting-started/sdk' },
            { text: 'CLI', link: '/getting-started/cli' }
          ]
        }
      ],


      '/sdk/': [
        {
          text: 'Python SDK',
          items: [
            { text: 'Quickstart', link: '/sdk/quickstart' },
            { text: 'Installation', link: '/sdk/installation' },
            { text: 'Authentication', link: '/sdk/authentication' },
            { text: 'Tasks', link: '/sdk/tasks' },
            { text: 'Async Client', link: '/sdk/async' },
            { text: 'Error Handling', link: '/sdk/errors' },
            { text: 'Examples', link: '/sdk/examples' }
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
    lineNumbers: false
  },

  mermaid: {
    theme: 'base',
    themeVariables: {
      // Neo-brutalist theme - zinc grays + brand red accents
      primaryColor: '#fafafa',           // zinc-50
      primaryTextColor: '#18181b',       // zinc-900
      primaryBorderColor: '#18181b',     // zinc-900

      secondaryColor: '#ffffff',         // white
      secondaryTextColor: '#18181b',     // zinc-900
      secondaryBorderColor: '#e4e4e7',   // zinc-200

      tertiaryColor: '#f4f4f5',          // zinc-100
      tertiaryTextColor: '#71717a',      // zinc-500
      tertiaryBorderColor: '#e4e4e7',    // zinc-200

      // General styling - technical aesthetic
      background: '#ffffff',
      mainBkg: '#fafafa',
      lineColor: '#18181b',
      textColor: '#18181b',
      fontFamily: 'Inter, system-ui, sans-serif',
      fontSize: '16px',

      // Flowchart - brutalist black lines
      nodeBorder: '#18181b',
      clusterBkg: '#f4f4f5',
      clusterBorder: '#18181b',
      defaultLinkColor: '#18181b',

      // Node colors
      nodeTextColor: '#18181b',

      // Accent color (brand red for emphasis)
      accentColor: 'hsl(10, 90%, 55%)',
      accentTextColor: '#ffffff'
    }
  }
})
)

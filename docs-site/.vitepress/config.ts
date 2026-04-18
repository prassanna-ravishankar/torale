import { defineConfig, type PageData } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

const SITE_ORIGIN = 'https://docs.torale.ai'
const SITE_DESCRIPTION = 'Torale developer documentation — API reference and Python SDK'

export default withMermaid(
  defineConfig({
  title: 'Torale Docs',
  description: SITE_DESCRIPTION,
  base: '/',
  lang: 'en-US',
  lastUpdated: true,
  cleanUrls: true,

  sitemap: {
    hostname: SITE_ORIGIN,
    transformItems: (items) => {
      const filtered = items.filter((item) => item.url !== '404' && !item.url.endsWith('/404'))
      return filtered
    },
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
    ['meta', { property: 'og:site_name', content: 'Torale Docs' }],
    ['meta', { property: 'og:image', content: `${SITE_ORIGIN}/og-image.png` }],
    ['meta', { property: 'og:image:width', content: '1200' }],
    ['meta', { property: 'og:image:height', content: '630' }],
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
    ['meta', { name: 'twitter:image', content: `${SITE_ORIGIN}/og-image.png` }],
  ],

  // Inject per-page canonical + og/twitter title+description+url into the
  // static HTML Googlebot sees. Without this, every page shares the global
  // <title>Torale Docs</title> and GSC reports "Duplicate without canonical".
  transformPageData(pageData: PageData) {
    const relPath = pageData.relativePath.replace(/(index)?\.md$/, '').replace(/\/$/, '')
    const canonical = relPath ? `${SITE_ORIGIN}/${relPath}` : `${SITE_ORIGIN}/`
    const pageTitle = pageData.title || pageData.frontmatter.title || 'Torale Docs'
    const pageDescription = pageData.frontmatter.description || SITE_DESCRIPTION
    const fullTitle = pageTitle === 'Torale Docs' ? pageTitle : `${pageTitle} | Torale Docs`

    pageData.frontmatter.head ??= []
    pageData.frontmatter.head.push(
      ['link', { rel: 'canonical', href: canonical }],
      ['meta', { name: 'description', content: pageDescription }],
      ['meta', { property: 'og:title', content: fullTitle }],
      ['meta', { property: 'og:description', content: pageDescription }],
      ['meta', { property: 'og:url', content: canonical }],
      ['meta', { name: 'twitter:title', content: fullTitle }],
      ['meta', { name: 'twitter:description', content: pageDescription }],
    )
  },

  themeConfig: {
    logo: '/logo.svg',

    nav: [
      { text: 'Getting Started', link: '/getting-started/', activeMatch: '/getting-started/' },
      { text: 'Architecture', link: '/architecture/self-scheduling-agents', activeMatch: '/architecture/' },
      { text: 'API', link: '/api/overview', activeMatch: '/api/' },
      { text: 'SDK', link: '/sdk/quickstart', activeMatch: '/sdk/' },
      { text: 'App', link: 'https://torale.ai' }
    ],

    sidebar: {
      '/getting-started/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Overview', link: '/getting-started/' },
            { text: 'Python SDK', link: '/getting-started/sdk' }
          ]
        }
      ],

      '/architecture/': [
        {
          text: 'Architecture',
          items: [
            { text: 'Self-Scheduling Agents', link: '/architecture/self-scheduling-agents' },
            { text: 'Grounded Search', link: '/architecture/grounded-search' },
            { text: 'Task State Machine', link: '/architecture/task-state-machine' }
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

      '/api/': [
        {
          text: 'API Reference',
          items: [
            { text: 'Overview', link: '/api/overview' },
            { text: 'Authentication', link: '/api/authentication' },
            { text: 'Tasks', link: '/api/tasks' },
            { text: 'Executions', link: '/api/executions' },
            { text: 'Notifications', link: '/api/notifications' },
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

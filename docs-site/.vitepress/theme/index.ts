import DefaultTheme from 'vitepress/theme'
import { onMounted } from 'vue'
import './style.css'

export default {
  extends: DefaultTheme,
  enhanceApp() {
    // Register Iconify icon packs for Mermaid diagrams
    if (typeof window !== 'undefined') {
      onMounted(() => {
        import('mermaid').then((mermaidModule) => {
          const mermaid = mermaidModule.default
          mermaid.registerIconPacks([
            {
              name: 'mdi',
              loader: () => import('@iconify-json/mdi').then((module) => module.icons),
            },
            {
              name: 'logos',
              loader: () => import('@iconify-json/logos').then((module) => module.icons),
            },
            {
              name: 'carbon',
              loader: () => import('@iconify-json/carbon').then((module) => module.icons),
            },
          ])
        })
      })
    }
  }
}

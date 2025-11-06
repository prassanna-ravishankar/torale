/// <reference types="svelte" />
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CLERK_PUBLISHABLE_KEY: string
  readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Runtime config injected at deployment time
interface RuntimeConfig {
  apiUrl: string
  clerkPublishableKey: string
}

interface Window {
  CONFIG?: RuntimeConfig
}

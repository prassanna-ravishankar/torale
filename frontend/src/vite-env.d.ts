/// <reference types="vite/client" />

interface ImportMetaEnv {
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
  CONFIG: RuntimeConfig
}

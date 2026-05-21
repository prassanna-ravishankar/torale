'use client'

import type { ReactNode } from 'react'

import { useApiSetup } from '@/hooks/useApi'

export function AuthedApiBootstrap({ children }: { children: ReactNode }) {
  useApiSetup()

  return <>{children}</>
}

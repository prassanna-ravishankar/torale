'use client'

import type { ReactNode } from 'react'
import { useEffect } from 'react'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'

import { useAuth } from '@/contexts/AuthContext'
import styles from './AuthReadyBoundary.module.css'

export function AuthReadyBoundary({ children }: { children: ReactNode }) {
  const { status, error, retryAuth, signOut } = useAuth()
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  useEffect(() => {
    if (status !== 'unauthenticated') return
    const query = searchParams.toString()
    const returnPath = query ? `${pathname}?${query}` : pathname
    router.replace(`/sign-in?redirect_url=${encodeURIComponent(returnPath)}`)
  }, [pathname, router, searchParams, status])

  if (status === 'authenticated') return <>{children}</>

  if (status === 'error') {
    return (
      <main className={styles.canvas}>
        <section className={styles.card} aria-live="polite">
          <p className={styles.eyebrow}>ACCOUNT CONNECTION</p>
          <h1>We couldn’t load your account</h1>
          <p>{error}</p>
          <div className={styles.actions}>
            <button className={styles.primary} onClick={retryAuth}>
              Try again
            </button>
            {signOut && (
              <button className={styles.secondary} onClick={() => void signOut()}>
                Sign out
              </button>
            )}
          </div>
        </section>
      </main>
    )
  }

  return (
    <main className={styles.canvas} aria-busy="true" aria-live="polite">
      <div className={styles.loading}>
        <span className={styles.pulse} aria-hidden="true" />
        <p>{status === 'unauthenticated' ? 'Taking you to sign in…' : 'Loading your watches…'}</p>
      </div>
    </main>
  )
}

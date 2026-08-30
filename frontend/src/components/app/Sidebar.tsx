'use client'

import { lazy, Suspense } from 'react'
import Link from 'next/link'
import { ownerWatchPath } from '@/lib/watchRoutes'
import { usePathname } from 'next/navigation'
import { Eye, Bell, Archive, Shield, Settings, Plug } from 'lucide-react'

import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'
import type { Task } from '@/types'

import styles from './AppShell.module.css'

const UserMenu = lazy(() => import('@/components/UserMenu'))

interface SidebarProps {
  /**
   * Callback fired when any nav item is clicked. Used by MobileDrawer to close
   * itself after navigation. Desktop sidebar passes a no-op.
   */
  onNavigate?: () => void
  /**
   * Active watches the user has — used to populate counts + Recent section.
   * Pass empty array if data isn't loaded; sidebar degrades gracefully.
   */
  watches?: Task[]
}

interface NavItemProps {
  to: string
  label: string
  icon: React.ReactNode
  count?: number
  matchPaths?: string[]
  onClick?: () => void
}

function NavItem({ to, label, icon, count, matchPaths, onClick }: NavItemProps) {
  const pathname = usePathname() || ''
  const isActive = (matchPaths ?? [to]).some((p) => pathname.startsWith(p))
  return (
    <Link
      href={to}
      onClick={onClick}
      className={cn(styles.item, isActive && styles.active)}
      aria-current={isActive ? 'page' : undefined}
    >
      <span className={styles.itemIcon}>{icon}</span>
      <span>{label}</span>
      {count != null && <span className={styles.itemCount}>{count}</span>}
    </Link>
  )
}

interface RecentWatchProps {
  watch: Task
  onClick?: () => void
}

function RecentWatch({ watch, onClick }: RecentWatchProps) {
  const pathname = usePathname() || ''
  const isActive = pathname === ownerWatchPath(watch.id)
  const status =
    watch.last_execution?.notification != null
      ? 'triggered'
      : watch.state === 'paused'
        ? 'paused'
        : watch.state === 'completed'
          ? 'idle'
          : 'active'
  return (
    <Link
      href={ownerWatchPath(watch.id)}
      onClick={onClick}
      className={cn(styles.watch, isActive && styles.active)}
    >
      <span className={cn(styles.watchDot, styles[status])} />
      <span className={styles.watchName}>{watch.name || watch.condition_description}</span>
    </Link>
  )
}

export const Sidebar: React.FC<SidebarProps> = ({ onNavigate, watches = [] }) => {
  const { user } = useAuth()
  const noAuth = process.env.NEXT_PUBLIC_WEBWHEN_NOAUTH === '1'
  const isAdmin = user?.publicMetadata?.role === 'admin'

  const triggeredCount = watches.filter(
    (w) => w.last_execution?.notification != null,
  ).length

  // Top 5 by updated_at (or created_at fallback), nulls last
  const recent = [...watches]
    .filter((w) => w.state !== 'completed')
    .sort((a, b) => {
      const ta = a.updated_at ?? a.created_at
      const tb = b.updated_at ?? b.created_at
      return new Date(tb).getTime() - new Date(ta).getTime()
    })
    .slice(0, 5)

  const initials =
    [user?.firstName?.[0], user?.lastName?.[0]]
      .filter(Boolean)
      .join('')
      .toUpperCase() || user?.email?.[0]?.toUpperCase() || '?'

  const displayName =
    [user?.firstName, user?.lastName].filter(Boolean).join(' ') || user?.email || 'webwhen'

  return (
    <aside className={styles.sidebar}>
      <Link href="/dashboard" className={styles.brand} onClick={onNavigate}>
        <img
          src="/brand/webwhen-mark.svg"
          alt="webwhen"
          className={styles.brandImg}
        />
        <span className={styles.brandWord}>webwhen</span>
      </Link>

      <div className={styles.section}>
        <NavItem
          to="/dashboard"
          label="All watches"
          icon={<Eye size={16} strokeWidth={1.5} />}
          count={watches.length || undefined}
          matchPaths={['/dashboard', '/tasks']}
          onClick={onNavigate}
        />
        <NavItem
          to="/dashboard?filter=triggered"
          label="Triggered"
          icon={<Bell size={16} strokeWidth={1.5} />}
          count={triggeredCount || undefined}
          onClick={onNavigate}
        />
        <NavItem
          to="/explore"
          label="Explore"
          icon={<Archive size={16} strokeWidth={1.5} />}
          onClick={onNavigate}
        />
      </div>

      {recent.length > 0 && (
        <div className={styles.section}>
          <div className={styles.label}>Recent</div>
          {recent.map((w) => (
            <RecentWatch key={w.id} watch={w} onClick={onNavigate} />
          ))}
        </div>
      )}

      {user && (
        <div className={styles.section}>
          <NavItem
            to="/settings/notifications"
            label="Settings"
            icon={<Settings size={16} strokeWidth={1.5} />}
            matchPaths={['/settings']}
            onClick={onNavigate}
          />
          <NavItem
            to="/settings/connectors"
            label="Connectors"
            icon={<Plug size={16} strokeWidth={1.5} />}
            onClick={onNavigate}
          />
          {isAdmin && (
            <NavItem
              to="/admin"
              label="Admin"
              icon={<Shield size={16} strokeWidth={1.5} />}
              onClick={onNavigate}
            />
          )}
        </div>
      )}

      <div className={styles.foot}>
        {user ? (
          <>
            {!noAuth ? (
              <Suspense fallback={<div className={styles.avatar}>{initials}</div>}>
                <UserMenu />
              </Suspense>
            ) : (
              <div className={styles.avatar}>{initials}</div>
            )}
            <div className={styles.footUser}>
              <div className={styles.who}>{displayName}</div>
              <div className={styles.plan}>beta</div>
            </div>
          </>
        ) : (
          <Link href="/sign-in" className={styles.signInLink} onClick={onNavigate}>
            Sign in →
          </Link>
        )}
      </div>
    </aside>
  )
}

export default Sidebar

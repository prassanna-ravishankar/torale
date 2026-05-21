'use client'

import Link from 'next/link'
import { MoreHorizontal } from 'lucide-react'

import { cn } from '@/lib/utils'
import type { Task } from '@/types'

import styles from './Dashboard.module.css'

interface WatchRowProps {
  watch: Task
  onMore?: (watch: Task) => void
}

function formatRelative(iso: string | null | undefined): string {
  if (!iso) return '—'
  const then = new Date(iso).getTime()
  const now = Date.now()
  const diff = now - then
  const min = Math.floor(diff / 60_000)
  if (min < 1) return 'just now'
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  const day = Math.floor(hr / 24)
  if (day < 30) return `${day}d ago`
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function formatNext(iso: string | null | undefined): string {
  if (!iso) return '—'
  const then = new Date(iso).getTime()
  const now = Date.now()
  const diff = then - now
  if (diff < 0) return 'soon'
  const min = Math.ceil(diff / 60_000)
  if (min < 60) return `in ${min}m`
  const hr = Math.ceil(min / 60)
  if (hr < 24) return `in ${hr}h`
  const day = Math.ceil(hr / 24)
  return `in ${day}d`
}

/**
 * Single watch row in the dashboard list. Per kit's `.watch-row` 5-col grid:
 * status dot · serif-italic question · last check · next check · action menu.
 * Click anywhere on the row navigates to the watch detail.
 */
export const WatchRow: React.FC<WatchRowProps> = ({ watch, onMore }) => {
  const triggered = watch.last_execution?.notification != null
  const status: 'active' | 'triggered' | 'paused' | 'completed' | 'error' = triggered
    ? 'triggered'
    : watch.state === 'paused'
      ? 'paused'
      : watch.state === 'completed'
        ? 'completed'
        : 'active'

  const lastCheck = watch.last_execution?.started_at
  const nextCheck = watch.next_run

  return (
    <Link href={`/dashboard/tasks/${watch.id}`} className={styles.row}>
      <span className={cn(styles.dot, styles[status])} aria-hidden />
      <div className={styles.text}>
        <p className={styles.q}>{watch.condition_description || watch.name}</p>
        {watch.name && watch.condition_description && (
          <div className={styles.meta}>{watch.name}</div>
        )}
      </div>
      <div className={cn(styles.cell, triggered && styles.ember)}>
        {triggered ? `triggered · ${formatRelative(lastCheck)}` : `last · ${formatRelative(lastCheck)}`}
      </div>
      <div className={styles.cell}>
        {watch.state === 'paused' ? 'paused' : watch.state === 'completed' ? 'done' : `next · ${formatNext(nextCheck)}`}
      </div>
      <button
        type="button"
        className={styles.more}
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          onMore?.(watch)
        }}
        aria-label="More actions"
      >
        <MoreHorizontal size={16} strokeWidth={1.5} />
      </button>
    </Link>
  )
}

export default WatchRow

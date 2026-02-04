import { Shield, Code2, User } from 'lucide-react'

interface RoleBadgeProps {
  role?: string | null
  size?: 'sm' | 'md'
}

const roleConfig = {
  admin: {
    bg: 'bg-red-50',
    text: 'text-red-700',
    border: 'border-red-200',
    icon: Shield,
    label: 'Admin',
  },
  developer: {
    bg: 'bg-blue-50',
    text: 'text-blue-700',
    border: 'border-blue-200',
    icon: Code2,
    label: 'Developer',
  },
} as const

const defaultConfig = {
  bg: 'bg-zinc-50',
  text: 'text-zinc-600',
  border: 'border-zinc-200',
  icon: User,
  label: 'User',
}

export function RoleBadge({ role, size = 'sm' }: RoleBadgeProps) {
  const config = (role && role in roleConfig)
    ? roleConfig[role as keyof typeof roleConfig]
    : defaultConfig

  const Icon = config.icon
  const textSize = size === 'sm' ? 'text-[9px]' : 'text-[10px]'

  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 ${config.bg} ${config.text} ${textSize} font-mono uppercase tracking-wider border ${config.border}`}>
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  )
}

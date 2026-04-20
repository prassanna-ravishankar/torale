import React from 'react';
import { Boxes, FileText, GitBranch, Layers } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConnectorLogoProps {
  slug: string;
  displayName: string;
  size?: 'sm' | 'md' | 'lg';
  muted?: boolean;
  className?: string;
}

// Map toolkit slug → lucide icon. Keep tiny; swap for vendor SVG once we
// have licensed assets. Fallback is the display name's first letter.
const ICON_BY_SLUG: Record<string, React.ComponentType<{ className?: string }>> = {
  notion: FileText,
  linear: Layers,
  github: GitBranch,
};

const sizeClass: Record<NonNullable<ConnectorLogoProps['size']>, string> = {
  sm: 'w-8 h-8 text-sm',
  md: 'w-10 h-10 text-base',
  lg: 'w-12 h-12 text-lg',
};

const iconSizeClass: Record<NonNullable<ConnectorLogoProps['size']>, string> = {
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
};

export const ConnectorLogo: React.FC<ConnectorLogoProps> = ({
  slug,
  displayName,
  size = 'md',
  muted = false,
  className,
}) => {
  const Icon = ICON_BY_SLUG[slug];
  return (
    <div
      className={cn(
        'flex items-center justify-center font-grotesk font-bold',
        sizeClass[size],
        muted ? 'bg-zinc-200 text-zinc-500' : 'bg-zinc-900 text-white',
        className
      )}
      aria-label={displayName}
    >
      {Icon ? <Icon className={iconSizeClass[size]} /> : displayName.charAt(0).toUpperCase()}
    </div>
  );
};

export { Boxes as ConnectorFallbackIcon };

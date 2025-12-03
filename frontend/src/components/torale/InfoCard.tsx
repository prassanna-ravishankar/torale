import React from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { SectionLabel } from './SectionLabel';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * InfoCard - Icon + Label + Content card for configuration sections
 *
 * Used in TaskDetail for displaying:
 * - Schedule
 * - Trigger Condition
 * - When to Notify
 * - Notification Channels
 */

interface InfoCardProps {
  icon: LucideIcon;
  label: string;
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export const InfoCard: React.FC<InfoCardProps> = ({
  icon: Icon,
  label,
  children,
  className,
  onClick,
}) => {
  return (
    <Card
      className={cn('border-2', onClick && 'cursor-pointer hover:border-zinc-900 transition-colors', className)}
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <SectionLabel icon={Icon}>{label}</SectionLabel>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
};

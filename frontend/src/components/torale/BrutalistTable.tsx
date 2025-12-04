import React from 'react';
import { cn } from '@/lib/utils';

/**
 * BrutalistTable - Neo-brutalist table component
 *
 * Provides consistent table styling across the application with:
 * - Bold borders (2px)
 * - Uppercase mono headers
 * - Zebra striping optional
 * - Hover states
 */

interface BrutalistTableProps {
  children: React.ReactNode;
  className?: string;
}

interface BrutalistTableHeaderProps {
  children: React.ReactNode;
  className?: string;
}

interface BrutalistTableBodyProps {
  children: React.ReactNode;
  className?: string;
}

interface BrutalistTableRowProps {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

interface BrutalistTableHeadProps {
  children: React.ReactNode;
  align?: 'left' | 'center' | 'right';
  className?: string;
}

interface BrutalistTableCellProps {
  children: React.ReactNode;
  align?: 'left' | 'center' | 'right';
  className?: string;
}

export const BrutalistTable: React.FC<BrutalistTableProps> = ({
  children,
  className,
}) => {
  return (
    <div className={cn('bg-white border-2 border-zinc-200 overflow-x-auto', className)}>
      <table className="w-full">
        {children}
      </table>
    </div>
  );
};

export const BrutalistTableHeader: React.FC<BrutalistTableHeaderProps> = ({
  children,
  className,
}) => {
  return (
    <thead className={cn('border-b-2 border-zinc-200 bg-zinc-50', className)}>
      {children}
    </thead>
  );
};

export const BrutalistTableBody: React.FC<BrutalistTableBodyProps> = ({
  children,
  className,
}) => {
  return (
    <tbody className={className}>
      {children}
    </tbody>
  );
};

export const BrutalistTableRow: React.FC<BrutalistTableRowProps> = ({
  children,
  onClick,
  className,
}) => {
  return (
    <tr
      onClick={onClick}
      className={cn(
        'border-b border-zinc-200 last:border-0',
        onClick && 'cursor-pointer hover:bg-zinc-50 transition-colors',
        className
      )}
    >
      {children}
    </tr>
  );
};

export const BrutalistTableHead: React.FC<BrutalistTableHeadProps> = ({
  children,
  align = 'left',
  className,
}) => {
  const alignmentClass = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  }[align];

  return (
    <th
      className={cn(
        'p-4 text-[10px] font-mono uppercase text-zinc-400 tracking-wider',
        alignmentClass,
        className
      )}
    >
      {children}
    </th>
  );
};

export const BrutalistTableCell: React.FC<BrutalistTableCellProps> = ({
  children,
  align = 'left',
  className,
}) => {
  const alignmentClass = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  }[align];

  return (
    <td
      className={cn(
        'p-4 text-sm',
        alignmentClass,
        className
      )}
    >
      {children}
    </td>
  );
};

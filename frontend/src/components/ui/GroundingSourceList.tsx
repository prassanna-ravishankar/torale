import React from 'react';
import { ExternalLink } from 'lucide-react';
import type { GroundingSource } from '@/types';

interface GroundingSourceListProps {
  sources: GroundingSource[];
  showTitle?: boolean;
  title?: string;
}

export const GroundingSourceList: React.FC<GroundingSourceListProps> = ({
  sources,
  showTitle = true,
  title = 'Sources:',
}) => {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      {showTitle && <p className="text-sm font-medium">{title}</p>}
      <div className="space-y-2">
        {sources.map((source, idx) => (
          <a
            key={idx}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-2 p-2 rounded-md hover:bg-muted transition-colors group"
          >
            <ExternalLink className="h-4 w-4 shrink-0 mt-0.5 text-muted-foreground group-hover:text-primary" />
            <div className="flex-1 min-w-0">
              <p className="text-sm group-hover:text-primary">
                {source.title}
              </p>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
};

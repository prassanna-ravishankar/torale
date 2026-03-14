import React from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import { FeedExecution } from '@/types';
import { BrutalistCard, SectionLabel } from '@/components/torale';
import { markdownCompact } from '@/lib/markdown';
import { formatTimeAgo, formatShortDateTime } from '@/lib/utils';
import { Search, Clock, ArrowUpRight } from 'lucide-react';

interface ResultCardProps {
  execution: FeedExecution;
  onClick?: () => void;
}

export const ResultCard: React.FC<ResultCardProps> = ({ execution, onClick }) => {
  const content = execution.notification || execution.result?.evidence;

  return (
    <BrutalistCard
      variant="clickable"
      onClick={onClick}
      hoverEffect={true}
      className="group overflow-hidden"
    >
      {/* Context Header */}
      <div className="px-4 py-3 bg-zinc-50 border-b border-zinc-100 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <div className="p-1.5 bg-white border border-zinc-200 rounded-sm text-zinc-400 group-hover:text-zinc-900 group-hover:border-zinc-300 transition-colors">
            <Search className="w-3.5 h-3.5" />
          </div>
          <div className="min-w-0">
            <h4 className="text-[11px] font-bold font-mono text-zinc-500 uppercase tracking-tight truncate">
              {execution.task_name}
            </h4>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] font-mono text-zinc-400">
            {formatTimeAgo(execution.started_at)}
          </span>
          <ArrowUpRight className="w-3.5 h-3.5 text-zinc-300 group-hover:text-zinc-900 transition-colors" />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="p-4 relative">
        <div className="max-h-[300px] overflow-hidden relative">
          <div className="prose prose-sm max-w-none text-zinc-800 leading-relaxed font-serif">
            <ReactMarkdown
              rehypePlugins={[rehypeSanitize]}
              components={markdownCompact}
            >
              {content || 'No content found.'}
            </ReactMarkdown>
          </div>
          
          {/* Fade effect for long reports */}
          <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-white to-transparent" />
        </div>
      </div>

      {/* Footer Meta */}
      <div className="px-4 py-2 flex items-center justify-between border-t border-zinc-50">
         <div className="flex items-center gap-1.5 text-[10px] font-mono text-zinc-400">
            <Clock className="w-3 h-3" />
            <span>{formatShortDateTime(execution.completed_at || execution.started_at)}</span>
         </div>
         {execution.grounding_sources && execution.grounding_sources.length > 0 && (
           <div className="text-[10px] font-mono text-zinc-400 bg-zinc-100 px-1.5 py-0.5 rounded-sm">
             {execution.grounding_sources.length} sources
           </div>
         )}
      </div>
    </BrutalistCard>
  );
};

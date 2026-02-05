import React from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { CheckCircle2, XCircle } from 'lucide-react';
import { GroundingSourceList } from '@/components/ui/GroundingSourceList';
import type { GroundingSource } from '@/types';

const MAX_DISPLAYED_ITEMS = 3;

interface SearchPreviewProps {
  answer: string;
  conditionMet: boolean;
  conditionDescription?: string;
  groundingSources: GroundingSource[];
  currentState?: any;
  showConditionBadge?: boolean;
}

export const SearchPreview: React.FC<SearchPreviewProps> = ({
  answer,
  conditionMet,
  conditionDescription,
  groundingSources,
  currentState,
  showConditionBadge = true,
}) => {
  return (
    <div className="space-y-4">
      {/* Condition Badge */}
      {showConditionBadge && conditionDescription && (
        <div className="flex items-start gap-2 p-3 bg-muted rounded-md">
          {conditionMet ? (
            <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
          ) : (
            <XCircle className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
          )}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium mb-1">
              {conditionMet ? 'Condition Met' : 'Condition Not Met'}
            </p>
            <p className="text-sm text-muted-foreground">
              {conditionDescription}
            </p>
          </div>
        </div>
      )}

      {/* Answer */}
      <Card className="p-4">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Badge variant="outline">Answer</Badge>
          </div>
          <div className="text-sm prose prose-sm max-w-none">
            <ReactMarkdown
              rehypePlugins={[rehypeSanitize]}
              components={{
                p: ({ children }) => <p className="mb-3 leading-relaxed">{children}</p>,
                ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1.5">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1.5">{children}</ol>,
                li: ({ children }) => <li className="text-sm leading-relaxed">{children}</li>,
                strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
                h1: ({ children }) => <h1 className="text-xl font-bold mb-3 mt-4">{children}</h1>,
                h2: ({ children }) => <h2 className="text-lg font-semibold mb-2 mt-3">{children}</h2>,
                h3: ({ children }) => <h3 className="text-base font-semibold mb-2 mt-2">{children}</h3>,
              }}
            >
              {answer}
            </ReactMarkdown>
          </div>
        </div>
      </Card>

      {/* Grounding Sources */}
      <GroundingSourceList sources={groundingSources} />

      {/* Current State (if provided) */}
      {currentState && Object.keys(currentState).length > 0 && (
        <Card className="p-3">
          <p className="text-sm font-medium mb-2">Extracted Information:</p>
          <div className="text-sm text-muted-foreground space-y-2">
            {Object.entries(currentState).map(([key, value]) => (
              <div key={key}>
                <span className="font-medium text-foreground">
                  {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}:
                </span>{' '}
                {Array.isArray(value) ? (
                  value.length > MAX_DISPLAYED_ITEMS ? (
                    <span className="text-xs">{value.slice(0, MAX_DISPLAYED_ITEMS).join(', ')} and {value.length - MAX_DISPLAYED_ITEMS} more</span>
                  ) : (
                    <span className="text-xs">{value.join(', ')}</span>
                  )
                ) : typeof value === 'object' && value !== null ? (
                  <pre className="text-xs mt-1 p-2 bg-background rounded overflow-x-auto">
                    {JSON.stringify(value, null, 2)}
                  </pre>
                ) : (
                  <span className="text-xs">{String(value)}</span>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { TaskExecution } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { GroundingSourceList } from "@/components/ui/GroundingSourceList";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
  CheckCircle2,
  XCircle,
  Clock,
  ChevronDown,
  ChevronUp,
  AlertCircle,
} from "lucide-react";

interface ExecutionTimelineProps {
  executions: TaskExecution[];
  highlightNotifications?: boolean;
}

export const ExecutionTimeline: React.FC<ExecutionTimelineProps> = ({
  executions,
  highlightNotifications = false,
}) => {
  if (executions.length === 0) {
    return (
      <div className="text-center py-12">
        <Clock className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <h3 className="mb-2">No executions yet</h3>
        <p className="text-muted-foreground">
          This task hasn't been executed yet. It will run according to its schedule.
        </p>
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success":
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case "failed":
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-yellow-500" />;
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(date);
  };

  return (
    <div className="space-y-4">
      {executions.map((execution) => {
        const [isExpanded, setIsExpanded] = useState(false);

        return (
          <Card
            key={execution.id}
            className={
              highlightNotifications && execution.condition_met
                ? "border-2 border-emerald-500 bg-emerald-50/30"
                : "border-2"
            }
          >
            <div className="p-4">
              {/* Layer 1: Status Summary (Always Visible) */}
              <div className="flex items-center justify-between gap-4 mb-3">
                <div className="flex items-center gap-3">
                  <div className="shrink-0">{getStatusIcon(execution.status)}</div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge
                      variant={
                        execution.status === "success"
                          ? "default"
                          : execution.status === "failed"
                          ? "destructive"
                          : "secondary"
                      }
                    >
                      {execution.status}
                    </Badge>

                    {execution.condition_met && (
                      <Badge className="bg-emerald-50 text-emerald-600 border-emerald-200">
                        <CheckCircle2 className="mr-1 h-3 w-3" />
                        Condition Met
                      </Badge>
                    )}
                  </div>
                </div>

                <span className="text-xs text-zinc-400 font-mono shrink-0">
                  {formatDate(execution.started_at)}
                </span>
              </div>

              {/* Layer 2: Key Information (Answer or Change Summary) */}
              {execution.change_summary && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 mb-3">
                  <p className="text-sm text-emerald-900 font-medium">
                    <span className="font-mono text-[10px] uppercase text-emerald-600 tracking-wider block mb-1">What Changed</span>
                    {execution.change_summary}
                  </p>
                </div>
              )}

              {execution.result?.answer && !isExpanded && (
                <p className="text-sm text-zinc-600 line-clamp-2 mb-3">
                  {execution.result.answer.replace(/[*#]/g, '')}
                </p>
              )}

              {/* Layer 3: Detailed Information (Collapsible) */}
              <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
                <CollapsibleTrigger className="flex items-center gap-2 text-xs font-mono text-zinc-500 hover:text-zinc-900 transition-colors mb-3">
                  {isExpanded ? (
                    <>
                      <ChevronUp className="w-3 h-3" />
                      Hide Details
                    </>
                  ) : (
                    <>
                      <ChevronDown className="w-3 h-3" />
                      Show Full Details
                    </>
                  )}
                </CollapsibleTrigger>

                <CollapsibleContent className="space-y-3">
                  {execution.result?.answer && (
                    <div className="p-4 bg-zinc-50 border-2 border-zinc-100">
                      <p className="text-[10px] font-mono uppercase text-zinc-400 tracking-wider mb-3">Full Answer</p>
                      <div className="text-sm prose prose-sm max-w-none">
                        <ReactMarkdown
                          components={{
                            p: ({ children }) => <p className="mb-3 leading-relaxed text-zinc-900">{children}</p>,
                            ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1.5">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1.5">{children}</ol>,
                            li: ({ children }) => <li className="text-sm leading-relaxed text-zinc-700">{children}</li>,
                            strong: ({ children }) => <strong className="font-bold text-zinc-900">{children}</strong>,
                            h1: ({ children }) => <h1 className="text-xl font-grotesk font-bold mb-3 mt-4 text-zinc-900">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-lg font-grotesk font-bold mb-2 mt-3 text-zinc-900">{children}</h2>,
                            h3: ({ children }) => <h3 className="text-base font-grotesk font-bold mb-2 mt-2 text-zinc-900">{children}</h3>,
                          }}
                        >
                          {execution.result.answer}
                        </ReactMarkdown>
                      </div>
                    </div>
                  )}

                  {execution.result?.current_state && (
                    <div className="p-4 bg-zinc-50 border-2 border-zinc-100">
                      <p className="text-[10px] font-mono uppercase text-zinc-400 tracking-wider mb-3">Current State</p>
                      <div className="text-sm space-y-3">
                        {Object.entries(execution.result.current_state).map(
                          ([key, value]) => (
                            <div key={key} className="flex flex-col gap-1">
                              <span className="font-mono text-xs text-zinc-900 font-bold">
                                {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                              </span>
                              {Array.isArray(value) ? (
                                value.length > 3 ? (
                                  <span className="text-sm text-zinc-600">{value.slice(0, 3).join(", ")} and {value.length - 3} more</span>
                                ) : (
                                  <span className="text-sm text-zinc-600">{value.join(", ")}</span>
                                )
                              ) : typeof value === "object" && value !== null ? (
                                <pre className="text-xs mt-1 p-3 bg-zinc-900 text-zinc-300 border border-zinc-800 overflow-x-auto font-mono">
                                  {JSON.stringify(value, null, 2)}
                                </pre>
                              ) : (
                                <span className="text-sm text-zinc-600">{String(value)}</span>
                              )}
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}

                  {execution.grounding_sources && execution.grounding_sources.length > 0 && (
                    <div className="p-4 bg-zinc-50 border-2 border-zinc-100">
                      <p className="text-[10px] font-mono uppercase text-zinc-400 tracking-wider mb-3">Sources</p>
                      <GroundingSourceList
                        sources={execution.grounding_sources}
                        title=""
                      />
                    </div>
                  )}
                </CollapsibleContent>
              </Collapsible>

              {execution.error_message && (
                <div className="p-4 bg-red-50 border-2 border-red-200">
                  <p className="text-[10px] font-mono uppercase text-red-400 tracking-wider mb-2">Error</p>
                  <p className="text-sm text-red-600 font-mono">
                    {execution.error_message}
                  </p>
                </div>
              )}
            </div>
          </Card>
        );
      })}
    </div>
  );
};

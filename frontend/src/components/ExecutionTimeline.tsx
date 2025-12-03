import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { TaskExecution } from "@/types";
import { GroundingSourceList } from "@/components/ui/GroundingSourceList";
import { StatusBadge, SectionLabel, CollapsibleSection, BrutalistCard } from "@/components/torale";
import {
  CheckCircle2,
  XCircle,
  Clock,
} from "lucide-react";

interface ExecutionTimelineProps {
  executions: TaskExecution[];
  highlightNotifications?: boolean;
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

interface ExecutionCardProps {
  execution: TaskExecution;
  highlightNotifications: boolean;
}

const ExecutionCard: React.FC<ExecutionCardProps> = ({ execution, highlightNotifications }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
          <BrutalistCard
            className={
              highlightNotifications && execution.condition_met
                ? "border-emerald-500 bg-emerald-50/30"
                : ""
            }
          >
              {/* Layer 1: Status Summary (Always Visible) */}
              <div className="flex items-center justify-between gap-4 mb-3">
                <div className="flex items-center gap-3">
                  <div className="shrink-0">{getStatusIcon(execution.status)}</div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <StatusBadge
                      variant={
                        execution.status === "success"
                          ? "success"
                          : execution.status === "failed"
                          ? "failed"
                          : "pending"
                      }
                    />

                    {execution.condition_met && (
                      <StatusBadge variant="met" />
                    )}
                  </div>
                </div>

                <span className="text-xs text-zinc-400 font-mono shrink-0">
                  {formatDate(execution.started_at)}
                </span>
              </div>

              {/* Layer 2: PRIMARY INFO - Answer & Sources (Always Visible) */}
              {execution.result?.answer && (
                <div className="mb-3 p-4 bg-white border-2 border-zinc-200">
                  <SectionLabel className="mb-3">Answer</SectionLabel>
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

              {execution.grounding_sources && execution.grounding_sources.length > 0 && (
                <div className="p-4 bg-white border-2 border-zinc-200 mb-3">
                  <SectionLabel className="mb-3">Sources</SectionLabel>
                  <GroundingSourceList
                    sources={execution.grounding_sources}
                    title=""
                  />
                </div>
              )}

              {/* Layer 3: METADATA (Collapsible - Change Summary, Current State) */}
              <CollapsibleSection
                title="Metadata"
                open={isExpanded}
                onOpenChange={setIsExpanded}
                variant="default"
              >
                <div className="space-y-3">
                  {execution.change_summary && (
                    <div className="p-3 bg-emerald-50 border border-emerald-200">
                      <p className="text-sm text-emerald-900 font-medium">
                        <span className="font-mono text-[10px] uppercase text-emerald-600 tracking-wider block mb-1">What Changed</span>
                        {execution.change_summary}
                      </p>
                    </div>
                  )}

                  {execution.result?.current_state && (
                    <div className="p-3 bg-zinc-900 border border-zinc-800">
                      <p className="text-[10px] font-mono uppercase text-zinc-500 tracking-wider mb-3">Current State (Dev)</p>
                      <div className="text-xs font-mono space-y-2">
                        {Object.entries(execution.result.current_state).map(
                          ([key, value]) => (
                            <div key={key} className="flex flex-col gap-1">
                              <span className="text-zinc-400">
                                {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                              </span>
                              {Array.isArray(value) ? (
                                value.length > 3 ? (
                                  <span className="text-zinc-300">{value.slice(0, 3).join(", ")} +{value.length - 3} more</span>
                                ) : (
                                  <span className="text-zinc-300">{value.join(", ")}</span>
                                )
                              ) : typeof value === "object" && value !== null ? (
                                <pre className="text-xs p-2 bg-zinc-950 text-zinc-400 border border-zinc-800 overflow-x-auto">
                                  {JSON.stringify(value, null, 2)}
                                </pre>
                              ) : (
                                <span className="text-zinc-300">{String(value)}</span>
                              )}
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </CollapsibleSection>

              {execution.error_message && (
                <div className="p-4 bg-red-50 border-2 border-red-200">
                  <SectionLabel className="mb-2 text-red-400">Error</SectionLabel>
                  <p className="text-sm text-red-600 font-mono">
                    {execution.error_message}
                  </p>
                </div>
              )}
          </BrutalistCard>
  );
};

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

  return (
    <div className="space-y-4">
      {executions.map((execution) => (
        <ExecutionCard
          key={execution.id}
          execution={execution}
          highlightNotifications={highlightNotifications}
        />
      ))}
    </div>
  );
};

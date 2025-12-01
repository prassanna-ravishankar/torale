import React from "react";
import ReactMarkdown from "react-markdown";
import { TaskExecution } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { GroundingSourceList } from "@/components/ui/GroundingSourceList";
import {
  CheckCircle2,
  XCircle,
  Clock,
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
      {executions.map((execution) => (
        <Card
          key={execution.id}
          className={
            highlightNotifications && execution.condition_met
              ? "border-2 border-emerald-500 bg-emerald-50/30"
              : "border-2"
          }
        >
          <div className="p-4">
            <div className="flex items-start gap-4">
              <div className="shrink-0 mt-1">{getStatusIcon(execution.status)}</div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
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
                    <Badge variant="default">
                      <AlertCircle className="mr-1 h-3 w-3" />
                      Condition Met
                    </Badge>
                  )}

                  <span className="text-sm text-muted-foreground ml-auto">
                    {formatDate(execution.started_at)}
                  </span>
                </div>

                {execution.change_summary && (
                  <div className="p-3 bg-zinc-50 border-2 border-zinc-100 mb-3">
                    <p className="text-sm">
                      <span className="font-mono text-[10px] uppercase text-zinc-400 tracking-wider block mb-1">What Changed</span>
                      {execution.change_summary}
                    </p>
                  </div>
                )}

                {execution.result?.answer && (
                  <div className="mb-3">
                    <div className="text-sm">
                      <ReactMarkdown
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
                        {execution.result.answer}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}

                {execution.result?.current_state && (
                  <div className="mb-3 p-3 bg-muted rounded-md">
                    <p className="text-sm font-medium mb-3">Current State:</p>
                    <div className="text-sm text-muted-foreground space-y-2">
                      {Object.entries(execution.result.current_state).map(
                        ([key, value]) => (
                          <div key={key}>
                            <span className="font-medium text-foreground">
                              {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}:
                            </span>{" "}
                            {Array.isArray(value) ? (
                              value.length > 3 ? (
                                <span className="text-xs">{value.slice(0, 3).join(", ")} and {value.length - 3} more</span>
                              ) : (
                                <span className="text-xs">{value.join(", ")}</span>
                              )
                            ) : typeof value === "object" && value !== null ? (
                              <pre className="text-xs mt-1 p-2 bg-background rounded overflow-x-auto">
                                {JSON.stringify(value, null, 2)}
                              </pre>
                            ) : (
                              <span className="text-xs">{String(value)}</span>
                            )}
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}

                <GroundingSourceList
                  sources={execution.grounding_sources}
                  title="Grounding Sources:"
                />

                {execution.error_message && (
                  <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                    <p className="text-sm text-destructive">
                      <span className="font-medium">Error: </span>
                      {execution.error_message}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};

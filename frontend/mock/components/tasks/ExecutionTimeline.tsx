import React from "react";
import { TaskExecution } from "../../types";
import { Badge } from "../ui/badge";
import { Card } from "../ui/card";
import {
  CheckCircle2,
  XCircle,
  Clock,
  ExternalLink,
  AlertCircle,
} from "lucide-react";
import { Button } from "../ui/button";

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
      {executions.map((execution, index) => (
        <Card
          key={execution.id}
          className={
            highlightNotifications && execution.condition_met
              ? "border-primary bg-primary/5"
              : ""
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
                  <div className="p-3 bg-muted rounded-md mb-3">
                    <p className="text-sm">
                      <span className="font-medium">What Changed: </span>
                      {execution.change_summary}
                    </p>
                  </div>
                )}

                {execution.result?.answer && (
                  <div className="mb-3">
                    <p className="text-sm mb-2">
                      <span className="font-medium">Answer: </span>
                      {execution.result.answer}
                    </p>
                  </div>
                )}

                {execution.result?.current_state && (
                  <div className="mb-3 p-3 bg-muted rounded-md">
                    <p className="text-sm mb-2">Current State:</p>
                    <div className="text-xs text-muted-foreground space-y-1">
                      {Object.entries(execution.result.current_state).map(
                        ([key, value]) => (
                          <div key={key}>
                            <span className="font-medium">{key}:</span>{" "}
                            {typeof value === "object"
                              ? JSON.stringify(value)
                              : String(value)}
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}

                {execution.grounding_sources.length > 0 && (
                  <div>
                    <p className="text-sm mb-2">Grounding Sources:</p>
                    <div className="space-y-2">
                      {execution.grounding_sources.map((source, idx) => (
                        <a
                          key={idx}
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-start gap-2 p-2 rounded-md hover:bg-muted transition-colors group"
                        >
                          <ExternalLink className="h-4 w-4 shrink-0 mt-0.5 text-muted-foreground group-hover:text-primary" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm group-hover:text-primary truncate">
                              {source.title}
                            </p>
                            <p className="text-xs text-muted-foreground truncate">
                              {source.url}
                            </p>
                          </div>
                        </a>
                      ))}
                    </div>
                  </div>
                )}

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

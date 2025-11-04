import React from "react";
import { TaskExecution } from "../../types";
import { Card } from "../ui/card";
import { ArrowRight, Info } from "lucide-react";
import { Alert } from "../ui/alert";

interface StateComparisonProps {
  executions: TaskExecution[];
}

export const StateComparison: React.FC<StateComparisonProps> = ({ executions }) => {
  const changedExecutions = executions.filter(
    (e) => e.change_summary || e.condition_met
  );

  if (changedExecutions.length === 0) {
    return (
      <div className="text-center py-12">
        <Info className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <h3 className="mb-2">No state changes detected</h3>
        <p className="text-muted-foreground">
          When the monitored information changes, you'll see a comparison here.
        </p>
      </div>
    );
  }

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
      <Alert>
        <Info className="h-4 w-4" />
        <div className="ml-2">
          <p className="text-sm">
            This view shows executions where the state changed or the trigger condition
            was met.
          </p>
        </div>
      </Alert>

      {changedExecutions.map((execution, index) => {
        const nextExecution = changedExecutions[index + 1];

        return (
          <Card key={execution.id} className="p-4">
            <div className="mb-3">
              <div className="flex items-center justify-between mb-2">
                <h3>{formatDate(execution.started_at)}</h3>
                {execution.condition_met && (
                  <span className="text-sm px-2 py-1 bg-primary text-primary-foreground rounded">
                    Condition Met
                  </span>
                )}
              </div>
              {execution.change_summary && (
                <p className="text-sm text-muted-foreground">{execution.change_summary}</p>
              )}
            </div>

            {execution.result?.current_state && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {nextExecution?.result?.current_state && (
                  <div className="space-y-2">
                    <p className="text-sm">Previous State:</p>
                    <div className="p-3 bg-muted rounded-md">
                      <div className="text-xs text-muted-foreground space-y-1">
                        {Object.entries(nextExecution.result.current_state).map(
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
                  </div>
                )}

                <div className="space-y-2">
                  <p className="text-sm">
                    {nextExecution?.result?.current_state ? "New State:" : "Current State:"}
                  </p>
                  <div className="p-3 bg-primary/10 border border-primary/20 rounded-md">
                    <div className="text-xs space-y-1">
                      {Object.entries(execution.result.current_state).map(
                        ([key, value]) => {
                          const previousValue =
                            nextExecution?.result?.current_state?.[key];
                          const hasChanged =
                            previousValue !== undefined &&
                            JSON.stringify(previousValue) !== JSON.stringify(value);

                          return (
                            <div
                              key={key}
                              className={hasChanged ? "font-medium text-primary" : ""}
                            >
                              <span className="font-medium">{key}:</span>{" "}
                              {typeof value === "object"
                                ? JSON.stringify(value)
                                : String(value)}
                              {hasChanged && (
                                <ArrowRight className="inline h-3 w-3 mx-1" />
                              )}
                            </div>
                          );
                        }
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {execution.result?.answer && (
              <div className="mt-3 p-3 bg-muted rounded-md">
                <p className="text-sm">{execution.result.answer}</p>
              </div>
            )}
          </Card>
        );
      })}
    </div>
  );
};

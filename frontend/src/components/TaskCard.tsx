import React from "react";
import type { Task } from "@/types";
import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  Clock,
  Search,
  ExternalLink,
  MoreVertical,
  Trash2,
  Play,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

interface TaskCardProps {
  task: Task;
  onToggle: (id: string, isActive: boolean) => void;
  onDelete: (id: string) => void;
  onExecute: (id: string) => void;
  onClick: (id: string) => void;
}

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onToggle,
  onDelete,
  onExecute,
  onClick,
}) => {
  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggle(task.id, !task.is_active);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm(`Are you sure you want to delete "${task.name}"?`)) {
      onDelete(task.id);
    }
  };

  const handleExecute = (e: React.MouseEvent) => {
    e.stopPropagation();
    onExecute(task.id);
  };

  return (
    <Card
      className="cursor-pointer hover:border-primary transition-colors"
      onClick={() => onClick(task.id)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="truncate">{task.name}</h3>
              {task.condition_met && (
                <Badge variant="default" className="shrink-0">
                  Triggered
                </Badge>
              )}
              {!task.is_active && (
                <Badge variant="secondary" className="shrink-0">
                  Paused
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {task.search_query}
            </p>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <Button variant="ghost" size="icon" className="shrink-0 ml-2">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleExecute}>
                <Play className="mr-2 h-4 w-4" />
                Run Now
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleDelete} className="text-destructive">
                <Trash2 className="mr-2 h-4 w-4" />
                Delete Task
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pb-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-4 w-4 shrink-0" />
          <span className="font-mono text-xs">{task.schedule}</span>
        </div>

        <div className="flex items-start gap-2 text-sm text-muted-foreground">
          <Search className="h-4 w-4 shrink-0 mt-0.5" />
          <span className="line-clamp-2">{task.condition_description}</span>
        </div>

        {task.condition_met && task.last_known_state && (
          <div className="p-2.5 bg-muted/50 rounded-md border border-muted">
            <p className="text-xs text-muted-foreground">
              📊 State captured - click "View Details" for full information
            </p>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex items-center justify-between pt-3 border-t">
        <div className="flex items-center gap-2">
          <Switch
            checked={task.is_active}
            onCheckedChange={() => onToggle(task.id, !task.is_active)}
            onClick={handleToggle}
          />
          <span className="text-sm text-muted-foreground">
            {task.is_active ? "Active" : "Paused"}
          </span>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onClick(task.id);
          }}
        >
          View Details
          <ExternalLink className="ml-2 h-3 w-3" />
        </Button>
      </CardFooter>
    </Card>
  );
};

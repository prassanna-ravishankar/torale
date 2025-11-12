export type TaskStatus = "pending" | "running" | "success" | "failed";
export type NotifyBehavior = "once" | "always" | "track_state";
export type ExecutorType = "llm_grounded_search";

export interface Task {
  id: string;
  name: string;
  schedule: string;
  executor_type: ExecutorType;
  search_query: string;
  condition_description: string;
  notify_behavior: NotifyBehavior;
  config: Record<string, any>;
  is_active: boolean;
  condition_met: boolean;
  last_known_state: Record<string, any> | null;
  last_notified_at: string | null;
  created_at: string;
  updated_at: string | null;
}

/**
 * Payload type for creating a new task.
 * Includes fields that are only used during creation and not returned in Task.
 */
export interface TaskCreatePayload {
  name: string;
  search_query: string;
  condition_description: string;
  schedule: string;
  notify_behavior: NotifyBehavior;
  executor_type: ExecutorType;
  config: Record<string, any>;
  is_active: boolean;
  run_immediately?: boolean;  // Execute task immediately after creation
  notifications?: any[];  // Notification configurations (optional)
}

export interface GroundingSource {
  url: string;
  title: string;
}

export interface TaskExecution {
  id: string;
  task_id: string;
  status: TaskStatus;
  started_at: string;
  completed_at: string | null;
  result: {
    answer: string;
    current_state: Record<string, any> | null;
  } | null;
  condition_met: boolean;
  change_summary: string | null;
  grounding_sources: GroundingSource[];
  error_message: string | null;
}

export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

export interface TaskTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  icon?: string;
  search_query: string;
  condition_description: string;
  schedule: string;
  notify_behavior: NotifyBehavior;
  config: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

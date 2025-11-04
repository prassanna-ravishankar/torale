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

export type TaskStatus = "pending" | "running" | "success" | "failed";
export type TaskState = "active" | "paused" | "completed";
export type NotifyBehavior = "once" | "always" | "track_state";
export type ExecutorType = "llm_grounded_search";
export type NotificationChannelType = "email" | "webhook";
export type NotificationDeliveryStatus = "success" | "failed" | "retrying";

/**
 * Embedded execution summary returned with tasks.
 * Subset of TaskExecution with only fields needed for status calculation.
 */
export interface TaskExecutionSummary {
  id: string;
  condition_met: boolean;
  started_at: string;
  completed_at: string | null;
  status: TaskStatus;
  result: Record<string, any> | null;
  change_summary: string | null;
  grounding_sources: GroundingSource[] | null;
}

export interface Task {
  id: string;
  name: string;
  schedule: string;
  executor_type: ExecutorType;
  search_query: string;
  condition_description: string;
  notify_behavior: NotifyBehavior;
  config: Record<string, any>;
  state: TaskState;

  // DEPRECATED: Use last_execution.condition_met instead (will be removed)
  condition_met: boolean;
  last_known_state: Record<string, any> | null;
  // DEPRECATED: Will be removed
  last_notified_at: string | null;

  // Latest execution reference (replaces sticky condition_met)
  last_execution_id: string | null;
  last_execution: TaskExecutionSummary | null;

  created_at: string;
  updated_at: string | null;
  // Notification channels
  notification_channels: NotificationChannelType[];
  notification_email: string | null;
  webhook_url: string | null;
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
  state: TaskState;
  run_immediately?: boolean;  // Execute task immediately after creation
  notifications?: NotificationConfig[];  // Notification configurations (optional)
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
  state: TaskState;
  created_at: string;
  updated_at: string | null;
}

/**
 * Response from the /api/v1/tasks/suggest endpoint
 * AI-generated task configuration from natural language
 */
export interface SuggestedTask {
  name: string;
  search_query: string;
  condition_description: string;
  schedule: string;
  notify_behavior: NotifyBehavior;
}

// Notification System Types

/**
 * Notification configuration for task creation
 * Matches backend NotificationConfig model
 */
export interface NotificationConfig {
  type: "email" | "webhook";
  // Email fields
  address?: string;
  template?: string;
  // Webhook fields
  url?: string;
  method?: string;
  headers?: Record<string, string>;
}

/**
 * Simplified notification channel for UI selection
 */
export interface NotificationChannel {
  type: NotificationChannelType;
  email?: string; // For email channel
  webhookUrl?: string; // For webhook channel
  useDefault?: boolean; // Use user-level defaults
}

/**
 * User-level webhook configuration
 */
export interface WebhookConfig {
  url: string | null;
  secret: string | null;
  enabled: boolean;
}

/**
 * Email verification state
 */
export interface EmailVerification {
  email: string;
  code: string;
  expiresAt: string;
  attemptsLeft: number;
}

/**
 * Webhook delivery record
 */
export interface WebhookDelivery {
  id: string;
  task_id: string;
  execution_id: string;
  webhook_url: string;
  status: NotificationDeliveryStatus;
  http_status_code: number | null;
  response_body: string | null;
  error_message: string | null;
  attempts: number;
  next_retry_at: string | null;
  created_at: string;
  updated_at: string | null;
}

/**
 * Email notification send record
 */
export interface NotificationSend {
  id: string;
  user_id: string;
  task_id: string;
  execution_id: string;
  notification_type: NotificationChannelType;
  recipient: string; // email address or webhook URL
  status: NotificationDeliveryStatus;
  error_message: string | null;
  created_at: string;
}

/**
 * User with verified emails (for settings page)
 */
export interface UserWithNotifications extends User {
  verified_notification_emails: string[];
  webhook_url: string | null;
  webhook_secret: string | null;
  webhook_enabled: boolean;
}

/**
 * API Key for CLI authentication
 */
export interface ApiKey {
  id: string;
  user_id: string;
  key_prefix: string;
  name: string;
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
}

/**
 * API Key creation response (includes full key once)
 */
export interface CreateApiKeyResponse {
  key: string; // Full key shown only once
  key_info: ApiKey;
}

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { useApi } from "@/hooks/useApi";
import { cn, getErrorMessage, getTaskShareUrl } from "@/lib/utils";
import type { Task } from "@/types";
import { Switch } from "@/components/torale";
import { ConnectorPickerSection } from "@/components/connectors/ConnectorPickerSection";
import styles from "./composer/Composer.module.css";
import modalStyles from "./ui/modal/Modal.module.css";
import landing from "./landing/Landing.module.css";

interface TaskEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task: Task | null;
  onSuccess: (task: Task) => void;
}

const MIN_INSTRUCTIONS_LENGTH = 10;

export const TaskEditDialog: React.FC<TaskEditDialogProps> = ({
  open,
  onOpenChange,
  task,
  onSuccess,
}) => {
  const api = useApi();
  const [name, setName] = useState("");
  const [condition, setCondition] = useState("");
  const [attachedConnectors, setAttachedConnectors] = useState<string[]>([]);
  const [isPublic, setIsPublic] = useState(false);
  const [isTogglingVisibility, setIsTogglingVisibility] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (task && open) {
      setName(task.name);
      setCondition(task.search_query || "");
      setIsPublic(task.is_public);
      setAttachedConnectors(task.attached_connector_slugs ?? []);
    }
  }, [task, open]);

  useEffect(() => {
    if (!open) setError("");
  }, [open]);

  const handleVisibilityToggle = async (checked: boolean) => {
    if (!task) return;
    setIsTogglingVisibility(true);
    try {
      const result = await api.updateTaskVisibility(task.id, checked);
      setIsPublic(result.is_public);
      toast.success(result.is_public ? "watch is now public" : "watch is now private");
      onSuccess({ ...task, is_public: result.is_public });
    } catch (err) {
      console.error("Failed to toggle visibility:", err);
      toast.error("failed to update visibility");
    } finally {
      setIsTogglingVisibility(false);
    }
  };

  const copyShareUrl = () => {
    if (!task) return;
    navigator.clipboard.writeText(getTaskShareUrl(task.id));
    toast.success("link copied");
  };

  const handleUpdate = async () => {
    if (!task) return;
    const trimmedCondition = condition.trim();
    if (!trimmedCondition || trimmedCondition.length < MIN_INSTRUCTIONS_LENGTH) {
      toast.error("describe what to watch for");
      return;
    }

    setError("");
    setSubmitting(true);
    try {
      const updated = await api.updateTask(task.id, {
        name: name.trim() || trimmedCondition.slice(0, 60),
        search_query: trimmedCondition,
        condition_description: trimmedCondition,
        attached_connector_slugs: attachedConnectors,
      });
      toast.success("watch updated");
      onSuccess(updated);
      onOpenChange(false);
    } catch (err) {
      console.error("Failed to update task:", err);
      const msg = getErrorMessage(err, "failed to update watch");
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (!task) return null;

  const canSubmit = condition.trim().length > 0 && !submitting;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={modalStyles.modal}>
        <DialogTitle className="sr-only">Edit watch</DialogTitle>
        <DialogDescription className="sr-only">
          Edit the condition and visibility for this watch.
        </DialogDescription>

        <div className={modalStyles.head}>
          <span className={modalStyles.headTitle}>edit watch · plain english · no rules</span>
          <button
            type="button"
            className={modalStyles.headClose}
            onClick={() => onOpenChange(false)}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className={modalStyles.body}>
          <div className={styles.conditionLabel}>The condition</div>
          <textarea
            className={cn(styles.conditionInput, "posthog-no-capture")}
            value={condition}
            onChange={(e) => setCondition(e.target.value)}
            disabled={submitting}
            autoFocus
          />

          <div className={styles.row2}>
            <div className={styles.field}>
              <label htmlFor="watch-name">Name (optional)</label>
              <input
                id="watch-name"
                type="text"
                value={name}
                placeholder="auto from condition"
                onChange={(e) => setName(e.target.value)}
                disabled={submitting}
              />
            </div>
            <div className={cn(styles.field, styles.toggleField)}>
              <label htmlFor="watch-public">{isPublic ? "Public" : "Private"}</label>
              <Switch
                id="watch-public"
                checked={isPublic}
                onCheckedChange={handleVisibilityToggle}
                disabled={isTogglingVisibility}
              />
            </div>
          </div>

          {isPublic && (
            <div className={styles.shareInfo}>
              <div className={styles.shareLink}>
                <span>{getTaskShareUrl(task.id)}</span>
                <button
                  type="button"
                  className={styles.shareLinkBtn}
                  onClick={copyShareUrl}
                  aria-label="Copy share link"
                >
                  copy
                </button>
              </div>
              {(task.view_count > 0 || task.subscriber_count > 0) && (
                <div className={styles.shareStats}>
                  <span>{task.view_count} views</span>
                  <span>{task.subscriber_count} forks</span>
                </div>
              )}
            </div>
          )}

          <div className={styles.connectorBlock}>
            <ConnectorPickerSection
              selected={attachedConnectors}
              onChange={setAttachedConnectors}
              disabled={submitting}
            />
          </div>

          {error && <div className={styles.error}>{error}</div>}
        </div>

        <div className={modalStyles.foot}>
          <span className={modalStyles.footHint}>
            the agent decides cadence + when to notify
          </span>
          <div className={modalStyles.footActions}>
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              disabled={submitting}
              className={cn(landing.btn, landing.btnSecondary)}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleUpdate}
              disabled={!canSubmit}
              className={cn(landing.btn, landing.btnPrimary)}
            >
              {submitting ? "Saving…" : "Save →"}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

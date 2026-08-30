import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { ConnectorPickerSection } from "@/components/connectors/ConnectorPickerSection";
import type { Task } from "@/types";
import { useApi } from "@/hooks/useApi";
import { toast } from "sonner";
import { cn, getErrorMessage } from "@/lib/utils";
import styles from "./composer/Composer.module.css";
import modalStyles from "./ui/modal/Modal.module.css";
import landing from "./landing/Landing.module.css";
import { WebwhenMark } from "./WebwhenMark";

const STARTING_ANIM_MS = 2400;

interface TaskCreationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskCreated: (task: Task) => void;
}

const MIN_INSTRUCTIONS_LENGTH = 10;

export const TaskCreationDialog: React.FC<TaskCreationDialogProps> = ({
  open,
  onOpenChange,
  onTaskCreated,
}) => {
  const api = useApi();
  const [condition, setCondition] = useState("");
  const [attachedConnectors, setAttachedConnectors] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) {
      setCondition("");
      setAttachedConnectors([]);
      setError("");
    }
  }, [open]);

  const handleSubmit = async () => {
    const trimmed = condition.trim();
    if (!trimmed) {
      toast.error("describe what to watch for");
      return;
    }
    if (trimmed.length < MIN_INSTRUCTIONS_LENGTH) {
      toast.error("a little more detail, please");
      return;
    }

    setError("");
    setSubmitting(true);

    const animStart = performance.now();
    try {
      // Backend/agent derives the name from the condition; no explicit name field.
      const newTask = await api.createTask({
        search_query: trimmed,
        condition_description: trimmed,
        state: "active",
        run_immediately: true,
        attached_connector_slugs: attachedConnectors,
      });

      // Let the starting animation complete before the modal closes.
      // The agent is "patient and watchful" — match that with the brand mark.
      const elapsed = performance.now() - animStart;
      const remaining = Math.max(0, STARTING_ANIM_MS - elapsed);
      if (remaining > 0) {
        await new Promise((r) => setTimeout(r, remaining));
      }

      onTaskCreated(newTask);
      onOpenChange(false);
    } catch (err) {
      const msg = getErrorMessage(err, "failed to create watch");
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const canSubmit = condition.trim().length > 0 && !submitting;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={modalStyles.modal}>
        {/* Visually-hidden title/description for a11y (Radix requires DialogTitle) */}
        <DialogTitle className="sr-only">New watch</DialogTitle>
        <DialogDescription className="sr-only">
          Describe the condition you want to watch for in plain English.
        </DialogDescription>

        <div className={modalStyles.head}>
          <span className={modalStyles.headTitle}>new watch · plain english · no rules</span>
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
            placeholder="Tell me when the next iPhone release date is announced."
            value={condition}
            onChange={(e) => setCondition(e.target.value)}
            disabled={submitting}
            autoFocus
          />

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
              onClick={handleSubmit}
              disabled={!canSubmit}
              className={cn(landing.btn, landing.btnPrimary)}
            >
              {submitting ? (
                <span className={styles.submittingMark}>
                  <WebwhenMark animated="starting" oneShot size={18} />
                  watching
                </span>
              ) : (
                "Watch →"
              )}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

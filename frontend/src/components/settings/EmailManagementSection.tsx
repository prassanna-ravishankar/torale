import React, { useState, useEffect, useCallback } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Loader2, Mail, Plus, Trash2 } from 'lucide-react';
import { useApi } from '@/hooks/useApi';
import { getErrorMessage } from '@/lib/utils';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import { EmailVerificationModal } from './EmailVerificationModal';
import { StatusBadge } from '@/components/torale';
import styles from './Settings.module.css';

export const EmailManagementSection: React.FC = () => {
  const api = useApi();
  const { user } = useAuth();
  const clerkEmail = user?.email;

  const [verifiedEmails, setVerifiedEmails] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [showVerificationModal, setShowVerificationModal] = useState(false);
  const [emailToDelete, setEmailToDelete] = useState<string | null>(null);

  const loadVerifiedEmails = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.getVerifiedEmails();
      setVerifiedEmails(response.verified_emails || []);
    } catch (err) {
      toast.error('Failed to load verified emails');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [api]);

  useEffect(() => {
    void loadVerifiedEmails();
  }, [loadVerifiedEmails]);

  const handleEmailVerified = (email: string) => {
    setVerifiedEmails((prev) => [...prev, email]);
  };

  const handleDeleteClick = (email: string) => {
    setEmailToDelete(email);
  };

  const handleConfirmDelete = async () => {
    if (!emailToDelete) return;

    setIsDeleting(emailToDelete);
    try {
      await api.removeVerifiedEmail(emailToDelete);
      setVerifiedEmails((prev) => prev.filter((e) => e !== emailToDelete));
      toast.success('Email removed successfully');
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to remove email'));
    } finally {
      setIsDeleting(null);
      setEmailToDelete(null);
    }
  };

  const handleAddEmailClick = () => {
    setShowVerificationModal(true);
  };

  const customEmails = verifiedEmails.filter((email) => email !== clerkEmail);

  return (
    <>
      {isLoading ? (
        <div className={styles.loadingRow}>
          <Loader2 className="h-4 w-4 animate-spin" />
          loading…
        </div>
      ) : (
        <>
          <div className={styles.runs}>
            {/* Clerk default email row */}
            {clerkEmail && (
              <div className={styles.run}>
                <span className={styles.runT}>account</span>
                <span className={`${styles.runDot} ${styles.runDotEmber}`} />
                <span className={`${styles.runB} ${styles.runBStrong}`}>{clerkEmail}</span>
                <span className="flex items-center gap-1.5">
                  <StatusBadge variant="success" label="Verified" size="sm" />
                  <StatusBadge variant="triggered" label="Default" size="sm" />
                </span>
              </div>
            )}

            {/* Custom verified emails */}
            {customEmails.map((email) => (
              <div key={email} className={styles.run}>
                <span className={styles.runT}>custom</span>
                <span className={`${styles.runDot} ${styles.runDotSuccess}`} />
                <span className={styles.runB}>{email}</span>
                <span className="flex items-center gap-1.5">
                  <StatusBadge variant="success" label="Verified" size="sm" />
                  <button
                    onClick={() => handleDeleteClick(email)}
                    disabled={isDeleting === email}
                    className={`${styles.iconBtn} ${styles.iconBtnDanger}`}
                    aria-label={`Remove ${email}`}
                  >
                    {isDeleting === email ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </button>
                </span>
              </div>
            ))}
          </div>

          {customEmails.length === 0 && (
            <div className={styles.emptyHint} style={{ marginTop: 12 }}>
              No custom emails yet. Add one to receive notifications at a different address.
            </div>
          )}

          <div className={styles.actions} style={{ marginTop: 16, justifyContent: 'flex-start' }}>
            <button
              type="button"
              onClick={handleAddEmailClick}
              className={styles.btnSecondary}
            >
              <Plus className="h-3.5 w-3.5" />
              Add email
            </button>
          </div>
        </>
      )}

      {/* Email Verification Modal */}
      <EmailVerificationModal
        open={showVerificationModal}
        onOpenChange={setShowVerificationModal}
        onVerified={handleEmailVerified}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!emailToDelete} onOpenChange={() => setEmailToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              <Mail className="inline h-4 w-4 mr-2" style={{ color: 'var(--ww-ink-3)' }} />
              Remove email?
            </AlertDialogTitle>
            <AlertDialogDescription>
              Remove <strong className="font-mono">{emailToDelete}</strong>? Watches configured to
              use this email will fall back to your account email.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className={styles.btnSecondary}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className={styles.btnDanger}
            >
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

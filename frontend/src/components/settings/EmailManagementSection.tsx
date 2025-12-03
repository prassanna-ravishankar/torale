import React, { useState, useEffect } from 'react';
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
import { Loader2, Mail, Plus, Trash2, CheckCircle2 } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import { EmailVerificationModal } from './EmailVerificationModal';
import { SectionLabel, BrutalistCard, StatusBadge } from '@/components/torale';

export const EmailManagementSection: React.FC = () => {
  const { user } = useAuth();
  const clerkEmail = user?.email;

  const [verifiedEmails, setVerifiedEmails] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [showVerificationModal, setShowVerificationModal] = useState(false);
  const [emailToDelete, setEmailToDelete] = useState<string | null>(null);

  useEffect(() => {
    loadVerifiedEmails();
  }, []);

  const loadVerifiedEmails = async () => {
    setIsLoading(true);
    try {
      const response = await api.getVerifiedEmails();
      setVerifiedEmails(response.verified_emails || []);
    } catch (err: any) {
      toast.error('Failed to load verified emails');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

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
    } catch (err: any) {
      toast.error(err.message || 'Failed to remove email');
    } finally {
      setIsDeleting(null);
      setEmailToDelete(null);
    }
  };

  const handleAddEmailClick = () => {
    setShowVerificationModal(true);
  };

  return (
    <>
      <BrutalistCard>
        {/* Header */}
        <div className="p-4 border-b border-zinc-200">
          <p className="text-xs text-zinc-500">
            Manage email addresses for task notifications. Your account email is always verified.
          </p>
        </div>

        {/* Content */}
        <div className="p-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-zinc-400" />
            </div>
          ) : (
            <div className="space-y-2">
              {/* Clerk Email (Always Verified) */}
              {clerkEmail && (
                <div className="p-3 bg-zinc-50 border border-zinc-200">
                  <div className="flex items-start gap-3">
                    <div className="bg-zinc-900 text-white w-8 h-8 flex items-center justify-center shrink-0">
                      <Mail className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs sm:text-sm font-mono text-zinc-900 break-all">{clerkEmail}</p>
                      <SectionLabel className="mt-0.5">Account Email</SectionLabel>
                      <div className="flex flex-wrap items-center gap-1.5 mt-2">
                        <StatusBadge variant="active" label="Verified" size="sm" />
                        <span className="px-1.5 py-0.5 bg-zinc-900 text-white text-[9px] font-mono uppercase tracking-wider">
                          Default
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Custom Verified Emails */}
              {verifiedEmails.filter(email => email !== clerkEmail).map((email) => (
                <div key={email} className="p-3 border border-zinc-200 hover:border-zinc-300 transition-colors">
                  <div className="flex items-start gap-3">
                    <div className="bg-zinc-100 w-8 h-8 flex items-center justify-center shrink-0">
                      <Mail className="h-4 w-4 text-zinc-600" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="text-xs sm:text-sm font-mono text-zinc-900 break-all">{email}</p>
                          <SectionLabel className="mt-0.5">Custom Email</SectionLabel>
                        </div>
                        <button
                          onClick={() => handleDeleteClick(email)}
                          disabled={isDeleting === email}
                          className="p-1.5 text-zinc-400 hover:text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50 shrink-0"
                        >
                          {isDeleting === email ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                      <div className="flex flex-wrap items-center gap-1.5 mt-2">
                        <StatusBadge variant="active" label="Verified" size="sm" />
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {/* No Custom Emails Message */}
              {verifiedEmails.filter(email => email !== clerkEmail).length === 0 && (
                <div className="p-3 bg-zinc-50 border border-dashed border-zinc-300 text-center">
                  <p className="text-xs text-zinc-500 font-mono">
                    No custom emails. Add one to receive notifications at a different address.
                  </p>
                </div>
              )}

              {/* Add Email Button */}
              <button
                onClick={handleAddEmailClick}
                className="w-full flex items-center justify-center gap-2 p-3 border-2 border-dashed border-zinc-300 text-zinc-500 hover:border-zinc-900 hover:text-zinc-900 hover:bg-zinc-50 transition-all text-sm font-mono"
              >
                <Plus className="h-4 w-4" />
                Add Email
              </button>
            </div>
          )}
        </div>
      </BrutalistCard>

      {/* Email Verification Modal */}
      <EmailVerificationModal
        open={showVerificationModal}
        onOpenChange={setShowVerificationModal}
        onVerified={handleEmailVerified}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!emailToDelete} onOpenChange={() => setEmailToDelete(null)}>
        <AlertDialogContent className="border-2 border-zinc-900">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-grotesk">Remove Email Address?</AlertDialogTitle>
            <AlertDialogDescription className="text-zinc-600">
              Are you sure you want to remove <strong className="font-mono">{emailToDelete}</strong>? Tasks configured to
              use this email will fall back to your account email.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="font-mono text-sm">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-red-600 hover:bg-red-700 font-mono text-sm"
            >
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

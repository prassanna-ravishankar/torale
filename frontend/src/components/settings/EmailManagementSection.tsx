import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
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
import { Loader2, Mail, Plus, Trash2, CheckCircle2, AlertCircle, Clock } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { useUser } from '@clerk/clerk-react';
import { EmailVerificationModal } from './EmailVerificationModal';

export const EmailManagementSection: React.FC = () => {
  const { user: clerkUser } = useUser();
  const clerkEmail = clerkUser?.primaryEmailAddress?.emailAddress;

  const [verifiedEmails, setVerifiedEmails] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [showVerificationModal, setShowVerificationModal] = useState(false);
  const [emailToDelete, setEmailToDelete] = useState<string | null>(null);
  const [rateLimitInfo, setRateLimitInfo] = useState<string>('');

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
    setRateLimitInfo('');
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
    // Check rate limit info
    const recentVerifications = verifiedEmails.length;
    if (recentVerifications >= 3) {
      setRateLimitInfo('You can verify up to 3 emails per hour. Please try again later.');
      return;
    }
    setShowVerificationModal(true);
  };

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Email Addresses</CardTitle>
          <CardDescription>
            Manage email addresses that can receive task notifications. Your Clerk email is always
            verified and cannot be removed.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="space-y-3">
              {/* Clerk Email (Always Verified) */}
              {clerkEmail && (
                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-full bg-primary/10 p-2">
                      <Mail className="h-4 w-4 text-primary" />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-medium">{clerkEmail}</span>
                      <span className="text-sm text-muted-foreground">Clerk Account Email</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="gap-1">
                      <CheckCircle2 className="h-3 w-3" />
                      Verified
                    </Badge>
                    <Badge variant="outline">Default</Badge>
                  </div>
                </div>
              )}

              {/* Custom Verified Emails */}
              {verifiedEmails.filter(email => email !== clerkEmail).map((email) => (
                <div key={email} className="flex items-center justify-between rounded-lg border p-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-full bg-secondary p-2">
                      <Mail className="h-4 w-4" />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-medium">{email}</span>
                      <span className="text-sm text-muted-foreground">Custom Email</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="gap-1">
                      <CheckCircle2 className="h-3 w-3" />
                      Verified
                    </Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteClick(email)}
                      disabled={isDeleting === email}
                    >
                      {isDeleting === email ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              ))}

              {/* No Custom Emails Message */}
              {verifiedEmails.filter(email => email !== clerkEmail).length === 0 && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    No custom emails added yet. Click "Add Email" to verify a custom notification
                    address.
                  </AlertDescription>
                </Alert>
              )}

              {/* Rate Limit Warning */}
              {rateLimitInfo && (
                <Alert variant="destructive">
                  <Clock className="h-4 w-4" />
                  <AlertDescription>{rateLimitInfo}</AlertDescription>
                </Alert>
              )}

              {/* Add Email Button */}
              <Button onClick={handleAddEmailClick} variant="outline" className="w-full">
                <Plus className="mr-2 h-4 w-4" />
                Add Email
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

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
            <AlertDialogTitle>Remove Email Address?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove <strong>{emailToDelete}</strong>? Tasks configured to
              use this email will fall back to your Clerk email.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete}>Remove Email</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

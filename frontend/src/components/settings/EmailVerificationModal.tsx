import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from '@/components/ui/input-otp';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Mail, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';

interface EmailVerificationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onVerified: (email: string) => void;
}

type Step = 'enter_email' | 'verify_code';

export const EmailVerificationModal: React.FC<EmailVerificationModalProps> = ({
  open,
  onOpenChange,
  onVerified,
}) => {
  const [step, setStep] = useState<Step>('enter_email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [expiresAt, setExpiresAt] = useState<Date | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(0);

  // Countdown timer for code expiration
  useEffect(() => {
    if (!expiresAt) return;

    const interval = setInterval(() => {
      const remaining = Math.floor((expiresAt.getTime() - Date.now()) / 1000);
      setTimeRemaining(Math.max(0, remaining));

      if (remaining <= 0) {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [expiresAt]);

  // Reset state when modal closes
  useEffect(() => {
    if (!open) {
      setStep('enter_email');
      setEmail('');
      setCode('');
      setError('');
      setExpiresAt(null);
      setTimeRemaining(0);
    }
  }, [open]);

  const handleSendCode = async () => {
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await api.sendVerificationCode(email);
      setExpiresAt(new Date(response.expires_at));
      setStep('verify_code');
      toast.success('Verification code sent to ' + email);
    } catch (err: any) {
      setError(err.message || 'Failed to send verification code');
      toast.error(err.message || 'Failed to send verification code');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    if (code.length !== 6) {
      setError('Please enter the 6-digit code');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await api.verifyEmailCode(email, code);
      toast.success('Email verified successfully!');
      onVerified(email);
      onOpenChange(false);
    } catch (err: any) {
      setError(err.message || 'Invalid verification code');
      toast.error(err.message || 'Invalid verification code');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async () => {
    setCode('');
    setError('');
    await handleSendCode();
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Verify Email Address
          </DialogTitle>
          <DialogDescription>
            {step === 'enter_email'
              ? 'Add a custom email address to receive notifications'
              : 'Enter the 6-digit code sent to your email'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {step === 'enter_email' && (
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSendCode();
                  }
                }}
                disabled={isLoading}
                autoFocus
              />
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              <p className="text-sm text-muted-foreground">
                You'll receive a 6-digit verification code valid for 15 minutes
              </p>
            </div>
          )}

          {step === 'verify_code' && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Verification Code</Label>
                <div className="flex justify-center">
                  <InputOTP
                    maxLength={6}
                    value={code}
                    onChange={(value) => {
                      setCode(value);
                      setError('');
                    }}
                    disabled={isLoading || timeRemaining === 0}
                  >
                    <InputOTPGroup>
                      <InputOTPSlot index={0} />
                      <InputOTPSlot index={1} />
                      <InputOTPSlot index={2} />
                      <InputOTPSlot index={3} />
                      <InputOTPSlot index={4} />
                      <InputOTPSlot index={5} />
                    </InputOTPGroup>
                  </InputOTP>
                </div>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  Code sent to <strong>{email}</strong>
                </span>
                <Button
                  type="button"
                  variant="link"
                  size="sm"
                  onClick={() => setStep('enter_email')}
                  className="h-auto p-0"
                >
                  Change email
                </Button>
              </div>

              {timeRemaining > 0 ? (
                <Alert>
                  <CheckCircle2 className="h-4 w-4" />
                  <AlertDescription>
                    Code expires in <strong>{formatTime(timeRemaining)}</strong>
                  </AlertDescription>
                </Alert>
              ) : (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Verification code has expired
                  </AlertDescription>
                </Alert>
              )}

              {timeRemaining === 0 && (
                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
                  onClick={handleResendCode}
                  disabled={isLoading}
                >
                  {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Resend Code
                </Button>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          {step === 'enter_email' ? (
            <>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                onClick={handleSendCode}
                disabled={isLoading || !email}
              >
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Send Code
              </Button>
            </>
          ) : (
            <>
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep('enter_email')}
                disabled={isLoading}
              >
                Back
              </Button>
              <Button
                type="button"
                onClick={handleVerifyCode}
                disabled={isLoading || code.length !== 6 || timeRemaining === 0}
              >
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Verify Email
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

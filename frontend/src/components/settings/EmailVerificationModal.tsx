import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from '@/components/ui/input-otp';
import { Loader2, AlertCircle } from 'lucide-react';
import { useApi } from '@/hooks/useApi';
import { getErrorMessage } from '@/lib/utils';
import { toast } from 'sonner';
import settingsStyles from './Settings.module.css';
import modalStyles from '@/components/ui/modal/Modal.module.css';

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
  const api = useApi();
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
    } catch (err) {
      const message = getErrorMessage(err, 'Failed to send verification code');
      setError(message);
      toast.error(message);
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
    } catch (err) {
      const message = getErrorMessage(err, 'Invalid verification code');
      setError(message);
      toast.error(message);
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

  const headTitle = step === 'enter_email' ? 'verify email' : 'enter code';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={modalStyles.modal}>
        <DialogTitle className="sr-only">Verify email address</DialogTitle>
        <DialogDescription className="sr-only">
          {step === 'enter_email'
            ? 'Add a custom email address to receive notifications'
            : 'Enter the 6-digit code sent to your email'}
        </DialogDescription>

        <div className={modalStyles.head}>
          <span className={modalStyles.headTitle}>{headTitle}</span>
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
          {step === 'enter_email' && (
            <div className="flex flex-col gap-3">
              <div className={settingsStyles.field}>
                <label htmlFor="verify-email">Email address</label>
                <input
                  id="verify-email"
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
              </div>
              {error && (
                <div
                  className="flex items-start gap-2 p-2 rounded-sm"
                  style={{
                    background: 'var(--ww-danger-soft)',
                    color: 'var(--ww-danger)',
                    fontFamily: 'var(--ww-font-mono)',
                    fontSize: '11px',
                  }}
                >
                  <AlertCircle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                  {error}
                </div>
              )}
              <p
                style={{
                  fontFamily: 'var(--ww-font-mono)',
                  fontSize: '11px',
                  color: 'var(--ww-ink-4)',
                }}
              >
                You'll receive a 6-digit verification code valid for 15 minutes.
              </p>
            </div>
          )}

          {step === 'verify_code' && (
            <div className="flex flex-col gap-4">
              <div className={settingsStyles.field}>
                <label>Verification code</label>
                <div className="flex justify-center pt-1">
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
                <div
                  className="flex items-start gap-2 p-2 rounded-sm"
                  style={{
                    background: 'var(--ww-danger-soft)',
                    color: 'var(--ww-danger)',
                    fontFamily: 'var(--ww-font-mono)',
                    fontSize: '11px',
                  }}
                >
                  <AlertCircle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                  {error}
                </div>
              )}

              <div
                className="flex items-center justify-between"
                style={{
                  fontFamily: 'var(--ww-font-mono)',
                  fontSize: '11px',
                  color: 'var(--ww-ink-4)',
                }}
              >
                <span>
                  sent to <strong style={{ color: 'var(--ww-ink-2)' }}>{email}</strong>
                </span>
                <button
                  type="button"
                  onClick={() => setStep('enter_email')}
                  className={settingsStyles.btnGhost}
                  style={{ padding: '4px 8px' }}
                >
                  Change email
                </button>
              </div>

              {timeRemaining > 0 ? (
                <p
                  style={{
                    fontFamily: 'var(--ww-font-mono)',
                    fontSize: '11px',
                    color: 'var(--ww-ink-4)',
                  }}
                >
                  Code expires in <strong style={{ color: 'var(--ww-ink-2)' }}>{formatTime(timeRemaining)}</strong>
                </p>
              ) : (
                <div
                  className="flex items-start gap-2 p-2 rounded-sm"
                  style={{
                    background: 'var(--ww-danger-soft)',
                    color: 'var(--ww-danger)',
                    fontFamily: 'var(--ww-font-mono)',
                    fontSize: '11px',
                  }}
                >
                  <AlertCircle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                  Verification code has expired
                </div>
              )}

              {timeRemaining === 0 && (
                <button
                  type="button"
                  className={settingsStyles.btnSecondary}
                  onClick={handleResendCode}
                  disabled={isLoading}
                  style={{ alignSelf: 'flex-start' }}
                >
                  {isLoading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  Resend code
                </button>
              )}
            </div>
          )}
        </div>

        <div className={modalStyles.foot}>
          <span className={modalStyles.footHint}>
            {step === 'enter_email' ? 'one-time code · 15 min validity' : 'enter the 6-digit code'}
          </span>
          <div className={modalStyles.footActions}>
            {step === 'enter_email' ? (
              <>
                <button
                  type="button"
                  className={settingsStyles.btnGhost}
                  onClick={() => onOpenChange(false)}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className={settingsStyles.btnPrimary}
                  onClick={handleSendCode}
                  disabled={isLoading || !email}
                >
                  {isLoading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  Send code
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  className={settingsStyles.btnGhost}
                  onClick={() => setStep('enter_email')}
                  disabled={isLoading}
                >
                  Back
                </button>
                <button
                  type="button"
                  className={settingsStyles.btnPrimary}
                  onClick={handleVerifyCode}
                  disabled={isLoading || code.length !== 6 || timeRemaining === 0}
                >
                  {isLoading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  Verify
                </button>
              </>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

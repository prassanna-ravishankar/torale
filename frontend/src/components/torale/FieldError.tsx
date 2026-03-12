import React from 'react';
import { AlertCircle } from 'lucide-react';

interface FieldErrorProps {
  message?: string;
}

export const FieldError: React.FC<FieldErrorProps> = ({ message }) => {
  if (!message) return null;
  return (
    <p className="text-xs text-destructive flex items-center gap-1.5">
      <AlertCircle className="h-3 w-3" />
      {message}
    </p>
  );
};

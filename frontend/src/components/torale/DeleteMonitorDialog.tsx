import React from 'react';
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

interface DeleteMonitorDialogProps {
  taskName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  extraDescription?: string;
}

export const DeleteMonitorDialog: React.FC<DeleteMonitorDialogProps> = ({
  taskName,
  open,
  onOpenChange,
  onConfirm,
  extraDescription,
}) => (
  <AlertDialog open={open} onOpenChange={onOpenChange}>
    <AlertDialogContent className="border-2 border-zinc-900 shadow-brutalist-lg">
      <AlertDialogHeader className="border-b-2 border-zinc-100 pb-4">
        <AlertDialogTitle className="font-grotesk">Delete Monitor</AlertDialogTitle>
        <AlertDialogDescription className="text-zinc-500">
          Are you sure you want to delete "{taskName}"? This action cannot be undone.{extraDescription ? ` ${extraDescription}` : ''}
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter className="gap-3">
        <AlertDialogCancel>Cancel</AlertDialogCancel>
        <AlertDialogAction onClick={onConfirm} className="shadow-brutalist">
          Delete
        </AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
);

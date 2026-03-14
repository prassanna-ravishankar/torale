import React from 'react';
import {
  Sheet,
  SheetContent,
} from '@/components/ui/sheet';
import {
  Drawer,
  DrawerContent,
} from '@/components/ui/drawer';
import { useIsMobile } from '@/components/ui/use-mobile';
import { TaskDetail } from './TaskDetail';

interface TaskDetailOverlayProps {
  taskId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentUserId?: string;
  onDeleted?: () => void;
}

export const TaskDetailOverlay: React.FC<TaskDetailOverlayProps> = ({
  taskId,
  open,
  onOpenChange,
  currentUserId,
  onDeleted,
}) => {
  const isMobile = useIsMobile();

  if (!taskId) return null;

  const content = (
    <div className="flex-1 overflow-y-auto pt-8">
      <TaskDetail
        taskId={taskId}
        onBack={() => onOpenChange(false)}
        onDeleted={() => {
          onOpenChange(false);
          onDeleted?.();
        }}
        currentUserId={currentUserId}
        compact={true}
      />
    </div>
  );

  if (isMobile) {
    return (
      <Drawer open={open} onOpenChange={onOpenChange}>
        <DrawerContent className="h-[90vh]">
          {content}
        </DrawerContent>
      </Drawer>
    );
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="sm:max-w-xl w-full p-0 flex flex-col">
        {content}
      </SheetContent>
    </Sheet>
  );
};

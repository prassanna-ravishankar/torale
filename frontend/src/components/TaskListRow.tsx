import React, { useState } from 'react';
import { motion, AnimatePresence } from '@/lib/motion-compat';
import type { Task } from '@/types';
import { StatusBadge } from '@/components/torale';
import { CronDisplay } from '@/components/ui/CronDisplay';
import { Button } from '@/components/ui/button';
import { getTaskStatus } from '@/lib/taskStatus';
import { formatTimeAgo } from '@/lib/utils';
import {
  Play,
  Pause,
  Settings,
  Trash2,
  ChevronRight,
  Clock,
} from 'lucide-react';
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

interface TaskListRowProps {
  task: Task;
  onToggle: (id: string, newState: 'active' | 'paused') => void;
  onDelete: (id: string) => void;
  onExecute: (id: string) => void;
  onEdit: (id: string) => void;
  onClick: (id: string) => void;
}

export const TaskListRow: React.FC<TaskListRowProps> = ({
  task,
  onToggle,
  onDelete,
  onExecute,
  onEdit,
  onClick,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const status = getTaskStatus(task.state);
  const isTaskActive = task.state === 'active';
  const lastExecution = task.last_execution;

  const handleRowClick = () => {
    setExpanded(!expanded);
  };

  const handleDelete = () => {
    onDelete(task.id);
    setShowDeleteDialog(false);
  };

  return (
    <>
      {/* Collapsed Row - renders as card on mobile, table row on desktop */}
      <motion.tr
        onClick={handleRowClick}
        className="block md:table-row bg-white md:bg-transparent border-2 md:border-b md:border-zinc-200 border-zinc-200 md:last:border-0 rounded-sm md:rounded-none p-4 md:p-0 mb-2 md:mb-0 cursor-pointer hover:bg-zinc-50 transition-colors"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        {/* Mobile Layout (block on < 768px) */}
        <td className="block md:hidden p-0">
          <div className="flex justify-between items-start gap-3 mb-2">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <motion.div
                animate={{ rotate: expanded ? 90 : 0 }}
                transition={{ duration: 0.2 }}
                className="text-zinc-400 flex-shrink-0"
              >
                <ChevronRight className="w-4 h-4" />
              </motion.div>
              <span className="font-grotesk font-bold text-sm truncate">{task.name}</span>
            </div>
            <StatusBadge variant={status.activityState} />
          </div>
          <div className="text-xs text-zinc-500 truncate pl-6 mb-2">
            {task.search_query}
          </div>
          <div className="flex gap-4 text-xs text-zinc-600 pl-6">
            <div className="flex items-center gap-1.5">
              <Clock className="w-3 h-3 flex-shrink-0" />
              <CronDisplay cron={task.schedule} className="truncate" showRaw={false} />
            </div>
            <div className="flex items-center gap-1.5">
              <span className="flex-shrink-0">🕐</span>
              <span className="truncate">
                {lastExecution ? formatTimeAgo(new Date(lastExecution.started_at)) : 'Never'}
              </span>
            </div>
          </div>
        </td>

        {/* Desktop Table Cells (hidden on mobile) */}
        <td className="hidden md:table-cell p-4">
          <div className="flex items-center gap-3">
            <motion.div
              animate={{ rotate: expanded ? 90 : 0 }}
              transition={{ duration: 0.2 }}
              className="text-zinc-400"
            >
              <ChevronRight className="w-4 h-4" />
            </motion.div>
            <div className="flex flex-col gap-1">
              <span className="font-grotesk font-bold text-sm">{task.name}</span>
              <span className="text-xs text-zinc-500 truncate max-w-xs">{task.search_query}</span>
            </div>
          </div>
        </td>
        <td className="hidden md:table-cell p-4">
          <StatusBadge variant={status.activityState} />
        </td>
        <td className="hidden md:table-cell p-4">
          <CronDisplay cron={task.schedule} className="text-sm font-mono text-zinc-600" showRaw={false} />
        </td>
        <td className="hidden md:table-cell p-4">
          {lastExecution ? (
            <span className="text-sm text-zinc-600">
              {new Date(lastExecution.started_at).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
              })}
            </span>
          ) : (
            <span className="text-sm text-zinc-400">Never</span>
          )}
        </td>
      </motion.tr>

      {/* Mobile Expanded Content */}
      <AnimatePresence>
        {expanded && (
          <motion.tr
            className="block md:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <td className="block p-0">
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="bg-white border-2 border-zinc-200 rounded-sm p-4 mb-2 mt-[-8px]">
                  {/* Latest Result */}
                  {lastExecution?.result?.answer ? (
                    <div className="mb-4">
                      <p className="text-sm text-zinc-700 leading-relaxed line-clamp-3">
                        {lastExecution.result.answer}
                      </p>
                      <div className="flex items-center gap-3 mt-2">
                        <span className="text-xs font-mono text-zinc-500">Condition:</span>
                        <StatusBadge
                          variant={lastExecution.condition_met ? 'met' : 'not_met'}
                          size="sm"
                        />
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-zinc-500 mb-4">No results yet</p>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onExecute(task.id);
                      }}
                    >
                      <Play className="w-3 h-3 mr-1.5" />
                      Run Now
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggle(task.id, isTaskActive ? 'paused' : 'active');
                      }}
                    >
                      {isTaskActive ? (
                        <>
                          <Pause className="w-3 h-3 mr-1.5" />
                          Pause
                        </>
                      ) : (
                        <>
                          <Play className="w-3 h-3 mr-1.5" />
                          Resume
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onEdit(task.id);
                      }}
                    >
                      <Settings className="w-3 h-3 mr-1.5" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowDeleteDialog(true);
                      }}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-3 h-3 mr-1.5" />
                      Delete
                    </Button>
                    <div className="flex-1" />
                    <Button
                      variant="default"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onClick(task.id);
                      }}
                    >
                      View Details
                      <ChevronRight className="w-3 h-3 ml-1.5" />
                    </Button>
                  </div>
                </div>
              </motion.div>
            </td>
          </motion.tr>
        )}
      </AnimatePresence>

      {/* Desktop Expanded Content */}
      <AnimatePresence>
        {expanded && (
          <tr className="hidden md:table-row">
            <td colSpan={4} className="p-0">
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="bg-zinc-50 border-b-2 border-zinc-200 p-4 pl-12">
                  {/* Latest Result */}
                  {lastExecution?.result?.answer ? (
                    <div className="mb-4">
                      <p className="text-sm text-zinc-700 leading-relaxed line-clamp-3">
                        {lastExecution.result.answer}
                      </p>
                      <div className="flex items-center gap-3 mt-2">
                        <span className="text-xs font-mono text-zinc-500">Condition:</span>
                        <StatusBadge
                          variant={lastExecution.condition_met ? 'met' : 'not_met'}
                          size="sm"
                        />
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-zinc-500 mb-4">No results yet</p>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onExecute(task.id);
                      }}
                    >
                      <Play className="w-3 h-3 mr-1.5" />
                      Run Now
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggle(task.id, isTaskActive ? 'paused' : 'active');
                      }}
                    >
                      {isTaskActive ? (
                        <>
                          <Pause className="w-3 h-3 mr-1.5" />
                          Pause
                        </>
                      ) : (
                        <>
                          <Play className="w-3 h-3 mr-1.5" />
                          Resume
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onEdit(task.id);
                      }}
                    >
                      <Settings className="w-3 h-3 mr-1.5" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowDeleteDialog(true);
                      }}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-3 h-3 mr-1.5" />
                      Delete
                    </Button>
                    <div className="flex-1" />
                    <Button
                      variant="default"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onClick(task.id);
                      }}
                    >
                      View Details
                      <ChevronRight className="w-3 h-3 ml-1.5" />
                    </Button>
                  </div>
                </div>
              </motion.div>
            </td>
          </tr>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent className="border-2 border-zinc-900 shadow-brutalist-lg">
          <AlertDialogHeader className="border-b-2 border-zinc-100 pb-4">
            <AlertDialogTitle className="font-grotesk">Delete Monitor</AlertDialogTitle>
            <AlertDialogDescription className="text-zinc-500">
              Are you sure you want to delete "{task.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="gap-3">
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="shadow-brutalist">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

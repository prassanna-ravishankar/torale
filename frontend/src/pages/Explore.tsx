import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';
import type { Task } from '@/types';
import { BrutalistCard, SectionLabel } from '@/components/torale';
import { Loader2, Eye, Users, ChevronLeft, ChevronRight, Compass, Copy } from 'lucide-react';
import { toast } from 'sonner';

export function Explore() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sortBy, setSortBy] = useState<'recent' | 'popular'>('popular');
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const limit = 20;

  useEffect(() => {
    loadTasks();
  }, [sortBy, offset]);

  const loadTasks = async () => {
    setIsLoading(true);
    try {
      const result = await api.getPublicTasks({ offset, limit, sort_by: sortBy });
      setTasks(result.tasks);
      setTotal(result.total);
    } catch (error) {
      console.error('Failed to load public tasks:', error);
      toast.error('Failed to load tasks');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTaskClick = (task: Task) => {
    navigate(`/tasks/${task.id}`);
  };

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  const handlePreviousPage = () => {
    if (offset > 0) {
      setOffset(offset - limit);
    }
  };

  const handleNextPage = () => {
    if (offset + limit < total) {
      setOffset(offset + limit);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-zinc-900 text-white">
              <Compass className="h-6 w-6" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold font-grotesk tracking-tight text-zinc-900">
              Explore Tasks
            </h1>
          </div>
          <p className="text-sm text-zinc-500 font-mono">
            Discover and copy public monitoring tasks from the community
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <SectionLabel>Sort by</SectionLabel>
            <div className="flex gap-2 border-2 border-zinc-200 bg-white">
              <button
                onClick={() => setSortBy('popular')}
                className={`px-3 py-1.5 text-xs font-mono uppercase tracking-wider transition-colors ${
                  sortBy === 'popular'
                    ? 'bg-zinc-900 text-white'
                    : 'bg-white text-zinc-600 hover:bg-zinc-50'
                }`}
              >
                Popular
              </button>
              <button
                onClick={() => setSortBy('recent')}
                className={`px-3 py-1.5 text-xs font-mono uppercase tracking-wider transition-colors ${
                  sortBy === 'recent'
                    ? 'bg-zinc-900 text-white'
                    : 'bg-white text-zinc-600 hover:bg-zinc-50'
                }`}
              >
                Recent
              </button>
            </div>
          </div>

          <div className="text-xs font-mono text-zinc-400">
            {total} {total === 1 ? 'task' : 'tasks'}
          </div>
        </div>

        {/* Task List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          </div>
        ) : tasks.length === 0 ? (
          <BrutalistCard className="p-12">
            <div className="text-center">
              <Compass className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
              <h3 className="text-lg font-grotesk font-bold text-zinc-900 mb-2">
                No public tasks yet
              </h3>
              <p className="text-sm text-zinc-500 font-mono">
                Be the first to share a task with the community!
              </p>
            </div>
          </BrutalistCard>
        ) : (
          <div className="space-y-4">
            {tasks.map((task) => (
              <BrutalistCard
                key={task.id}
                variant="clickable"
                onClick={() => handleTaskClick(task)}
                className="group"
              >
                {/* Header */}
                <div className="p-4 border-b border-zinc-100">
                  <h3 className="text-lg font-bold font-grotesk text-zinc-900 mb-1 group-hover:text-zinc-700 transition-colors">
                    {task.name}
                  </h3>
                  {task.slug && task.creator_username && (
                    <div className="flex items-center gap-1.5 text-[10px] font-mono text-zinc-400">
                      <Copy className="h-3 w-3" />
                      <span className="truncate">
                        /t/{task.creator_username}/{task.slug}
                      </span>
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="p-4">
                  <p className="text-sm text-zinc-600 leading-relaxed line-clamp-2">
                    {task.condition_description}
                  </p>
                </div>

                {/* Footer with stats */}
                <div className="bg-zinc-50 p-3 border-t border-zinc-100 flex items-center gap-4">
                  <div className="flex items-center gap-1.5">
                    <Eye className="h-4 w-4 text-zinc-400" />
                    <span className="text-xs font-mono text-zinc-600">{task.view_count}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Users className="h-4 w-4 text-zinc-400" />
                    <span className="text-xs font-mono text-zinc-600">{task.subscriber_count}</span>
                  </div>
                </div>
              </BrutalistCard>
            ))}
          </div>
        )}

        {/* Pagination */}
        {!isLoading && tasks.length > 0 && totalPages > 1 && (
          <div className="flex items-center justify-center gap-3 mt-8">
            <button
              onClick={handlePreviousPage}
              disabled={offset === 0}
              className="flex items-center gap-1.5 px-4 py-2 border-2 border-zinc-200 bg-white text-sm font-mono hover:border-zinc-900 transition-colors disabled:opacity-50 disabled:hover:border-zinc-200 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </button>
            <div className="text-sm font-mono text-zinc-500">
              Page {currentPage} of {totalPages}
            </div>
            <button
              onClick={handleNextPage}
              disabled={offset + limit >= total}
              className="flex items-center gap-1.5 px-4 py-2 border-2 border-zinc-200 bg-white text-sm font-mono hover:border-zinc-900 transition-colors disabled:opacity-50 disabled:hover:border-zinc-200 disabled:cursor-not-allowed"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

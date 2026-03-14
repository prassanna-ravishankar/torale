import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { Task, FeedExecution } from '@/types';
import { BrutalistCard, SectionLabel } from '@/components/torale';
import { ResultCard } from '@/components/ResultCard';
import { TaskDetailOverlay } from '@/components/TaskDetailOverlay';
import { Loader2, Eye, Users, ChevronLeft, ChevronRight, Compass, Copy, Rss, Globe } from 'lucide-react';
import { toast } from 'sonner';
import { getTaskShareUrl } from '@/lib/utils';
import { DynamicMeta } from '@/components/DynamicMeta';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from '@/contexts/AuthContext';

export function Explore() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [feed, setFeed] = useState<FeedExecution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isFeedLoading, setIsFeedLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('feed');
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'recent' | 'popular'>('popular');
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const limit = 20;

  const loadTasks = useCallback(async () => {
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
  }, [offset, limit, sortBy]);

  const loadFeed = useCallback(async () => {
    setIsFeedLoading(true);
    try {
      const data = await api.getPublicFeed();
      setFeed(data);
    } catch (error) {
      console.error('Failed to load public feed:', error);
    } finally {
      setIsFeedLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  useEffect(() => {
    loadFeed();
  }, [loadFeed]);

  const handleTaskClick = (task: Task) => {
    setSelectedTaskId(task.id);
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
    <>
      <DynamicMeta
        title="Explore Intelligence - Torale"
        description="Discover community monitoring results and public tasks. Browse live findings and copy monitors to your dashboard."
        url="https://torale.ai/explore"
      />
      <div className="min-h-screen bg-zinc-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-zinc-900 text-white">
              <Compass className="h-6 w-6" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold font-grotesk tracking-tight text-zinc-900">
              Explore
            </h1>
          </div>
          <p className="text-sm text-zinc-500 font-mono">
            Discover community monitors and live findings from across the web
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-transparent p-0 gap-8 h-auto border-b border-zinc-200 w-full justify-start rounded-none">
            <TabsTrigger 
              value="feed" 
              className="px-0 pb-3 rounded-none border-b-2 border-transparent data-[state=active]:border-zinc-900 data-[state=active]:bg-transparent shadow-none font-bold font-grotesk text-lg"
            >
              Global Feed
            </TabsTrigger>
            <TabsTrigger 
              value="tasks"
              className="px-0 pb-3 rounded-none border-b-2 border-transparent data-[state=active]:border-zinc-900 data-[state=active]:bg-transparent shadow-none font-bold font-grotesk text-lg"
            >
              Browse Tasks
            </TabsTrigger>
          </TabsList>

          <TabsContent value="feed" className="mt-0 outline-none">
            {isFeedLoading ? (
              <div className="flex items-center justify-center py-24">
                <Loader2 className="h-8 w-8 animate-spin text-zinc-300" />
              </div>
            ) : feed.length === 0 ? (
              <BrutalistCard className="p-12 text-center">
                <Globe className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
                <h3 className="text-lg font-grotesk font-bold text-zinc-900 mb-2">
                  No public results yet
                </h3>
                <p className="text-sm text-zinc-500 font-mono">
                  Results from public monitors will appear here.
                </p>
              </BrutalistCard>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {feed.map((execution) => (
                  <ResultCard 
                    key={execution.id} 
                    execution={execution} 
                    onClick={() => setSelectedTaskId(execution.task_id)}
                  />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="tasks" className="mt-0 outline-none">
            {/* Controls */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
              <div className="flex items-center gap-3">
                <SectionLabel>Sort by</SectionLabel>
                <div className="flex gap-2 border-2 border-zinc-200 bg-white p-0.5">
                  <button
                    onClick={() => setSortBy('popular')}
                    className={`px-3 py-1.5 text-[10px] font-mono uppercase tracking-wider transition-colors ${
                      sortBy === 'popular'
                        ? 'bg-zinc-900 text-white'
                        : 'bg-white text-zinc-600 hover:bg-zinc-50'
                    }`}
                  >
                    Popular
                  </button>
                  <button
                    onClick={() => setSortBy('recent')}
                    className={`px-3 py-1.5 text-[10px] font-mono uppercase tracking-wider transition-colors ${
                      sortBy === 'recent'
                        ? 'bg-zinc-900 text-white'
                        : 'bg-white text-zinc-600 hover:bg-zinc-50'
                    }`}
                  >
                    Recent
                  </button>
                </div>
              </div>

              <div className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest">
                {total} {total === 1 ? 'task' : 'tasks'}
              </div>
            </div>

            {/* Task List */}
            {isLoading ? (
              <div className="flex items-center justify-center py-24">
                <Loader2 className="h-8 w-8 animate-spin text-zinc-300" />
              </div>
            ) : tasks.length === 0 ? (
              <BrutalistCard className="p-12 text-center">
                <Compass className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
                <h3 className="text-lg font-grotesk font-bold text-zinc-900 mb-2">
                  No public tasks yet
                </h3>
                <p className="text-sm text-zinc-500 font-mono">
                  Be the first to share a monitor with the community!
                </p>
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
                    <div className="p-4 border-b border-zinc-100 flex justify-between items-start">
                      <div className="min-w-0">
                        <h3 className="text-lg font-bold font-grotesk text-zinc-900 mb-1 group-hover:text-zinc-700 transition-colors">
                          {task.name}
                        </h3>
                        <div className="flex items-center gap-3">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              const shareUrl = getTaskShareUrl(task.id);
                              navigator.clipboard.writeText(shareUrl);
                              toast.success('Share URL copied to clipboard');
                            }}
                            className="flex items-center gap-1.5 text-[10px] font-mono text-zinc-400 hover:text-zinc-900 transition-colors"
                            title="Copy share URL"
                          >
                            <Copy className="h-3 w-3" />
                            <span className="truncate max-w-[150px]">
                              /tasks/{task.id}
                            </span>
                          </button>
                          <a
                            href={api.getTaskRssUrl(task.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="flex items-center gap-1 text-[10px] font-mono text-zinc-400 hover:text-zinc-900 transition-colors"
                            title="RSS feed"
                          >
                            <Rss className="h-3 w-3" />
                            <span>RSS</span>
                          </a>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4 shrink-0">
                        <div className="flex flex-col items-end">
                           <div className="flex items-center gap-1.5 text-zinc-400">
                              <Eye className="h-3.5 w-3.5" />
                              <span className="text-xs font-mono">{task.view_count}</span>
                           </div>
                           <div className="flex items-center gap-1.5 text-zinc-400">
                              <Users className="h-3.5 w-3.5" />
                              <span className="text-xs font-mono">{task.subscriber_count}</span>
                           </div>
                        </div>
                      </div>
                    </div>

                    {/* Content */}
                    <div className="p-4 bg-zinc-50/50">
                      <p className="text-sm text-zinc-600 leading-relaxed line-clamp-2">
                        {task.condition_description}
                      </p>
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
          </TabsContent>
        </Tabs>
      </div>
      
      {/* Detail Overlay */}
      <TaskDetailOverlay
        taskId={selectedTaskId}
        open={!!selectedTaskId}
        onOpenChange={(open) => !open && setSelectedTaskId(null)}
        currentUserId={user?.id}
        onDeleted={loadTasks}
      />
    </div>
    </>
  );
}

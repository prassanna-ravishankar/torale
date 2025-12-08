import { useEffect, useState } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { api } from '@/lib/api';
import { Loader2 } from 'lucide-react';
import { DynamicMeta } from '@/components/DynamicMeta';
import type { Task } from '@/types';

export function VanityTaskRedirect() {
  const { username, slug } = useParams<{ username: string; slug: string }>();
  const [task, setTask] = useState<Task | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!username || !slug) {
      setError('Invalid URL');
      setIsLoading(false);
      return;
    }

    loadTask();
  }, [username, slug]);

  const loadTask = async () => {
    if (!username || !slug) return;

    setIsLoading(true);
    try {
      const fetchedTask = await api.getPublicTaskByVanityUrl(username, slug);
      setTask(fetchedTask);
    } catch (error) {
      console.error('Failed to load task:', error);
      setError('Task not found');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !task) {
    return <Navigate to="/explore" replace />;
  }

  // Generate OpenGraph metadata
  // Use centralized API base URL from api client
  const ogImage = `${api.getBaseUrl()}/api/v1/og/tasks/${task.id}.jpg`;

  // For ogUrl, use the frontend URL (not API URL)
  const ogUrl = `${window.location.origin}/t/${username}/${slug}`;
  const ogTitle = `${task.name} - Torale`;
  const ogDescription = task.condition_description || 'Monitor the web with AI';

  return (
    <>
      <DynamicMeta
        title={ogTitle}
        description={ogDescription}
        image={ogImage}
        url={ogUrl}
        type="article"
      />
      <Navigate to={`/tasks/${task.id}`} replace />
    </>
  );
}

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import { api } from '@/lib/api';
import type { FeedExecution, GroundingSource } from '@/types';
import { markdownCompact } from '@/lib/markdown';
import { formatTimeAgo } from '@/lib/utils';
import { DynamicMeta } from '@/components/DynamicMeta';
import styles from '@/components/explore/Explore.module.css';

const rehypePlugins = [rehypeSanitize];

function getHost(url: string): string {
  try {
    return new URL(url).host.replace(/^www\./, '');
  } catch {
    return url;
  }
}

interface FeedEntryProps {
  execution: FeedExecution;
  onClick: () => void;
}

function FeedEntry({ execution, onClick }: FeedEntryProps) {
  const content = execution.notification || execution.result?.evidence || 'No content found.';

  // Source list: prefer execution.result.sources, fall back to grounding_sources.
  const sources: GroundingSource[] =
    execution.result?.sources && execution.result.sources.length > 0
      ? execution.result.sources
      : execution.grounding_sources ?? [];

  // Heuristic clip: long answers get a fade-out so the feed stays a moment list.
  const isLong = content.length > 600;

  return (
    <button
      type="button"
      className={styles.entry}
      onClick={onClick}
      aria-label={`Open watch ${execution.task_name}`}
    >
      <div className={styles.entryEyebrow}>
        <span className={styles.entryEyebrowName}>{execution.task_name}</span>
        <span className={styles.entryEyebrowSep}>·</span>
        <span className={styles.entryEyebrowTime}>{formatTimeAgo(execution.started_at)}</span>
      </div>

      <div className={styles.entryBodyWrap}>
        <div className={`${styles.entryBody} ${isLong ? styles.entryClipped : ''}`}>
          <ReactMarkdown rehypePlugins={rehypePlugins} components={markdownCompact}>
            {content}
          </ReactMarkdown>
        </div>
        {isLong && <div className={styles.entryFade} aria-hidden="true" />}
      </div>

      {sources.length > 0 && (
        <div className={styles.entrySources}>
          {sources.slice(0, 4).map((src, i) => (
            <div key={`${src.url}-${i}`} className={styles.entrySource}>
              <span className={styles.entrySourceHost}>{getHost(src.url)}</span>
              <span className={styles.entrySourceLink}>{src.title || src.url}</span>
            </div>
          ))}
        </div>
      )}
    </button>
  );
}

export function Explore() {
  const navigate = useNavigate();
  const [feed, setFeed] = useState<FeedExecution[]>([]);
  const [isFeedLoading, setIsFeedLoading] = useState(true);

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
    loadFeed();
  }, [loadFeed]);

  return (
    <>
      <DynamicMeta
        path="/explore"
        title="Explore — webwhen"
        description="See what people are watching with webwhen — public watches and recent triggers across the open web."
      />
      <div className={styles.column}>
        {isFeedLoading ? (
          <div className={styles.loading}>watching the feed…</div>
        ) : feed.length === 0 ? (
          <div className={styles.empty}>
            <p className={styles.emptyPull}>Nothing public yet.</p>
            <p className={styles.emptySub}>Recent triggers from public watches will appear here.</p>
          </div>
        ) : (
          <div className={styles.feed}>
            {feed.map((execution) => (
              <FeedEntry
                key={execution.id}
                execution={execution}
                onClick={() => navigate(`/tasks/${execution.task_id}`)}
              />
            ))}
          </div>
        )}
      </div>
    </>
  );
}

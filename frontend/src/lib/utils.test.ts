import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { cn, calculateDurationInSeconds, formatDuration, formatTimeAgo } from './utils';

describe('cn', () => {
  it('merges class names correctly', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('handles conditional classes', () => {
    expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz');
  });

  it('merges tailwind classes correctly', () => {
    expect(cn('px-2', 'px-4')).toBe('px-4');
  });
});

describe('calculateDurationInSeconds', () => {
  it('calculates duration between two timestamps', () => {
    const start = '2025-01-01T00:00:00Z';
    const end = '2025-01-01T00:01:00Z';
    expect(calculateDurationInSeconds(start, end)).toBe(60);
  });

  it('rounds to nearest integer', () => {
    const start = '2025-01-01T00:00:00Z';
    const end = '2025-01-01T00:00:42.5Z';
    expect(calculateDurationInSeconds(start, end)).toBe(43);
  });
});

describe('formatDuration', () => {
  it('formats completed duration', () => {
    const start = '2025-01-01T00:00:00Z';
    const end = '2025-01-01T00:00:42Z';
    expect(formatDuration(start, end)).toBe('42s');
  });

  it('returns default label for incomplete duration', () => {
    const start = '2025-01-01T00:00:00Z';
    expect(formatDuration(start, null)).toBe('In progress');
  });

  it('returns custom label for incomplete duration', () => {
    const start = '2025-01-01T00:00:00Z';
    expect(formatDuration(start, null, 'Running')).toBe('Running');
  });

  it('handles null start time', () => {
    expect(formatDuration(null, null)).toBe('In progress');
  });
});

describe('formatTimeAgo', () => {
  beforeEach(() => {
    // Mock Date.now() to return a fixed timestamp
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2025-01-01T12:00:00Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns "Just now" for times less than 1 minute ago', () => {
    const dateString = '2025-01-01T11:59:30Z'; // 30 seconds ago
    expect(formatTimeAgo(dateString)).toBe('Just now');
  });

  it('returns minutes for times less than 1 hour ago', () => {
    const dateString = '2025-01-01T11:45:00Z'; // 15 minutes ago
    expect(formatTimeAgo(dateString)).toBe('15m ago');
  });

  it('returns hours for times less than 24 hours ago', () => {
    const dateString = '2025-01-01T09:00:00Z'; // 3 hours ago
    expect(formatTimeAgo(dateString)).toBe('3h ago');
  });

  it('returns days for times less than 7 days ago', () => {
    const dateString = '2024-12-29T12:00:00Z'; // 3 days ago
    expect(formatTimeAgo(dateString)).toBe('3d ago');
  });

  it('returns formatted date for times more than 7 days ago', () => {
    const dateString = '2024-12-20T12:00:00Z'; // 12 days ago
    const result = formatTimeAgo(dateString);
    // toLocaleDateString format varies by locale, just check it's not relative
    expect(result).not.toContain('ago');
    expect(result).toContain('12/20/2024');
  });

  it('handles edge case at exactly 1 minute', () => {
    const dateString = '2025-01-01T11:59:00Z'; // Exactly 1 minute ago
    expect(formatTimeAgo(dateString)).toBe('1m ago');
  });

  it('handles edge case at exactly 1 hour', () => {
    const dateString = '2025-01-01T11:00:00Z'; // Exactly 1 hour ago
    expect(formatTimeAgo(dateString)).toBe('1h ago');
  });

  it('handles edge case at exactly 1 day', () => {
    const dateString = '2024-12-31T12:00:00Z'; // Exactly 1 day ago
    expect(formatTimeAgo(dateString)).toBe('1d ago');
  });

  it('handles edge case at exactly 7 days', () => {
    const dateString = '2024-12-25T12:00:00Z'; // Exactly 7 days ago
    expect(formatTimeAgo(dateString)).toBe('7d ago');
  });
});

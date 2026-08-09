# Memory Index

- [feedback_landing_copy.md](feedback_landing_copy.md) - Landing page: avoid jargon, lead with moment not mechanism; JS rendering hurts SEO
- [project_infra_gotchas.md](project_infra_gotchas.md) - GKE Autopilot spot preemptions, cloud-sql-proxy auth delays, agent cold-start probe failures
- [project_gemini_503s.md](project_gemini_503s.md) - Gemini 503s classified as "unknown" not "rate_limit" in errors.py; 19% failure rate, open issue
- [project_execution_id_reuse_legacy.md](project_execution_id_reuse_legacy.md) - Pre-PR#207 rows have inflated durations and stale errors; don't backfill, they age out
- [project_notification_links.md](project_notification_links.md) - Notification CTAs are owner links; public `/tasks/:id` returns 404 for private watches
- [project_watch_lifecycle.md](project_watch_lifecycle.md) - Watches are user-controlled; suppress agent auto-completion and guard rescheduling races
- [project_search_retrieval.md](project_search_retrieval.md) - Search is independent from the reasoning model; Perplexity/Parallel replaced Gemini native grounding based on evals

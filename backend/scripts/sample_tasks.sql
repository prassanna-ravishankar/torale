-- Sample monitoring tasks for November 2025
-- Usage: Replace :user_id with the actual user UUID
--   e.g., psql -v user_id="'your-uuid-here'" -f sample_tasks.sql

INSERT INTO tasks (
    id,
    user_id,
    name,
    schedule,
    executor_type,
    search_query,
    condition_description,
    notify_behavior,
    is_active,
    config
) VALUES

-- 1. Tech Product Launch Monitor
(
    gen_random_uuid(),
    :user_id,
    'RTX 5090 Release Date',
    '0 9 * * *',  -- Daily at 9 AM
    'llm_grounded_search',
    'When is the NVIDIA RTX 5090 graphics card being released?',
    'A specific release date or pre-order date has been officially announced by NVIDIA',
    'once',
    true,
    '{"model": "gemini-2.0-flash-exp"}'::jsonb
),

-- 2. Concert Ticket Availability
(
    gen_random_uuid(),
    :user_id,
    'Taylor Swift Eras Tour 2025',
    '0 */4 * * *',  -- Every 4 hours
    'llm_grounded_search',
    'Are tickets available for Taylor Swift Eras Tour 2025 dates?',
    'New tour dates are announced or tickets become available for purchase',
    'track_state',
    true,
    '{"model": "gemini-2.0-flash-exp"}'::jsonb
),

-- 3. AI Model Release
(
    gen_random_uuid(),
    :user_id,
    'GPT-5 Launch Announcement',
    '0 8 * * *',  -- Daily at 8 AM
    'llm_grounded_search',
    'Has OpenAI announced GPT-5 or when will it be released?',
    'OpenAI has officially announced GPT-5 with a launch date or availability timeframe',
    'once',
    true,
    '{"model": "gemini-2.0-flash-exp"}'::jsonb
),

-- 4. Gaming Console Restock
(
    gen_random_uuid(),
    :user_id,
    'PS5 Pro Stock at Best Buy',
    '0 */2 * * *',  -- Every 2 hours
    'llm_grounded_search',
    'Is PlayStation 5 Pro in stock at Best Buy?',
    'PS5 Pro shows as in stock and available for purchase at BestBuy.com',
    'always',
    true,
    '{"model": "gemini-2.0-flash-exp"}'::jsonb
),

-- 5. Summer Program Registration
(
    gen_random_uuid(),
    :user_id,
    'Community Pool Summer Pass 2026',
    '0 10 * * 1',  -- Weekly on Monday at 10 AM
    'llm_grounded_search',
    'When does registration open for summer 2026 community pool memberships?',
    'Registration dates or early bird pricing for summer 2026 pool passes are announced',
    'once',
    true,
    '{"model": "gemini-2.0-flash-exp"}'::jsonb
),

-- 6. Software Framework Release
(
    gen_random_uuid(),
    :user_id,
    'React 19 Stable Release',
    '0 12 * * *',  -- Daily at noon
    'llm_grounded_search',
    'Has React 19 stable version been released?',
    'React 19 stable version is officially released and available on npm',
    'once',
    true,
    '{"model": "gemini-2.0-flash-exp"}'::jsonb
);

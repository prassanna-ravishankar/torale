-- Seed task templates for November 2025
-- Diverse templates across categories: Tech, Shopping, Events, Seasonal, Software

INSERT INTO task_templates (
    name,
    description,
    category,
    icon,
    search_query,
    condition_description,
    schedule,
    notify_behavior,
    config
) VALUES

-- Tech: Product Launch
(
    'GPU Release Monitor',
    'Monitor for NVIDIA RTX 5090 graphics card release announcements',
    'Tech',
    '🎮',
    'When is the NVIDIA RTX 5090 graphics card being released?',
    'A specific release date or pre-order date has been officially announced by NVIDIA',
    '0 9 * * *',  -- Daily at 9 AM
    'once',
    '{"model": "gemini-2.0-flash-exp"}'::jsonb
),

-- Shopping: Stock Alert
(
    'PS5 Pro Stock Alert',
    'Get notified when PlayStation 5 Pro is back in stock at major retailers',
    'Shopping',
    '🎮',
    'Is PlayStation 5 Pro in stock at Best Buy?',
    'PS5 Pro shows as in stock and available for purchase at BestBuy.com',
    '0 */2 * * *',  -- Every 2 hours
    'always',
    '{"model": "gemini-2.0-flash-exp"}'::jsonb
),

-- Events: Concert Tickets
(
    'Concert Ticket Tracker',
    'Track Taylor Swift Eras Tour 2025 ticket availability',
    'Events',
    '🎵',
    'Are tickets available for Taylor Swift Eras Tour 2025 dates?',
    'New tour dates are announced or tickets become available for purchase',
    '0 */4 * * *',  -- Every 4 hours
    'track_state',
    '{"model": "gemini-2.0-flash-exp"}'::jsonb
),

-- Tech: AI Model Release
(
    'AI Model Launch Watch',
    'Stay updated on GPT-5 release announcements from OpenAI',
    'Tech',
    '🤖',
    'Has OpenAI announced GPT-5 or when will it be released?',
    'OpenAI has officially announced GPT-5 with a launch date or availability timeframe',
    '0 8 * * *',  -- Daily at 8 AM
    'once',
    '{"model": "gemini-2.0-flash-exp"}'::jsonb
),

-- Seasonal: Summer Programs
(
    'Summer Program Registration',
    'Monitor for community pool membership registration opening',
    'Seasonal',
    '🏊',
    'When does registration open for summer 2026 community pool memberships?',
    'Registration dates or early bird pricing for summer 2026 pool passes are announced',
    '0 10 * * 1',  -- Weekly on Monday at 10 AM
    'once',
    '{"model": "gemini-2.0-flash-exp"}'::jsonb
),

-- Software: Framework Release
(
    'Framework Release Tracker',
    'Track stable release of React 19',
    'Software',
    '⚛️',
    'Has React 19 stable version been released?',
    'React 19 stable version is officially released and available on npm',
    '0 12 * * *',  -- Daily at noon
    'once',
    '{"model": "gemini-2.0-flash-exp"}'::jsonb
);

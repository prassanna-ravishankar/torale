"""squashed initial schema

Revision ID: e95666a4cd0e
Revises: (none - squashed from 22 migrations)
Create Date: 2025-02-01

Squashed migration that creates the full Torale schema from scratch.
Production already has this revision stamped, so it will never re-run there.
Only runs against fresh databases (local dev, CI, new environments).
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e95666a4cd0e"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    # --- users ---
    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            clerk_user_id TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            first_name TEXT,
            verified_notification_emails TEXT[] DEFAULT ARRAY[]::TEXT[],
            webhook_url TEXT,
            webhook_secret TEXT,
            webhook_enabled BOOLEAN DEFAULT false,
            username VARCHAR(30) UNIQUE
        )
    """)
    op.execute("CREATE INDEX idx_users_clerk_user_id ON users(clerk_user_id)")
    op.execute("CREATE INDEX idx_users_email ON users(email)")

    # --- task_executions (before tasks, because tasks references it) ---
    op.execute("""
        CREATE TABLE task_executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_id UUID NOT NULL,
            status TEXT NOT NULL,
            started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE,
            result JSONB,
            error_message TEXT,
            condition_met BOOLEAN,
            change_summary TEXT,
            grounding_sources JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_task_executions_task_id ON task_executions(task_id)")

    # --- tasks ---
    op.execute("""
        CREATE TABLE tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            schedule TEXT NOT NULL,
            search_query TEXT,
            condition_description TEXT,
            notify_behavior TEXT DEFAULT 'once',
            last_known_state JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            notifications JSONB NOT NULL DEFAULT '[]'::jsonb,
            notification_channels TEXT[] DEFAULT ARRAY['email']::TEXT[],
            notification_email TEXT,
            webhook_url TEXT,
            webhook_secret TEXT,
            is_public BOOLEAN DEFAULT false,
            slug VARCHAR(255),
            view_count INTEGER DEFAULT 0,
            subscriber_count INTEGER DEFAULT 0,
            forked_from_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
            state TEXT NOT NULL DEFAULT 'active',
            state_changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            last_execution_id UUID REFERENCES task_executions(id) ON DELETE SET NULL,
            CONSTRAINT check_notify_behavior CHECK (notify_behavior IN ('once', 'always')),
            CONSTRAINT check_notification_channels CHECK (notification_channels <@ ARRAY['email', 'webhook']::TEXT[]),
            CONSTRAINT tasks_state_check CHECK (state IN ('active', 'paused', 'completed'))
        )
    """)

    # Add FK from task_executions.task_id -> tasks.id now that tasks exists
    op.execute("""
        ALTER TABLE task_executions
        ADD CONSTRAINT task_executions_task_id_fkey
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
    """)

    # Unique constraint on (user_id, name)
    op.execute("ALTER TABLE tasks ADD CONSTRAINT uq_tasks_user_id_name UNIQUE (user_id, name)")

    # Tasks indexes
    op.execute("CREATE INDEX idx_tasks_user_id ON tasks(user_id)")
    op.execute("CREATE INDEX idx_tasks_state ON tasks(state)")
    op.execute("CREATE INDEX idx_tasks_user_state ON tasks(user_id, state)")
    op.execute("CREATE INDEX idx_tasks_is_public ON tasks(is_public) WHERE is_public = true")
    op.execute(
        "CREATE UNIQUE INDEX idx_tasks_user_slug ON tasks(user_id, slug) WHERE slug IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX idx_tasks_forked_from ON tasks(forked_from_task_id) WHERE forked_from_task_id IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX idx_tasks_public_view_count ON tasks(view_count) WHERE is_public = true"
    )

    # Tasks trigger
    op.execute("""
        CREATE TRIGGER update_tasks_updated_at
            BEFORE UPDATE ON tasks
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
    """)

    # --- task_templates ---
    op.execute("""
        CREATE TABLE task_templates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            category VARCHAR(100) NOT NULL,
            icon VARCHAR(50),
            search_query TEXT NOT NULL,
            condition_description TEXT NOT NULL,
            schedule VARCHAR(100) NOT NULL,
            notify_behavior VARCHAR(50) NOT NULL,
            config JSON DEFAULT '{"model": "gemini-2.5-flash"}'::json,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            CONSTRAINT chk_templates_notify_behavior CHECK (notify_behavior IN ('once', 'always'))
        )
    """)
    op.execute("CREATE INDEX idx_templates_category ON task_templates(category)")
    op.execute("CREATE INDEX idx_templates_active ON task_templates(is_active)")

    # Seed task templates
    op.execute("""
        INSERT INTO task_templates (
            name, description, category, icon, search_query,
            condition_description, schedule, notify_behavior, config
        )
        SELECT * FROM (VALUES
            (
                'GPU Release Monitor',
                'Monitor for NVIDIA RTX 5090 graphics card release announcements',
                'Tech',
                '🎮',
                'When is the NVIDIA RTX 5090 graphics card being released?',
                'A specific release date or pre-order date has been officially announced by NVIDIA',
                '0 9 * * *',
                'once',
                '{"model": "gemini-2.5-flash"}'::jsonb
            ),
            (
                'PS5 Pro Stock Alert',
                'Get notified when PlayStation 5 Pro is back in stock at major retailers',
                'Shopping',
                '🎮',
                'Is PlayStation 5 Pro in stock at Best Buy?',
                'PS5 Pro shows as in stock and available for purchase at BestBuy.com',
                '0 */2 * * *',
                'always',
                '{"model": "gemini-2.5-flash"}'::jsonb
            ),
            (
                'Concert Ticket Tracker',
                'Track Taylor Swift Eras Tour 2025 ticket availability',
                'Events',
                '🎵',
                'Are tickets available for Taylor Swift Eras Tour 2025 dates?',
                'New tour dates are announced or tickets become available for purchase',
                '0 */4 * * *',
                'always',
                '{"model": "gemini-2.5-flash"}'::jsonb
            ),
            (
                'AI Model Launch Watch',
                'Stay updated on GPT-5 release announcements from OpenAI',
                'Tech',
                '🤖',
                'Has OpenAI announced GPT-5 or when will it be released?',
                'OpenAI has officially announced GPT-5 with a launch date or availability timeframe',
                '0 8 * * *',
                'once',
                '{"model": "gemini-2.5-flash"}'::jsonb
            ),
            (
                'Summer Program Registration',
                'Monitor for community pool membership registration opening',
                'Seasonal',
                '🏊',
                'When does registration open for summer 2026 community pool memberships?',
                'Registration dates or early bird pricing for summer 2026 pool passes are announced',
                '0 10 * * 1',
                'once',
                '{"model": "gemini-2.5-flash"}'::jsonb
            ),
            (
                'Framework Release Tracker',
                'Track stable release of React 19',
                'Software',
                '⚛️',
                'Has React 19 stable version been released?',
                'React 19 stable version is officially released and available on npm',
                '0 12 * * *',
                'once',
                '{"model": "gemini-2.5-flash"}'::jsonb
            )
        ) AS v(name, description, category, icon, search_query, condition_description, schedule, notify_behavior, config)
        WHERE NOT EXISTS (SELECT 1 FROM task_templates LIMIT 1)
    """)

    # --- api_keys ---
    op.execute("""
        CREATE TABLE api_keys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            key_prefix TEXT NOT NULL,
            key_hash TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            last_used_at TIMESTAMP WITH TIME ZONE,
            is_active BOOLEAN NOT NULL DEFAULT true
        )
    """)
    op.execute("CREATE INDEX idx_api_keys_user_id ON api_keys(user_id)")
    op.execute("CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash) WHERE is_active = true")

    # --- waitlist ---
    op.execute("""
        CREATE TABLE waitlist (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            status TEXT NOT NULL DEFAULT 'pending',
            invited_at TIMESTAMP WITH TIME ZONE,
            notes TEXT,
            CONSTRAINT waitlist_status_check CHECK (status IN ('pending', 'invited', 'converted'))
        )
    """)
    op.execute("CREATE INDEX idx_waitlist_status ON waitlist(status)")
    op.execute("CREATE INDEX idx_waitlist_created_at ON waitlist(created_at)")

    # --- email_verifications ---
    op.execute("""
        CREATE TABLE email_verifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            email TEXT NOT NULL,
            verification_code TEXT NOT NULL,
            verified BOOLEAN DEFAULT false,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            verified_at TIMESTAMP WITH TIME ZONE,
            attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    op.execute(
        "CREATE INDEX idx_email_verifications_code ON email_verifications(verification_code) WHERE verified = false"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_pending_email_verification ON email_verifications(user_id, email) WHERE verified = false"
    )
    op.execute(
        "CREATE INDEX idx_email_verifications_user_created ON email_verifications(user_id, created_at)"
    )

    # --- notification_sends ---
    op.execute("""
        CREATE TABLE notification_sends (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
            recipient_email TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            execution_id UUID REFERENCES task_executions(id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'success',
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    op.execute(
        "CREATE INDEX idx_notification_sends_user_time ON notification_sends(user_id, created_at)"
    )
    op.execute(
        "CREATE INDEX idx_notification_sends_email_time ON notification_sends(recipient_email, created_at)"
    )

    # --- webhook_deliveries ---
    op.execute("""
        CREATE TABLE webhook_deliveries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            execution_id UUID REFERENCES task_executions(id) ON DELETE CASCADE,
            webhook_url TEXT NOT NULL,
            payload JSONB NOT NULL,
            signature TEXT NOT NULL,
            http_status INTEGER,
            response_body TEXT,
            attempt_number INTEGER NOT NULL DEFAULT 1,
            delivered_at TIMESTAMP WITH TIME ZONE,
            failed_at TIMESTAMP WITH TIME ZONE,
            error_message TEXT,
            next_retry_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_webhook_deliveries_task_id ON webhook_deliveries(task_id)")
    op.execute(
        "CREATE INDEX idx_webhook_deliveries_next_retry ON webhook_deliveries(next_retry_at) WHERE delivered_at IS NULL AND failed_at IS NULL"
    )

    # --- reserved_usernames ---
    op.execute("""
        CREATE TABLE reserved_usernames (
            username VARCHAR(30) PRIMARY KEY
        )
    """)
    op.execute("""
        INSERT INTO reserved_usernames (username) VALUES
            ('admin'),
            ('api'),
            ('explore'),
            ('settings'),
            ('support'),
            ('help'),
            ('www'),
            ('app'),
            ('dashboard'),
            ('tasks'),
            ('public'),
            ('auth'),
            ('signin'),
            ('signup'),
            ('login'),
            ('logout'),
            ('register')
        ON CONFLICT (username) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS reserved_usernames CASCADE")
    op.execute("DROP TABLE IF EXISTS webhook_deliveries CASCADE")
    op.execute("DROP TABLE IF EXISTS notification_sends CASCADE")
    op.execute("DROP TABLE IF EXISTS email_verifications CASCADE")
    op.execute("DROP TABLE IF EXISTS waitlist CASCADE")
    op.execute("DROP TABLE IF EXISTS api_keys CASCADE")
    op.execute("DROP TABLE IF EXISTS task_templates CASCADE")
    op.execute("DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks")
    op.execute("DROP TABLE IF EXISTS tasks CASCADE")
    op.execute("DROP TABLE IF EXISTS task_executions CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

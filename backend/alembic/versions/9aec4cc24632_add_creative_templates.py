"""add_creative_templates

Revision ID: 9aec4cc24632
Revises: e95666a4cd0e
Create Date: 2026-02-01 19:58:13.458941

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9aec4cc24632"
down_revision: str | Sequence[str] | None = "e95666a4cd0e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Remove old templates to keep the list clean and high-quality
    op.execute("DELETE FROM task_templates")

    # Insert new "Agent-First" templates
    op.execute("""
        INSERT INTO task_templates (
            name, description, category, icon, search_query,
            condition_description, schedule, notify_behavior, config
        )
        SELECT * FROM (VALUES
            (
                'GTA VI Release Date',
                'Get notified the moment Rockstar announces the exact release date',
                'Gaming',
                '🎮',
                'Has Rockstar Games announced the specific release date for Grand Theft Auto VI?',
                'A specific release date (day/month) is officially confirmed by Rockstar',
                '0 12 * * *',
                'once',
                '{"model": "gemini-2.5-flash"}'::jsonb
            ),
            (
                'SpaceX Starship Launch',
                'Track the next orbital flight test schedule',
                'Space',
                '🚀',
                'When is the next SpaceX Starship orbital flight test scheduled?',
                'An official launch window or date is announced by SpaceX or FAA',
                '0 9 * * *',
                'once',
                '{"model": "gemini-2.5-flash"}'::jsonb
            ),
            (
                'Mortgage Rate Drop',
                'Alert me when 30-year fixed rates drop below 5.5%',
                'Finance',
                '📉',
                'What is the current average 30-year fixed mortgage rate in the US?',
                'The average rate drops below 5.5%',
                '0 10 * * 1',
                'once',
                '{"model": "gemini-2.5-flash"}'::jsonb
            ),
            (
                'Northern Lights London',
                'Monitor space weather forecasts for aurora visibility in the UK',
                'Nature',
                '🌌',
                'Is there a high probability of seeing the Northern Lights in Southern England/London tonight or tomorrow?',
                'Forecast indicates high KP index or red alert for Southern UK visibility',
                '0 16 * * *',
                'always',
                '{"model": "gemini-2.5-flash"}'::jsonb
            ),
            (
                'Vintage Film Restock',
                'Check if Kodak Gold 200 is back in stock at major UK retailers',
                'Photography',
                '📸',
                'Is Kodak Gold 200 35mm film in stock at Analogue Wonderland or Parallax?',
                'Film is listed as "In Stock" and available for purchase',
                '0 */4 * * *',
                'once',
                '{"model": "gemini-2.5-flash"}'::jsonb
            ),
            (
                'iPhone 18 Rumors',
                'Weekly digest of credible iPhone 18 leaks and specs',
                'Tech',
                '📱',
                'What are the latest credible rumors and leaks for the iPhone 18 lineup?',
                'New credible leaks about specs, design, or release timing from major sources',
                '0 9 * * 5',
                'always',
                '{"model": "gemini-2.5-flash"}'::jsonb
            ),
            (
                'Weekend Train Strikes',
                'Warn me if there are train strikes planned for this weekend',
                'Travel',
                '🚆',
                'Are there any rail strikes planned in the UK for this coming weekend?',
                'Strikes are confirmed that affect major rail lines this weekend',
                '0 10 * * 3',
                'always',
                '{"model": "gemini-2.5-flash"}'::jsonb
            ),
            (
                'Anthropic Jobs',
                'Notify me when new "Prompt Engineer" roles open in London',
                'Careers',
                '💼',
                'Are there any open "Prompt Engineer" or "Research Engineer" roles at Anthropic in London?',
                'A new job listing matching the title and location is found',
                '0 9 * * *',
                'once',
                '{"model": "gemini-2.5-flash"}'::jsonb
            )
        ) AS v(name, description, category, icon, search_query, condition_description, schedule, notify_behavior, config)
    """)


def downgrade() -> None:
    op.execute("DELETE FROM task_templates")
    # Re-insert the old seed data if we really wanted to, but for dev it's fine to just empty it
    # or leave it empty as the previous migration will re-seed on a fresh install.

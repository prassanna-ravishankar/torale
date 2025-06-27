-- Create notification preferences table
CREATE TABLE notification_preferences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    user_email TEXT NOT NULL,
    email_enabled BOOLEAN DEFAULT true,
    email_frequency TEXT DEFAULT 'immediate' CHECK (email_frequency IN ('immediate', 'hourly', 'daily', 'disabled')),
    browser_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Create notification logs table
CREATE TABLE notification_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    alert_id UUID REFERENCES change_alerts(id) ON DELETE SET NULL,
    user_email TEXT NOT NULL,
    notification_type TEXT NOT NULL CHECK (notification_type IN ('email', 'browser', 'webhook')),
    status TEXT NOT NULL CHECK (status IN ('sent', 'failed', 'pending')),
    provider TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_code INTEGER,
    metadata JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add notification tracking columns to change_alerts
ALTER TABLE change_alerts 
ADD COLUMN notification_sent BOOLEAN DEFAULT false,
ADD COLUMN notification_sent_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN notification_retry_count INTEGER DEFAULT 0;

-- Create indexes
CREATE INDEX idx_notification_preferences_user_id ON notification_preferences(user_id);
CREATE INDEX idx_notification_preferences_user_email ON notification_preferences(user_email);
CREATE INDEX idx_notification_logs_alert_id ON notification_logs(alert_id);
CREATE INDEX idx_notification_logs_user_email ON notification_logs(user_email);
CREATE INDEX idx_notification_logs_sent_at ON notification_logs(sent_at);
CREATE INDEX idx_change_alerts_notification_sent ON change_alerts(notification_sent) WHERE notification_sent = false;

-- Enable RLS
ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for notification_preferences
CREATE POLICY "Users can view their own notification preferences"
    ON notification_preferences FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own notification preferences"
    ON notification_preferences FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own notification preferences"
    ON notification_preferences FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- RLS Policies for notification_logs (read-only for users)
CREATE POLICY "Users can view their own notification logs"
    ON notification_logs FOR SELECT
    USING (user_email = (SELECT email FROM auth.users WHERE id = auth.uid()));

-- Service role can access all notification data
CREATE POLICY "Service role can access all notification preferences"
    ON notification_preferences FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can access all notification logs"
    ON notification_logs FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- Create function to auto-create notification preferences for new users
CREATE OR REPLACE FUNCTION create_default_notification_preferences()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO notification_preferences (user_id, user_email)
    VALUES (NEW.id, NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create default preferences for new users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION create_default_notification_preferences();
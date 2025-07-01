-- Enable pg_net extension for HTTP requests
CREATE EXTENSION IF NOT EXISTS pg_net;

-- Create function to trigger notification when change alert is created
CREATE OR REPLACE FUNCTION trigger_change_alert_notification()
RETURNS TRIGGER AS $$
DECLARE
    user_email_val TEXT;
    user_query TEXT;
    source_url TEXT;
    alert_content TEXT;
    supabase_url TEXT;
    service_key TEXT;
BEGIN
    -- Get user email from user_id
    SELECT email INTO user_email_val
    FROM auth.users 
    WHERE id = NEW.user_id;

    -- Get monitoring details
    SELECT 
        uq.query_text,
        ms.url,
        sc.processed_text
    INTO user_query, source_url, alert_content
    FROM monitored_sources ms
    LEFT JOIN user_queries uq ON ms.user_query_id = uq.id
    LEFT JOIN scraped_content sc ON sc.monitored_source_id = ms.id
    WHERE ms.id = NEW.monitored_source_id
    ORDER BY sc.scraped_at DESC
    LIMIT 1;

    -- Get Supabase configuration (these should be set as environment variables)
    supabase_url := current_setting('app.supabase_url', true);
    service_key := current_setting('app.supabase_service_key', true);

    -- If environment variables are not set, use defaults (for development)
    IF supabase_url IS NULL THEN
        supabase_url := 'https://your-project.supabase.co';
    END IF;

    -- Trigger Edge Function asynchronously using pg_net
    PERFORM net.http_post(
        url := supabase_url || '/functions/v1/send-notification',
        headers := jsonb_build_object(
            'Content-Type', 'application/json',
            'Authorization', 'Bearer ' || COALESCE(service_key, 'your-service-key')
        ),
        body := jsonb_build_object(
            'user_email', user_email_val,
            'query', COALESCE(user_query, 'Content monitoring'),
            'target_url', COALESCE(source_url, 'Unknown source'),
            'content', COALESCE(alert_content, NEW.change_summary),
            'alert_id', NEW.id::text
        )
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on change_alerts table
CREATE TRIGGER on_change_alert_created
    AFTER INSERT ON change_alerts
    FOR EACH ROW
    EXECUTE FUNCTION trigger_change_alert_notification();

-- Create function to handle manual notification sending
CREATE OR REPLACE FUNCTION send_notification_manual(
    p_alert_id UUID,
    p_notification_type TEXT DEFAULT 'email'
)
RETURNS JSONB AS $$
DECLARE
    alert_record RECORD;
    user_email_val TEXT;
    user_query TEXT;
    source_url TEXT;
    alert_content TEXT;
    supabase_url TEXT;
    service_key TEXT;
    result JSONB;
BEGIN
    -- Get alert details
    SELECT ca.*, sc.processed_text
    INTO alert_record
    FROM change_alerts ca
    LEFT JOIN monitored_sources ms ON ca.monitored_source_id = ms.id
    LEFT JOIN scraped_content sc ON sc.monitored_source_id = ms.id
    WHERE ca.id = p_alert_id
    ORDER BY sc.scraped_at DESC
    LIMIT 1;

    IF NOT FOUND THEN
        RETURN jsonb_build_object('success', false, 'error', 'Alert not found');
    END IF;

    -- Get user email
    SELECT email INTO user_email_val
    FROM auth.users 
    WHERE id = alert_record.user_id;

    -- Get monitoring details
    SELECT 
        uq.query_text,
        ms.url
    INTO user_query, source_url
    FROM monitored_sources ms
    LEFT JOIN user_queries uq ON ms.user_query_id = uq.id
    WHERE ms.id = alert_record.monitored_source_id;

    -- Get Supabase configuration
    supabase_url := current_setting('app.supabase_url', true);
    service_key := current_setting('app.supabase_service_key', true);

    IF supabase_url IS NULL THEN
        supabase_url := 'https://your-project.supabase.co';
    END IF;

    -- Send notification
    PERFORM net.http_post(
        url := supabase_url || '/functions/v1/send-notification',
        headers := jsonb_build_object(
            'Content-Type', 'application/json',
            'Authorization', 'Bearer ' || COALESCE(service_key, 'your-service-key')
        ),
        body := jsonb_build_object(
            'user_email', user_email_val,
            'query', COALESCE(user_query, 'Content monitoring'),
            'target_url', COALESCE(source_url, 'Unknown source'),
            'content', COALESCE(alert_record.processed_text, alert_record.change_summary),
            'alert_id', p_alert_id::text
        )
    );

    -- Update retry count
    UPDATE change_alerts 
    SET notification_retry_count = notification_retry_count + 1
    WHERE id = p_alert_id;

    RETURN jsonb_build_object(
        'success', true, 
        'message', 'Notification triggered',
        'alert_id', p_alert_id
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to get notification stats
CREATE OR REPLACE FUNCTION get_notification_stats(p_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    total_alerts INTEGER;
    sent_notifications INTEGER;
    failed_notifications INTEGER;
    pending_notifications INTEGER;
BEGIN
    -- Get alert counts
    SELECT COUNT(*) INTO total_alerts
    FROM change_alerts
    WHERE user_id = p_user_id;

    SELECT COUNT(*) INTO sent_notifications
    FROM notification_logs nl
    WHERE nl.user_email = (SELECT email FROM auth.users WHERE id = p_user_id)
    AND nl.status = 'sent';

    SELECT COUNT(*) INTO failed_notifications
    FROM notification_logs nl
    WHERE nl.user_email = (SELECT email FROM auth.users WHERE id = p_user_id)
    AND nl.status = 'failed';

    SELECT COUNT(*) INTO pending_notifications
    FROM change_alerts ca
    WHERE ca.user_id = p_user_id
    AND ca.notification_sent = false;

    RETURN jsonb_build_object(
        'total_alerts', total_alerts,
        'sent_notifications', sent_notifications,
        'failed_notifications', failed_notifications,
        'pending_notifications', pending_notifications
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
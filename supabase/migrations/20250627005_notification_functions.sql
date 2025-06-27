-- Create a simple trigger that marks alerts for processing
CREATE OR REPLACE FUNCTION mark_alert_for_notification()
RETURNS TRIGGER AS $$
BEGIN
    -- The Python backend will pick up alerts where notification_sent = false
    -- This trigger just ensures the flag is set correctly
    NEW.notification_sent = false;
    NEW.notification_sent_at = NULL;
    NEW.notification_retry_count = 0;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for new alerts
DROP TRIGGER IF EXISTS on_change_alert_created ON change_alerts;
CREATE TRIGGER on_change_alert_created
    BEFORE INSERT ON change_alerts
    FOR EACH ROW
    EXECUTE FUNCTION mark_alert_for_notification();

-- Create function to manually trigger notification processing
CREATE OR REPLACE FUNCTION queue_notification_processing(p_alert_id UUID)
RETURNS JSONB AS $$
BEGIN
    -- Reset notification status to queue for reprocessing
    UPDATE change_alerts 
    SET 
        notification_sent = false,
        notification_sent_at = NULL,
        notification_retry_count = COALESCE(notification_retry_count, 0) + 1
    WHERE id = p_alert_id;
    
    RETURN jsonb_build_object(
        'success', true,
        'message', 'Alert queued for notification processing',
        'alert_id', p_alert_id
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to get pending notification count
CREATE OR REPLACE FUNCTION get_pending_notification_count()
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)::INTEGER
        FROM change_alerts
        WHERE notification_sent = false
        AND is_acknowledged = false
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to get notification queue status
CREATE OR REPLACE FUNCTION get_notification_queue_status()
RETURNS JSONB AS $$
DECLARE
    pending_count INTEGER;
    failed_today INTEGER;
    sent_today INTEGER;
BEGIN
    -- Count pending notifications
    SELECT COUNT(*)::INTEGER INTO pending_count
    FROM change_alerts
    WHERE notification_sent = false
    AND is_acknowledged = false;
    
    -- Count failed notifications in last 24 hours
    SELECT COUNT(*)::INTEGER INTO failed_today
    FROM notification_logs
    WHERE status = 'failed'
    AND sent_at > NOW() - INTERVAL '24 hours';
    
    -- Count successful notifications in last 24 hours
    SELECT COUNT(*)::INTEGER INTO sent_today
    FROM notification_logs
    WHERE status = 'sent'
    AND sent_at > NOW() - INTERVAL '24 hours';
    
    RETURN jsonb_build_object(
        'pending_count', pending_count,
        'failed_today', failed_today,
        'sent_today', sent_today,
        'checked_at', NOW()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to get notification stats for a user
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

-- Create index for efficient notification processing
CREATE INDEX IF NOT EXISTS idx_change_alerts_notification_queue 
ON change_alerts (notification_sent, is_acknowledged, detected_at) 
WHERE notification_sent = false AND is_acknowledged = false;

-- Create index for retry logic
CREATE INDEX IF NOT EXISTS idx_change_alerts_retry_count 
ON change_alerts (notification_retry_count, notification_sent) 
WHERE notification_sent = false;

-- Grant necessary permissions for RLS policies
GRANT EXECUTE ON FUNCTION queue_notification_processing(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_pending_notification_count() TO authenticated;
GRANT EXECUTE ON FUNCTION get_notification_queue_status() TO authenticated;
GRANT EXECUTE ON FUNCTION get_notification_stats(UUID) TO authenticated;
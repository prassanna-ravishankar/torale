# Supabase-Native Notifications

## Overview

Torale now uses Supabase's native capabilities for handling notifications instead of a separate microservice. This provides better performance, simpler architecture, and real-time capabilities.

## Architecture

```
Change Detection → Database Trigger → Edge Function → Email Provider
                ↘ Realtime → Browser Notifications
```

### Components

1. **Database Triggers**: Automatically fire when new alerts are created
2. **Edge Functions**: Handle email sending via SendGrid/Resend
3. **Realtime Subscriptions**: Instant browser notifications via WebSocket
4. **Notification Preferences**: User-configurable settings with RLS
5. **Notification Logs**: Audit trail for all notification attempts

## Database Schema

### notification_preferences
```sql
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    user_email TEXT NOT NULL,
    email_enabled BOOLEAN DEFAULT true,
    email_frequency TEXT DEFAULT 'immediate',
    browser_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### notification_logs
```sql
CREATE TABLE notification_logs (
    id UUID PRIMARY KEY,
    alert_id UUID REFERENCES change_alerts(id),
    user_email TEXT NOT NULL,
    notification_type TEXT CHECK (notification_type IN ('email', 'browser', 'webhook')),
    status TEXT CHECK (status IN ('sent', 'failed', 'pending')),
    provider TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    response_code INTEGER,
    metadata JSONB,
    error_message TEXT
);
```

## Edge Function

### Location
`supabase/functions/send-notification/index.ts`

### Features
- **Multi-provider support**: SendGrid and Resend
- **Rich HTML emails**: Beautiful, responsive email templates
- **Notification preferences**: Respects user settings
- **Audit logging**: Tracks all notification attempts
- **Error handling**: Graceful failure and retry tracking

### Environment Variables
- `SENDGRID_API_KEY` or `RESEND_API_KEY`: Email provider API key
- `EMAIL_PROVIDER`: 'sendgrid' or 'resend' (defaults to 'resend')

## Database Triggers

### Automatic Notifications
```sql
CREATE TRIGGER on_change_alert_created
    AFTER INSERT ON change_alerts
    FOR EACH ROW
    EXECUTE FUNCTION trigger_change_alert_notification();
```

### Manual Notifications
```sql
SELECT send_notification_manual('alert-uuid-here');
```

## Frontend Integration

### Real-time Subscriptions
```typescript
// Subscribe to new alerts
const channel = supabase
  .channel('change_alerts')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'change_alerts',
    filter: `user_id=eq.${user.id}`
  }, (payload) => {
    // Handle new alert
    showBrowserNotification(payload.new)
  })
  .subscribe()
```

### Hook Usage
```typescript
import { useNotifications } from '@/hooks/useNotifications'

function MyComponent() {
  const { 
    alerts, 
    preferences, 
    updatePreferences,
    acknowledgeAlert 
  } = useNotifications()
  
  // Component logic
}
```

## Deployment

### 1. Database Migrations
Run the SQL migrations:
```bash
# Apply notification tables
psql -d your_db < supabase/migrations/20240627_create_notification_tables.sql

# Apply triggers
psql -d your_db < supabase/migrations/20240627_create_notification_triggers.sql
```

### 2. Deploy Edge Function
```bash
# Deploy the notification function
supabase functions deploy send-notification

# Set environment variables
supabase secrets set SENDGRID_API_KEY=your_key_here
supabase secrets set EMAIL_PROVIDER=sendgrid
```

### 3. Configure Database Settings
```sql
-- Set Supabase configuration for triggers
ALTER DATABASE your_db SET app.supabase_url = 'https://your-project.supabase.co';
ALTER DATABASE your_db SET app.supabase_service_key = 'your-service-key';
```

## Features

### Email Notifications
- ✅ **Rich HTML templates** with responsive design
- ✅ **Content preview** with proper truncation
- ✅ **Multi-provider support** (SendGrid, Resend)
- ✅ **User preferences** with frequency controls
- ✅ **Delivery tracking** and error logging

### Browser Notifications
- ✅ **Real-time delivery** via Supabase Realtime
- ✅ **Permission management** with user controls
- ✅ **Custom notification content** and actions
- ✅ **Notification grouping** by alert type

### Management Features
- ✅ **Notification preferences** per user
- ✅ **Manual retry** for failed notifications
- ✅ **Delivery statistics** and analytics
- ✅ **Audit logging** for compliance

## Benefits vs Microservice

### Performance
- **Zero network latency** for database operations
- **Instant triggers** on data changes
- **Real-time subscriptions** for browser notifications

### Simplicity
- **One less service** to maintain and deploy
- **Integrated security** with Supabase Auth and RLS
- **Unified logging** and monitoring

### Cost Efficiency
- **No separate infrastructure** costs
- **Included in Supabase** pricing
- **Auto-scaling** Edge Functions

### Developer Experience
- **Type-safe** client integration
- **Real-time by default** with subscriptions
- **Built-in auth context** in functions

## Monitoring

### Health Checks
```sql
-- Check notification stats
SELECT get_notification_stats('user-uuid');

-- View recent logs
SELECT * FROM notification_logs 
WHERE sent_at > NOW() - INTERVAL '1 hour'
ORDER BY sent_at DESC;
```

### Metrics
- **Delivery rate**: Successful notifications / Total attempts
- **Response times**: Edge Function execution times
- **Error rate**: Failed notifications / Total attempts
- **User engagement**: Acknowledgment rates

## Future Enhancements

### Planned Features
- 📱 **SMS notifications** via Twilio integration
- 📱 **Push notifications** for mobile apps  
- 🔗 **Webhook delivery** for external integrations
- 📊 **Advanced analytics** and reporting
- 🎨 **Custom email templates** per user
- ⏰ **Scheduled notifications** with batching
- 🔄 **Retry policies** with exponential backoff
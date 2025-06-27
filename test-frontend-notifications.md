# Frontend Notification Integration Test Guide

## Testing Steps

### 1. Start All Services
```bash
# Terminal 1 - Start microservices
./start-microservices.sh

# Terminal 2 - Start frontend
cd frontend
npm run dev
```

### 2. Test Notification Preferences UI

1. **Sign In**
   - Navigate to http://localhost:3000
   - Sign in with your test account

2. **Access Settings**
   - Click "Settings" in the navigation menu
   - You should see three sections:
     - Profile Information
     - Notification Preferences
     - Account Actions

3. **Test Email Notifications Toggle**
   - Toggle "Email Notifications" on/off
   - Should see "Saving preferences..." briefly
   - When enabled, email frequency options should appear
   - Test switching between: Immediate, Hourly, Daily

4. **Test Browser Notifications**
   - Toggle "Browser Notifications" on
   - If first time: Browser permission prompt should appear
   - Accept the permission
   - Toggle should reflect the enabled state

5. **Verify API Calls**
   - Open browser DevTools (F12)
   - Check Network tab for API calls:
     - GET `/api/v1/notifications/preferences` - Should load preferences
     - PUT `/api/v1/notifications/preferences` - Should update when toggling

### 3. Test Real-time Notifications

1. **Enable Browser Notifications**
   - Ensure browser notifications are enabled in settings

2. **Create a Test Alert**
   - Go to Sources page
   - Create a new monitored source
   - Wait for change detection to trigger

3. **Verify Notification Display**
   - Should see browser notification popup
   - Alert should appear in Alerts page in real-time

### 4. Common Issues & Solutions

**Issue: "Error loading notification preferences"**
- Check that all microservices are running
- Verify backend is accessible at http://localhost:8000
- Check browser console for detailed errors

**Issue: Browser notifications not working**
- Ensure HTTPS or localhost (browsers block notifications on HTTP)
- Check browser notification permissions in settings
- Try different browser if issues persist

**Issue: Preferences not saving**
- Check notification service logs: `docker logs notification-service`
- Verify Supabase connection in notification service
- Check for SendGrid API key configuration

### 5. Database Verification

Check if preferences are stored correctly:

```sql
-- In Supabase SQL Editor
SELECT * FROM notification_preferences WHERE user_id = 'YOUR_USER_ID';
```

Should see:
- `email_enabled`: true/false
- `email_frequency`: immediate/hourly/daily
- `browser_enabled`: true/false

## Success Criteria

✅ Settings page loads without errors
✅ Notification preferences component displays current settings
✅ Email toggle works and shows/hides frequency options
✅ Browser notification toggle works and requests permission
✅ Changes persist after page refresh
✅ Real-time alerts trigger browser notifications when enabled
✅ API calls complete successfully (check Network tab)
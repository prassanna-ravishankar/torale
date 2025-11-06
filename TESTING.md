# Admin Console Testing Guide

## Prerequisites
1. Set admin role in Clerk Dashboard:
   - Go to https://dashboard.clerk.com → Users
   - Find your user account
   - Edit User → Public metadata
   - Add: `{"role": "admin"}`
   - Save

## Backend Testing

### 1. Start Backend
```bash
cd backend
uv run uvicorn torale.api.main:app --reload
```

### 2. Test Admin Endpoints (requires admin user token)
```bash
# Get your Clerk token from browser DevTools (Application → Local Storage)
TOKEN="your-clerk-jwt-token"

# Test stats endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/stats

# Test queries endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/queries?limit=10

# Test executions endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/executions?limit=10

# Test users endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/users

# Test errors endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/errors

# Test Temporal endpoints
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/temporal/workflows
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/temporal/schedules
```

### 3. Test Non-Admin Access (should return 403)
```bash
# Use a non-admin user token
curl -H "Authorization: Bearer $NON_ADMIN_TOKEN" http://localhost:8000/admin/stats
# Expected: {"detail":"Admin access required"}
```

## Frontend Testing

### 1. Start Frontend
```bash
cd frontend
npm run dev
```

### 2. Manual UI Testing Checklist

**Navigation:**
- [ ] Login with admin user
- [ ] Verify "Admin" button appears in header
- [ ] Click "Admin" button → navigates to /admin
- [ ] Verify admin button is highlighted when on /admin page
- [ ] Login with non-admin user → Admin button should NOT appear
- [ ] Navigate to /admin as non-admin → should redirect to /

**Overview Tab:**
- [ ] User capacity card shows correct values
- [ ] Active tasks card shows task count
- [ ] 24h executions card shows execution stats
- [ ] Success rate card displays percentage
- [ ] Popular queries list displays (if data exists)

**Queries Tab:**
- [ ] Table loads and displays user queries
- [ ] "Active only" toggle filters correctly
- [ ] All columns display: user, name, query, condition, schedule, status, executions, triggered
- [ ] Status badges show correct colors (active/inactive, met/not met)
- [ ] Email addresses are properly formatted

**Executions Tab:**
- [ ] Table loads and displays executions
- [ ] Status filter dropdown works (all/success/failed/running)
- [ ] All columns display correctly
- [ ] Time stamps show "X ago" format
- [ ] Duration calculated correctly
- [ ] Grounding sources count displays

**Temporal Tab:**
- [ ] Workflows tab loads and shows recent workflows
- [ ] Schedules tab loads and shows active schedules
- [ ] Status badges have correct colors
- [ ] Workflow IDs and types display
- [ ] Cron specs show in schedules

**Errors Tab:**
- [ ] Error list loads
- [ ] Shows "No recent errors" when healthy
- [ ] Error cards display user email, query, error message
- [ ] Timestamps show relative time
- [ ] Task IDs are displayed

**Users Tab:**
- [ ] Capacity card shows used/total/available
- [ ] Users table loads with all users
- [ ] All stats display: tasks, executions, triggered count
- [ ] "Deactivate" button only shows for active users
- [ ] Clicking deactivate shows confirmation dialog
- [ ] Deactivating user updates UI and capacity count

## Integration Testing

### Test Complete Flow:
1. Create a task as a regular user
2. Switch to admin account
3. Verify task appears in "Queries" tab
4. Execute the task manually
5. Verify execution appears in "Executions" tab
6. Check Temporal tab shows the workflow
7. If task fails, verify it appears in "Errors" tab
8. Test user deactivation:
   - Note current capacity (e.g., 87/100)
   - Deactivate a user
   - Verify capacity updates (e.g., 86/100)
   - Verify user's tasks are deactivated

## Expected Behavior

### Security:
- ✓ Non-admin users cannot access /admin endpoints (403 Forbidden)
- ✓ Non-admin users redirected to / when visiting /admin page
- ✓ Admin link only visible to admin users
- ✓ All admin API calls require valid Clerk JWT

### Performance:
- ✓ Stats load within 1-2 seconds
- ✓ Tables load within 2-3 seconds (with typical data)
- ✓ No console errors
- ✓ No TypeScript errors

### Data Accuracy:
- ✓ User counts match database
- ✓ Task counts are accurate
- ✓ Execution stats correctly aggregated
- ✓ Popular queries sorted by count
- ✓ Temporal data syncs with Temporal UI

## Known Limitations

1. **Temporal Workflows**: Limited to last 24 hours (last 100 workflows)
2. **Schedules**: Next run time not calculated (would require cron parsing)
3. **Real-time Updates**: No auto-refresh (manual page refresh required)
4. **Pagination**: Fixed limits (can be adjusted via query params)

## Troubleshooting

**"Admin access required" error:**
- Verify `publicMetadata.role === "admin"` in Clerk
- Check JWT token is valid
- Ensure clerk_secret_key is set in backend

**Empty data in admin console:**
- Create some tasks as a regular user first
- Execute tasks to generate execution history
- Temporal data only shows if Temporal is running

**TypeScript errors:**
- Run `npm install` in frontend directory
- Check all shadcn/ui components are installed
- Verify date-fns is in package.json

**Import errors in backend:**
- Ensure in virtual environment: `uv sync`
- Check all dependencies installed
- Verify Python version >= 3.10

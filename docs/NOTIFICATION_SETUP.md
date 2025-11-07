# Notification System Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd backend
uv sync
```

The `novu>=1.6.0` package is already in `pyproject.toml`.

### 2. Run Database Migration

```bash
# Start database
docker compose up -d postgres

# Run migration (if services running)
docker compose exec api alembic upgrade head

# OR start fresh
docker compose down -v
docker compose up -d
```

### 3. Configure Environment Variables

Add to `.env`:

```bash
# Novu Cloud (optional - system works without it)
NOVU_SECRET_KEY=your_key_from_novu_dashboard
NOVU_WORKFLOW_ID=torale-condition-met
NOVU_VERIFICATION_WORKFLOW_ID=torale-email-verification
```

### 4. Create Novu Workflows (Optional)

Only needed if you want email notifications via Novu Cloud.

**Sign up:** https://novu.co

**Create Workflow 1: torale-condition-met**
1. Go to Workflows → Create Workflow
2. Name: "Torale Condition Met"
3. Identifier: `torale-condition-met`
4. Add Email channel
5. Use template from `docs/NOTIFICATIONS.md`

**Create Workflow 2: torale-email-verification**
1. Go to Workflows → Create Workflow
2. Name: "Torale Email Verification"
3. Identifier: `torale-email-verification`
4. Add Email channel
5. Use template from `docs/NOTIFICATIONS.md`

### 5. Test the System

```bash
# Run notification tests
cd backend
python scripts/test_notifications.py
```

Expected output:
```
✓ Generated code: 123456
✓ Code format valid
✓ Generated secret: abc123...
✓ Signature verification: True
✓ Created payload: task.condition_met
⚠ Novu not configured (expected in development)
✅ All tests passed!
```

## Development Workflow

### Without Novu (Email Disabled)

The system works perfectly without Novu configured:
- Webhook notifications work normally
- Email verification codes printed to console
- No emails sent (development mode)

```bash
# Don't set NOVU_SECRET_KEY
# System logs: "Novu not configured - notifications disabled"
```

### With Novu (Email Enabled)

Full email functionality:
- Verification codes sent via email
- Condition notifications sent via email
- Webhooks work as well

```bash
# Set NOVU_SECRET_KEY in .env
# System logs: "Novu service initialized successfully"
```

## API Testing

### Test Email Verification

```bash
# Send verification code
curl -X POST http://localhost:8000/api/v1/email-verification/send \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Response includes code (development only)
# {"message": "...", "code": "123456"}

# Verify code
curl -X POST http://localhost:8000/api/v1/email-verification/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "code": "123456"}'
```

### Test Webhook Configuration

```bash
# Get webhook config
curl http://localhost:8000/api/v1/webhooks/config

# Update webhook config
curl -X PUT http://localhost:8000/api/v1/webhooks/config \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://webhook.site/your-id",
    "enabled": true
  }'

# Response includes generated secret
# {"success": true, "webhook_secret": "abc123..."}

# Test webhook delivery
curl -X POST http://localhost:8000/api/v1/webhooks/test \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://webhook.site/your-id",
    "webhook_secret": "abc123..."
  }'
```

### Test Task with Notifications

```bash
# Create task with email and webhook notifications
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Notification",
    "schedule": "0 9 * * *",
    "executor_type": "llm_grounded_search",
    "search_query": "When is next iPhone release?",
    "condition_description": "Release date announced",
    "notify_behavior": "once",
    "notification_channels": ["email", "webhook"],
    "webhook_url": "https://webhook.site/your-id",
    "config": {"model": "gemini-2.0-flash-exp"}
  }'

# Trigger manual execution
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/execute

# Check webhook deliveries
curl http://localhost:8000/api/v1/webhooks/deliveries?task_id={task_id}
```

## Production Deployment

### 1. Add Kubernetes Secrets

```bash
# Create Novu secret
kubectl create secret generic novu-secret \
  --from-literal=NOVU_SECRET_KEY=your_production_key \
  -n torale

# Update deployment to reference secret
# (Already configured in helm/torale/values.yaml)
```

### 2. Deploy

```bash
# Migration runs automatically via init container
git push origin main

# Or manually
just k8s-deploy-all
```

### 3. Verify

```bash
# Check API logs
kubectl logs -n torale deploy/torale-api | grep -i novu

# Should see:
# "Novu service initialized successfully"

# Check worker logs
kubectl logs -n torale deploy/torale-workers | grep -i notification

# Check migration
kubectl logs -n torale deploy/torale-api -c init-migrations
```

## Troubleshooting

### "Novu not configured" in logs

**Expected in development** if you haven't set `NOVU_SECRET_KEY`.

To enable:
1. Sign up at https://novu.co
2. Get API key from dashboard
3. Add to `.env`: `NOVU_SECRET_KEY=your_key`
4. Create workflows in Novu dashboard
5. Restart services

### "novu package not installed"

```bash
cd backend
uv sync
# or
uv add novu
```

### Email verification code not appearing

**Without Novu:** Check console logs - code is printed there in development.

**With Novu:** Check spam folder, verify workflow exists in Novu dashboard.

### Webhook signature verification failing

- Ensure you're using the secret returned when enabling webhooks
- Check timestamp tolerance (5 minutes by default)
- Verify payload hasn't been modified
- Use timing-safe comparison (see docs/NOTIFICATIONS.md)

### Migration fails

```bash
# Start fresh
docker compose down -v
docker compose up -d postgres
docker compose up -d api

# Check migration status
docker compose exec api alembic current
docker compose exec api alembic history

# Manually run migration
docker compose exec api alembic upgrade head
```

### Rate limit hit

**Daily limit (100/day per user):**
- Wait until next day
- Or increase limit in `EmailVerificationService.check_spam_limits()`

**Hourly limit (10/hour per email):**
- Wait one hour
- Or increase limit in `EmailVerificationService.check_spam_limits()`

## Next Steps

1. **Configure Novu** - Sign up and create workflows for email notifications
2. **Test webhooks** - Use webhook.site or requestbin.com to test payload delivery
3. **Add frontend** - Build UI for email verification and webhook configuration
4. **Monitor usage** - Query `notification_sends` table for usage stats
5. **Set up alerts** - Monitor for spam patterns or high failure rates

## Support

- **Documentation:** `docs/NOTIFICATIONS.md`
- **Test Script:** `backend/scripts/test_notifications.py`
- **API Reference:** http://localhost:8000/docs
- **Novu Docs:** https://docs.novu.co

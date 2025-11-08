# Torale Notification System

## Overview

Torale supports multi-channel notifications with email validation to prevent spam and webhook support for custom integrations.

## Features

- **Email Notifications** via Novu Cloud
- **Webhook Notifications** with HMAC-SHA256 signing
- **Email Verification** to prevent spam abuse
- **Rate Limiting** (100/day per user, 10/hour per email)
- **Spam Protection** with verified email requirements

## Notification Channels

### Email (via Novu Cloud)

**Setup:**
1. Create account at https://novu.co
2. Get API key from dashboard
3. Add to `.env`: `NOVU_SECRET_KEY=your_key`
4. Create workflows in Novu dashboard (see below)

**Workflows Required:**
1. `torale-condition-met` - Main notification when task triggers
2. `torale-email-verification` - Email verification codes

### Webhooks

**Setup:**
1. Configure webhook URL in user settings or per-task
2. Receive HMAC-signed webhooks when conditions are met
3. Verify signatures for security

**Webhook Payload:**
```json
{
  "id": "exec_123",
  "event_type": "task.condition_met",
  "created_at": 1699564800,
  "object": "event",
  "api_version": "v1",
  "data": {
    "task": {
      "id": "task_456",
      "name": "iPhone Release Monitor",
      "search_query": "When is next iPhone release?",
      "condition_description": "Release date announced"
    },
    "execution": {
      "id": "exec_123",
      "condition_met": true,
      "change_summary": "Apple announced September 12th release",
      "completed_at": "2024-11-09T10:30:00Z"
    },
    "result": {
      "answer": "The next iPhone will be released on September 12th, 2024",
      "grounding_sources": [...]
    }
  }
}
```

**Webhook Headers:**
```
Content-Type: application/json
User-Agent: Torale-Webhooks/1.0
X-Torale-Event: task.condition_met
X-Torale-Signature: t=1699564800,v1=abc123...
X-Torale-Delivery: exec_123
X-Torale-Timestamp: 1699564800
```

## Email Verification

To prevent spam, custom notification emails must be verified before use.

**Verification Flow:**
1. User adds email in settings
2. System sends 6-digit verification code
3. User enters code (15-minute expiry, 5 attempts max)
4. Email added to verified list

**Clerk Email Bypass:**
Emails from Clerk OAuth are pre-verified and work immediately.

**Rate Limits:**
- Max 3 verification emails per hour
- Max 5 code attempts before requiring new code

## Webhook Signature Verification

**Python Example:**
```python
import hmac
import hashlib
import time

def verify_webhook(payload, signature_header, secret):
    # Parse signature
    parts = dict(p.split('=') for p in signature_header.split(','))
    timestamp = int(parts['t'])
    expected_sig = parts['v1']

    # Check timestamp (prevent replay attacks)
    if abs(time.time() - timestamp) > 300:  # 5 minutes
        return False

    # Verify signature
    signed_payload = f"{timestamp}.{payload}"
    computed_sig = hmac.new(
        secret.encode(),
        signed_payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_sig, expected_sig)
```

## Spam Protection

**Rate Limits:**
- 100 notifications per day per user
- 10 notifications per hour to same email address

**Email Validation:**
- Only verified emails can receive notifications
- Clerk emails are automatically verified
- Custom emails require verification code

**Webhook Retries:**
- Failed webhooks retry 3 times (1min, 5min, 15min)
- After 3 failures, marked as permanently failed

## API Endpoints

### Email Verification
```
POST   /api/v1/email-verification/send        # Send verification code
POST   /api/v1/email-verification/verify      # Verify code
GET    /api/v1/email-verification/verified-emails  # List verified emails
DELETE /api/v1/email-verification/verified-emails/{email}  # Remove email
```

### Webhooks
```
GET    /api/v1/webhooks/config            # Get webhook config
PUT    /api/v1/webhooks/config            # Update webhook config
POST   /api/v1/webhooks/test              # Test webhook delivery
POST   /api/v1/webhooks/verify            # Webhook verification endpoint
GET    /api/v1/webhooks/deliveries        # Webhook delivery history
```

## Testing

**Run test script:**
```bash
cd backend
python scripts/test_notifications.py
```

**Manual webhook test:**
```bash
# Create webhook at https://webhook.site
# Copy URL and secret
curl -X POST http://localhost:8000/api/v1/webhooks/test \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://webhook.site/your-id",
    "webhook_secret": "your-secret"
  }'
```

## Troubleshooting

**Email not sending:**
- Check `NOVU_SECRET_KEY` is set
- Verify workflows exist in Novu dashboard
- Check logs: `docker compose logs api | grep -i novu`

**Webhook failing:**
- Verify URL is HTTPS (required for security)
- Check webhook secret matches
- Review delivery history at `/api/v1/webhooks/deliveries`
- Check endpoint logs for errors

**Verification code not working:**
- Code expires after 15 minutes
- Max 5 attempts before needing new code
- Check spam folder for verification email

## Database Tables

**email_verifications:**
- Stores verification codes and attempts
- Auto-expires after 15 minutes

**notification_sends:**
- Tracks all notification sends for rate limiting
- Used to detect spam patterns

**webhook_deliveries:**
- Stores all webhook delivery attempts
- Includes retry schedule and error messages

## Migration

**Run migration:**
```bash
# Local
docker compose down -v
docker compose up -d postgres
docker compose exec api alembic upgrade head

# Production (automatic via init container)
git push origin main
```

## Environment Variables

```bash
# Novu Cloud (optional)
NOVU_SECRET_KEY=                        # Get from novu.co dashboard
NOVU_WORKFLOW_ID=torale-condition-met   # Main notification workflow
NOVU_VERIFICATION_WORKFLOW_ID=torale-email-verification  # Verification workflow
```

## Novu Workflow Templates

### Condition Met Workflow

**Setup Steps:**
1. Create workflow with identifier: `torale-condition-met`
2. Add Email channel
3. **Define payload schema first** (click "Payload" or "Variables" in workflow editor):
   ```json
   {
     "task_name": "string",
     "search_query": "string",
     "answer": "string",
     "change_summary": "string",
     "grounding_sources": "array",
     "task_id": "string",
     "execution_id": "string"
   }
   ```
4. Configure Email step:

**Subject:**
```
{{payload.task_name}} - Condition Met!
```

**Body:**
```
Hi there!

Your Torale monitoring task "{{payload.task_name}}" has detected a match.

**What you asked:**
{{payload.search_query}}

**What we found:**
{{payload.answer}}

{% if payload.change_summary %}
**What changed:**
{{payload.change_summary}}
{% endif %}

**Sources:**
{% for source in payload.grounding_sources %}
- {{source.title}}: {{source.uri}}
{% endfor %}

View details: https://torale.ai/tasks/{{payload.task_id}}

---
Sent by Torale Monitoring
```

### Email Verification Workflow

**Setup Steps:**
1. Create workflow with identifier: `torale-email-verification`
2. Add Email channel
3. **Define payload schema first**:
   ```json
   {
     "code": "string",
     "user_name": "string",
     "expires_in_minutes": "number"
   }
   ```
4. Configure Email step:

**Subject:**
```
Verify your email for Torale notifications
```

**Body:**
```
Your verification code is: {{payload.code}}

This code expires in {{payload.expires_in_minutes}} minutes.

If you didn't request this, ignore this email.

---
Torale
```

**Note:** Novu requires you to define payload variables before you can use them in templates. Always set up the payload schema first to avoid "Variable invalid or missing namespace" errors.

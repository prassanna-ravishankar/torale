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

**Body (HTML - recommended):**
```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
  </head>
  <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
      <tr>
        <td align="center" style="padding: 40px 0;">
          <table role="presentation" style="width: 600px; max-width: 100%; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <!-- Header -->
            <tr>
              <td style="padding: 32px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600;">
                  🎯 Condition Met!
                </h1>
                <p style="margin: 8px 0 0 0; color: #e0e7ff; font-size: 16px;">
                  {{payload.task_name}}
                </p>
              </td>
            </tr>

            <!-- Content -->
            <tr>
              <td style="padding: 40px;">
                <p style="margin: 0 0 24px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                  Your Torale monitoring task has detected a match. Here's what we found:
                </p>

                <!-- What you asked -->
                <div style="margin: 0 0 24px 0; padding: 20px; background-color: #f9fafb; border-left: 4px solid #667eea; border-radius: 4px;">
                  <h2 style="margin: 0 0 8px 0; color: #667eea; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                    What you asked
                  </h2>
                  <p style="margin: 0; color: #1f2937; font-size: 15px; line-height: 1.6;">
                    {{payload.search_query}}
                  </p>
                </div>

                <!-- What we found -->
                <div style="margin: 0 0 24px 0; padding: 20px; background-color: #f0fdf4; border-left: 4px solid #10b981; border-radius: 4px;">
                  <h2 style="margin: 0 0 8px 0; color: #10b981; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                    What we found
                  </h2>
                  <p style="margin: 0; color: #1f2937; font-size: 15px; line-height: 1.6;">
                    {{payload.answer}}
                  </p>
                </div>

                <!-- What changed -->
                {% if payload.change_summary %}
                <div style="margin: 0 0 24px 0; padding: 20px; background-color: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 4px;">
                  <h2 style="margin: 0 0 8px 0; color: #f59e0b; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                    What changed
                  </h2>
                  <p style="margin: 0; color: #1f2937; font-size: 15px; line-height: 1.6;">
                    {{payload.change_summary}}
                  </p>
                </div>
                {% endif %}

                <!-- Sources -->
                {% if payload.grounding_sources %}
                <div style="margin: 0 0 32px 0;">
                  <h2 style="margin: 0 0 12px 0; color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                    Sources
                  </h2>
                  <ul style="margin: 0; padding: 0; list-style: none;">
                    {% for source in payload.grounding_sources %}
                    <li style="margin: 0 0 8px 0; padding: 12px 16px; background-color: #f9fafb; border-radius: 4px;">
                      <a href="{{source.uri}}" style="color: #667eea; text-decoration: none; font-size: 14px;">
                        <strong>{{source.title}}</strong>
                      </a>
                    </li>
                    {% endfor %}
                  </ul>
                </div>
                {% endif %}

                <!-- CTA Button -->
                <table role="presentation" style="width: 100%;">
                  <tr>
                    <td align="center">
                      <a href="https://torale.ai/tasks/{{payload.task_id}}" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px;">
                        View Full Details
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- Footer -->
            <tr>
              <td style="padding: 24px 40px; background-color: #f9fafb; border-radius: 0 0 8px 8px; border-top: 1px solid #e5e7eb;">
                <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 13px; text-align: center;">
                  Sent by <strong>Torale Monitoring</strong>
                </p>
                <p style="margin: 0; color: #9ca3af; font-size: 12px; text-align: center;">
                  Automated monitoring for the web
                </p>
              </td>
            </tr>
          </table>

          <!-- Unsubscribe footer -->
          <table role="presentation" style="width: 600px; max-width: 100%; margin-top: 24px;">
            <tr>
              <td style="padding: 0 40px; text-align: center;">
                <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                  You're receiving this because you created a monitoring task on Torale.
                  <br>
                  <a href="https://torale.ai/settings/notifications" style="color: #667eea; text-decoration: none;">Manage notification preferences</a>
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
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

**Body (HTML - recommended):**
```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
  </head>
  <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
      <tr>
        <td align="center" style="padding: 40px 0;">
          <table role="presentation" style="width: 600px; max-width: 100%; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <!-- Header -->
            <tr>
              <td style="padding: 32px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600;">
                  🔐 Verify Your Email
                </h1>
                <p style="margin: 8px 0 0 0; color: #e0e7ff; font-size: 16px;">
                  Torale Email Verification
                </p>
              </td>
            </tr>

            <!-- Content -->
            <tr>
              <td style="padding: 40px;">
                <p style="margin: 0 0 24px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                  Hi there! 👋
                </p>

                <p style="margin: 0 0 32px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                  Please use the following verification code to complete your email verification:
                </p>

                <!-- Verification Code -->
                <div style="margin: 0 0 32px 0; text-align: center;">
                  <div style="display: inline-block; padding: 24px 48px; background-color: #f9fafb; border: 2px dashed #667eea; border-radius: 8px;">
                    <p style="margin: 0; color: #667eea; font-size: 36px; font-weight: 700; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                      {{payload.code}}
                    </p>
                  </div>
                </div>

                <!-- Expiry Notice -->
                <div style="margin: 0 0 24px 0; padding: 16px; background-color: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 4px;">
                  <p style="margin: 0; color: #92400e; font-size: 14px;">
                    ⏰ This code expires in <strong>{{payload.expires_in_minutes}} minutes</strong>
                  </p>
                </div>

                <!-- Security Notice -->
                <p style="margin: 0 0 16px 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                  If you didn't request this verification code, you can safely ignore this email.
                </p>
              </td>
            </tr>

            <!-- Footer -->
            <tr>
              <td style="padding: 24px 40px; background-color: #f9fafb; border-radius: 0 0 8px 8px; border-top: 1px solid #e5e7eb;">
                <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 13px; text-align: center;">
                  Sent by <strong>Torale</strong>
                </p>
                <p style="margin: 0; color: #9ca3af; font-size: 12px; text-align: center;">
                  Secure email verification
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
```

**Note:** Novu requires you to define payload variables before you can use them in templates. Always set up the payload schema first to avoid "Variable invalid or missing namespace" errors.

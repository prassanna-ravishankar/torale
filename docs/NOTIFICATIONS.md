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
3. `torale-task-welcome` - Welcome email after task creation

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
NOVU_WELCOME_WORKFLOW_ID=torale-task-welcome  # Welcome email workflow
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
  <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f9fafb;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
      <tr>
        <td align="center" style="padding: 48px 16px;">
          <table role="presentation" style="width: 100%; max-width: 600px; background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.1);">
            <!-- Header with primary brand color -->
            <tr>
              <td style="padding: 32px; background-color: #ffffff; border-bottom: 1px solid #e5e7eb;">
                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                  <tr>
                    <td style="vertical-align: top;">
                      <!-- Icon container matching frontend pattern (h-8 w-8 rounded-lg bg-primary/10) -->
                      <div style="display: inline-block; width: 32px; height: 32px; background-color: rgba(168, 85, 247, 0.1); border-radius: 6px; text-align: center; line-height: 32px; margin-right: 12px;">
                        <span style="color: #a855f7; font-size: 18px;">✓</span>
                      </div>
                    </td>
                    <td style="vertical-align: top;">
                      <h1 style="margin: 0; color: #09090b; font-size: 20px; font-weight: 600; line-height: 1.2;">
                        Condition Met
                      </h1>
                      <p style="margin: 4px 0 0 0; color: #71717a; font-size: 14px; line-height: 1.4;">
                        {{payload.task_name}}
                      </p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- Content -->
            <tr>
              <td style="padding: 32px;">
                <p style="margin: 0 0 24px 0; color: #3f3f46; font-size: 14px; line-height: 1.6;">
                  Your monitoring task has detected a match. Here's what we found:
                </p>

                <!-- What you asked - matching Card pattern with border-left accent -->
                <div style="margin: 0 0 16px 0; padding: 16px; background-color: #f9fafb; border-left: 3px solid #a855f7; border-radius: 6px;">
                  <h2 style="margin: 0 0 8px 0; color: #a855f7; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                    What You Asked
                  </h2>
                  <p style="margin: 0; color: #09090b; font-size: 14px; line-height: 1.6;">
                    {{payload.search_query}}
                  </p>
                </div>

                <!-- What we found - matching success/green state -->
                <div style="margin: 0 0 16px 0; padding: 16px; background-color: #f0fdf4; border-left: 3px solid #22c55e; border-radius: 6px;">
                  <h2 style="margin: 0 0 8px 0; color: #16a34a; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                    What We Found
                  </h2>
                  <p style="margin: 0; color: #09090b; font-size: 14px; line-height: 1.6;">
                    {{payload.answer}}
                  </p>
                </div>

                <!-- What changed - matching warning/yellow state -->
                {% if payload.change_summary %}
                <div style="margin: 0 0 16px 0; padding: 16px; background-color: #fefce8; border-left: 3px solid #eab308; border-radius: 6px;">
                  <h2 style="margin: 0 0 8px 0; color: #ca8a04; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                    What Changed
                  </h2>
                  <p style="margin: 0; color: #09090b; font-size: 14px; line-height: 1.6;">
                    {{payload.change_summary}}
                  </p>
                </div>
                {% endif %}

                <!-- Sources with muted styling -->
                {% if payload.grounding_sources %}
                <div style="margin: 24px 0 0 0;">
                  <h2 style="margin: 0 0 12px 0; color: #71717a; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                    Sources
                  </h2>
                  <div style="display: block;">
                    {% for source in payload.grounding_sources %}
                    <div style="margin: 0 0 8px 0; padding: 12px; background-color: #f9fafb; border-radius: 6px;">
                      <a href="{{source.uri}}" target="_blank" rel="noopener noreferrer" style="color: #a855f7; text-decoration: underline; font-size: 13px; line-height: 1.4; display: block;">
                        {{source.title}}
                      </a>
                      <div style="margin-top: 4px; font-size: 11px; color: #71717a; word-break: break-all;">
                        {{source.uri}}
                      </div>
                    </div>
                    {% endfor %}
                  </div>
                </div>
                {% endif %}

                <!-- CTA Button matching frontend Button component -->
                <div style="margin: 32px 0 0 0; text-align: center;">
                  <a href="https://torale.ai/tasks/{{payload.task_id}}" target="_blank" rel="noopener noreferrer" style="display: inline-block; padding: 10px 24px; background-color: #a855f7; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 14px;">
                    View Full Details
                  </a>
                </div>
              </td>
            </tr>

            <!-- Footer with muted colors -->
            <tr>
              <td style="padding: 24px 32px; background-color: #f9fafb; border-radius: 0 0 8px 8px; border-top: 1px solid #e5e7eb;">
                <p style="margin: 0 0 4px 0; color: #71717a; font-size: 12px; text-align: center; line-height: 1.5;">
                  Sent by <strong style="color: #52525b;">Torale</strong>
                </p>
                <p style="margin: 0; color: #a1a1aa; font-size: 11px; text-align: center; line-height: 1.5;">
                  Automated monitoring for the web
                </p>
              </td>
            </tr>
          </table>

          <!-- Unsubscribe footer -->
          <table role="presentation" style="width: 100%; max-width: 600px; margin-top: 16px;">
            <tr>
              <td style="text-align: center;">
                <p style="margin: 0; color: #a1a1aa; font-size: 11px; line-height: 1.6;">
                  You're receiving this because you created a monitoring task.
                  <br>
                  <a href="https://torale.ai/settings/notifications" style="color: #a855f7; text-decoration: none;">Manage preferences</a>
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
  <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f9fafb;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
      <tr>
        <td align="center" style="padding: 48px 16px;">
          <table role="presentation" style="width: 100%; max-width: 600px; background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.1);">
            <!-- Header -->
            <tr>
              <td style="padding: 32px; background-color: #ffffff; border-bottom: 1px solid #e5e7eb;">
                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                  <tr>
                    <td style="vertical-align: top;">
                      <!-- Icon container matching frontend pattern -->
                      <div style="display: inline-block; width: 32px; height: 32px; background-color: rgba(168, 85, 247, 0.1); border-radius: 6px; text-align: center; line-height: 32px; margin-right: 12px;">
                        <span style="color: #a855f7; font-size: 18px;">🔒</span>
                      </div>
                    </td>
                    <td style="vertical-align: top;">
                      <h1 style="margin: 0; color: #09090b; font-size: 20px; font-weight: 600; line-height: 1.2;">
                        Verify Your Email
                      </h1>
                      <p style="margin: 4px 0 0 0; color: #71717a; font-size: 14px; line-height: 1.4;">
                        Email Verification
                      </p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- Content -->
            <tr>
              <td style="padding: 32px;">
                <p style="margin: 0 0 24px 0; color: #3f3f46; font-size: 14px; line-height: 1.6;">
                  Please use the following verification code to complete your email verification:
                </p>

                <!-- Verification Code with Card-like styling -->
                <div style="margin: 0 0 24px 0; text-align: center;">
                  <div style="display: inline-block; padding: 24px 48px; background-color: #faf5ff; border: 2px dashed #a855f7; border-radius: 8px;">
                    <p style="margin: 0; color: #a855f7; font-size: 32px; font-weight: 700; letter-spacing: 12px; font-family: 'Courier New', monospace;">
                      {{payload.code}}
                    </p>
                  </div>
                </div>

                <!-- Expiry Notice with warning state -->
                <div style="margin: 0 0 24px 0; padding: 16px; background-color: #fefce8; border-left: 3px solid #eab308; border-radius: 6px;">
                  <p style="margin: 0; color: #09090b; font-size: 13px; line-height: 1.6;">
                    <span style="color: #ca8a04;">⚠</span> This code expires in <strong>{{payload.expires_in_minutes}} minutes</strong>
                  </p>
                </div>

                <!-- Security Notice with muted text -->
                <p style="margin: 0; color: #71717a; font-size: 13px; line-height: 1.6;">
                  If you didn't request this verification code, you can safely ignore this email.
                </p>
              </td>
            </tr>

            <!-- Footer -->
            <tr>
              <td style="padding: 24px 32px; background-color: #f9fafb; border-radius: 0 0 8px 8px; border-top: 1px solid #e5e7eb;">
                <p style="margin: 0 0 4px 0; color: #71717a; font-size: 12px; text-align: center; line-height: 1.5;">
                  Sent by <strong style="color: #52525b;">Torale</strong>
                </p>
                <p style="margin: 0; color: #a1a1aa; font-size: 11px; text-align: center; line-height: 1.5;">
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

### Task Welcome Workflow

**Setup Steps:**
1. Create workflow with identifier: `torale-task-welcome`
2. Add Email channel
3. **Define payload schema first**:
   ```json
   {
     "task_name": "string",
     "search_query": "string",
     "condition_description": "string",
     "notify_behavior": "string",
     "schedule_description": "string",
     "first_check_completed": "boolean",
     "answer": "string",
     "condition_met": "boolean",
     "grounding_sources": "array",
     "task_id": "string"
   }
   ```
4. Configure Email step:

**Subject:**
```
✓ {{payload.task_name}} is now monitoring
```

**Body (HTML - recommended):**
```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f9fafb;">
  <table role="presentation" style="width: 100%; border-collapse: collapse;">
    <tr>
      <td align="center" style="padding: 48px 16px;">
        <table role="presentation" style="width: 100%; max-width: 600px; background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px;">

          <!-- Header -->
          <tr>
            <td style="padding: 32px; border-bottom: 1px solid #e5e7eb;">
              <div style="display: inline-block; width: 32px; height: 32px; background-color: rgba(168, 85, 247, 0.1); border-radius: 6px; text-align: center; line-height: 32px; margin-right: 12px;">
                <span style="color: #a855f7; font-size: 18px;">🚀</span>
              </div>
              <h1 style="display: inline; margin: 0; color: #09090b; font-size: 20px; font-weight: 600;">
                Your Task is Live!
              </h1>
              <p style="margin: 8px 0 0 0; color: #71717a; font-size: 14px;">
                {{payload.task_name}}
              </p>
            </td>
          </tr>

          <!-- Content -->
          <tr>
            <td style="padding: 32px;">
              <p style="margin: 0 0 24px 0; color: #3f3f46; font-size: 14px; line-height: 1.6;">
                Great news! We've just completed your first check and your monitoring task is now running.
              </p>

              <!-- What We're Watching -->
              <div style="margin: 0 0 16px 0; padding: 16px; background-color: #f9fafb; border-left: 3px solid #a855f7; border-radius: 6px;">
                <h2 style="margin: 0 0 8px 0; color: #a855f7; font-size: 11px; font-weight: 600; text-transform: uppercase;">
                  What We're Watching
                </h2>
                <p style="margin: 0; color: #09090b; font-size: 14px;">
                  {{payload.search_query}}
                </p>
              </div>

              <!-- When You'll Be Notified -->
              <div style="margin: 0 0 16px 0; padding: 16px; background-color: #f0fdf4; border-left: 3px solid #22c55e; border-radius: 6px;">
                <h2 style="margin: 0 0 8px 0; color: #16a34a; font-size: 11px; font-weight: 600; text-transform: uppercase;">
                  When You'll Be Notified
                </h2>
                <p style="margin: 0; color: #09090b; font-size: 14px;">
                  {{payload.condition_description}}
                </p>
              </div>

              <!-- How Often We Check -->
              <div style="margin: 0 0 24px 0; padding: 16px; background-color: #fefce8; border-left: 3px solid #eab308; border-radius: 6px;">
                <h2 style="margin: 0 0 8px 0; color: #ca8a04; font-size: 11px; font-weight: 600; text-transform: uppercase;">
                  Check Schedule
                </h2>
                <p style="margin: 0; color: #09090b; font-size: 14px;">
                  {{payload.schedule_description}}
                </p>
              </div>

              <!-- First Check Results (if available) -->
              {% if payload.first_check_completed %}
              <div style="margin: 0 0 24px 0; padding: 20px; background-color: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">
                <h2 style="margin: 0 0 16px 0; color: #09090b; font-size: 16px; font-weight: 600;">
                  First Check Results
                </h2>

                {% if payload.condition_met %}
                <div style="margin: 0 0 12px 0; padding: 12px; background-color: #dcfce7; border-radius: 6px;">
                  <p style="margin: 0; color: #16a34a; font-size: 13px; font-weight: 600;">
                    ✓ Condition Already Met!
                  </p>
                </div>
                {% else %}
                <div style="margin: 0 0 12px 0; padding: 12px; background-color: #fff7ed; border-radius: 6px;">
                  <p style="margin: 0; color: #ea580c; font-size: 13px; font-weight: 600;">
                    Not yet - We'll keep watching
                  </p>
                </div>
                {% endif %}

                <p style="margin: 12px 0 0 0; color: #3f3f46; font-size: 13px; line-height: 1.6;">
                  {{payload.answer}}
                </p>

                {% if payload.grounding_sources %}
                <div style="margin: 16px 0 0 0;">
                  <p style="margin: 0 0 8px 0; color: #71717a; font-size: 11px; font-weight: 600; text-transform: uppercase;">
                    Sources
                  </p>
                  {% for source in payload.grounding_sources %}
                  <div style="margin: 0 0 6px 0;">
                    <a href="{{source.uri}}" style="color: #a855f7; text-decoration: underline; font-size: 12px;">
                      {{source.title}}
                    </a>
                  </div>
                  {% endfor %}
                </div>
                {% endif %}
              </div>
              {% endif %}

              <!-- How Notifications Work -->
              <div style="margin: 0 0 24px 0; padding: 20px; background-color: #fef3c7; border-radius: 8px; border: 1px solid #fbbf24;">
                <h3 style="margin: 0 0 12px 0; color: #92400e; font-size: 14px; font-weight: 600;">
                  📬 About Your Notifications
                </h3>

                {% if payload.notify_behavior == 'once' %}
                <p style="margin: 0; color: #78350f; font-size: 13px; line-height: 1.6;">
                  <strong>Notify Once:</strong> We'll send you an email the first time we detect your condition is met, then automatically stop monitoring. Perfect for one-time announcements like release dates.
                </p>
                {% elsif payload.notify_behavior == 'always' %}
                <p style="margin: 0; color: #78350f; font-size: 13px; line-height: 1.6;">
                  <strong>Always Notify:</strong> We'll send you an email every time we check and find your condition is met. Great for recurring opportunities like stock availability or price drops.
                </p>
                {% else %}
                <p style="margin: 0; color: #78350f; font-size: 13px; line-height: 1.6;">
                  <strong>Track Changes:</strong> We'll notify you only when the information changes from our last check. Ideal for monitoring updates and changes over time.
                </p>
                {% endif %}
              </div>

              <!-- CTA -->
              <div style="margin: 24px 0 0 0; text-align: center;">
                <a href="https://torale.ai/tasks/{{payload.task_id}}" style="display: inline-block; padding: 12px 32px; background-color: #a855f7; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 14px;">
                  View Task Dashboard
                </a>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 24px; background-color: #f9fafb; border-radius: 0 0 8px 8px; border-top: 1px solid #e5e7eb;">
              <p style="margin: 0; color: #71717a; font-size: 12px; text-align: center;">
                You can pause, edit, or delete this task anytime from your dashboard
              </p>
            </td>
          </tr>
        </table>

        <!-- Unsubscribe -->
        <p style="margin: 16px 0 0 0; color: #a1a1aa; font-size: 11px; text-align: center;">
          <a href="https://torale.ai/settings/notifications" style="color: #a855f7; text-decoration: none;">Manage notification preferences</a>
        </p>
      </td>
    </tr>
  </table>
</body>
</html>
```

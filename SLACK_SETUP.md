# Slack OAuth Integration Setup Guide

> **Note:** This is a temporary guide for testing the Slack OAuth integration. This file will NOT be committed to the repository.

---

## Prerequisites

- A Slack workspace where you have admin access
- Backend running locally or deployed
- `OAUTH_ENCRYPTION_KEY` configured in your environment

---

## Step 1: Create Slack App

### 1.1 Go to Slack API Dashboard

Visit: https://api.slack.com/apps

Click **"Create New App"** → **"From scratch"**

### 1.2 Basic Information

- **App Name**: `Torale Notifications` (or your preferred name)
- **Development Slack Workspace**: Select your workspace
- Click **"Create App"**

---

## Step 2: Configure OAuth & Permissions

### 2.1 Add Redirect URLs

In the left sidebar, go to **"OAuth & Permissions"**

Scroll to **"Redirect URLs"** section and click **"Add New Redirect URL"**

Add these URLs based on your environment:

**Local Development:**
```
http://localhost:8000/api/v1/integrations/slack/callback
```

**Staging:**
```
https://staging-api.torale.ai/api/v1/integrations/slack/callback
```

**Production:**
```
https://api.torale.ai/api/v1/integrations/slack/callback
```

Click **"Save URLs"**

### 2.2 Add Bot Token Scopes

Scroll down to **"Scopes"** section → **"Bot Token Scopes"**

Click **"Add an OAuth Scope"** and add:

1. **`chat:write`** - Post messages to channels as the bot
2. **`channels:read`** - View basic information about public channels

These are the minimum required scopes for the integration to work.

---

## Step 3: Get App Credentials

### 3.1 Navigate to Basic Information

In the left sidebar, click **"Basic Information"**

### 3.2 Copy Credentials

Under **"App Credentials"** section:

1. **Client ID**: Copy the value (looks like `1234567890.1234567890`)
2. **Client Secret**: Click **"Show"** then copy the value (looks like `abcdef1234567890abcdef1234567890`)

⚠️ **Keep your Client Secret secure!** Never commit it to version control.

---

## Step 4: Configure Environment Variables

### 4.1 Generate Encryption Key

Run this command to generate a secure encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output (should look like: `ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=`)

### 4.2 Update Your `.env` File

Add these variables to your `.env` file:

```bash
# Slack OAuth Integration
SLACK_CLIENT_ID=1234567890.1234567890
SLACK_CLIENT_SECRET=abcdef1234567890abcdef1234567890
SLACK_REDIRECT_URI=http://localhost:8000/api/v1/integrations/slack/callback

# OAuth Token Encryption Key [REQUIRED]
OAUTH_ENCRYPTION_KEY=ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=
```

**Replace with your actual values:**
- Use the Client ID and Secret from Step 3.2
- Use the encryption key you generated in Step 4.1
- Update the redirect URI based on your environment

---

## Step 5: Run Database Migrations

The Slack integration requires the `oauth_integrations` table.

```bash
cd backend
alembic upgrade head
```

You should see output indicating the migration ran successfully:
```
INFO  [alembic.runtime.migration] Running upgrade bcb594440c88 -> 44bd571210b1, create oauth_integrations table
```

---

## Step 6: Start Your Backend

### Local Development

```bash
just dev-noauth
```

Wait for the server to start. You should see in the logs:
```
INFO:torale.api.main:Webhook retry job registered
```

### Verify the Server is Running

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

---

## Step 7: Test the OAuth Flow

### 7.1 Initiate OAuth Authorization

```bash
curl http://localhost:8000/api/v1/integrations/slack/authorize \
  -H "Authorization: Bearer fake-token-for-local"
```

**Expected response:**
```json
{
  "authorization_url": "https://slack.com/oauth/v2/authorize?client_id=...",
  "state": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 7.2 Complete Authorization in Browser

1. Copy the `authorization_url` from the response
2. Open it in your browser
3. You'll see the Slack OAuth consent screen
4. Click **"Allow"** to authorize the app
5. Slack will redirect you back to your callback URL

**Successful redirect looks like:**
```
http://localhost:8000/api/v1/integrations/slack/callback?code=1234567890.1234567890&state=eyJhbGc...
```

**Expected response:**
```json
{
  "success": true,
  "workspace_name": "Your Workspace Name"
}
```

If you see an error, check:
- Your redirect URL matches exactly what's configured in Slack app settings
- Your `OAUTH_ENCRYPTION_KEY` is set correctly
- The JWT state token hasn't expired (valid for 5 minutes)

---

## Step 8: List Available Channels

After successful authorization, you can list channels:

```bash
curl http://localhost:8000/api/v1/integrations/slack/channels \
  -H "Authorization: Bearer fake-token-for-local"
```

**Expected response:**
```json
{
  "channels": [
    {"id": "C1234567890", "name": "#general"},
    {"id": "C0987654321", "name": "#random"},
    {"id": "C1122334455", "name": "#torale-notifications"}
  ]
}
```

---

## Step 9: Select Notification Channel

Choose a channel where you want to receive notifications:

```bash
curl -X POST http://localhost:8000/api/v1/integrations/slack/select-channel \
  -H "Authorization: Bearer fake-token-for-local" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "C1234567890",
    "channel_name": "#torale-notifications"
  }'
```

**Replace** `C1234567890` with an actual channel ID from Step 8.

**Expected response:**
```json
{
  "success": true
}
```

---

## Step 10: Verify Integration Status

Check that the integration is configured correctly:

```bash
curl http://localhost:8000/api/v1/integrations/slack \
  -H "Authorization: Bearer fake-token-for-local"
```

**Expected response:**
```json
{
  "connected": true,
  "workspace_name": "Your Workspace Name",
  "channel_name": "#torale-notifications",
  "connected_at": "2024-02-13T10:30:00Z",
  "last_used_at": null
}
```

---

## Step 11: Test Notification Delivery

### 11.1 Create a Test Task

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer fake-token-for-local" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Slack Notification",
    "search_query": "What is the weather today?",
    "condition_description": "Weather information is available",
    "run_immediately": true
  }'
```

### 11.2 Check Your Slack Channel

Within a few seconds, you should see a message in your selected Slack channel:

```
🔔 Test Slack Notification

Weather information is available with current conditions.

Sources:
• weather.com - Current Weather Conditions
• Weather Underground - Local Forecast
```

The message will be formatted with Slack Block Kit for rich formatting.

---

## Troubleshooting

### Error: "OAUTH_ENCRYPTION_KEY environment variable is required"

**Cause:** The encryption key is not set or is `None`

**Fix:**
1. Generate a new key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
2. Add it to your `.env` file as `OAUTH_ENCRYPTION_KEY=<key>`
3. Restart your backend

### Error: "Slack integration not found"

**Cause:** You haven't completed the OAuth flow yet

**Fix:** Complete Step 7 to authorize the app

### Error: "OAuth state expired (>5min)"

**Cause:** You took more than 5 minutes between authorization and callback

**Fix:** Restart the OAuth flow from Step 7.1

### Error: "State token user mismatch (CSRF protection)"

**Cause:** The user who started OAuth is different from the user in the callback

**Fix:** Make sure you're using the same auth token throughout the flow

### Slack Webhook Not Firing

**Possible causes:**
1. Integration not configured - check Step 10
2. No channel selected - check Step 9
3. Task doesn't meet condition - check task execution logs
4. Notification priority - Slack takes priority, check if it succeeded

**Debug:**
```bash
# Check logs for Slack notification attempts
docker logs torale-backend-1 | grep -i slack

# Check integration status
curl http://localhost:8000/api/v1/integrations/slack \
  -H "Authorization: Bearer fake-token-for-local"
```

### Can't See All Channels

**Cause:** Slack API paginates channel lists at 1000 channels

**Status:** This is a known limitation (noted in code-reviewer feedback)

**Workaround:** Select from the first 1000 channels, or manually note the channel ID

---

## Revoking the Integration

To disconnect the Slack integration:

```bash
curl -X DELETE http://localhost:8000/api/v1/integrations/slack \
  -H "Authorization: Bearer fake-token-for-local"
```

**Expected response:**
```json
{
  "success": true
}
```

This will:
- Delete the encrypted token from the database
- Remove the channel selection
- Slack notifications will no longer be sent

To reconnect, restart from Step 7.

---

## Security Notes

### Token Storage

- OAuth tokens are **encrypted at rest** using Fernet (AES-128)
- Encryption key is stored in environment variable (never in database)
- Tokens are decrypted only when needed for API calls

### CSRF Protection

- OAuth state parameter is a **signed JWT** containing:
  - `user_id` - Prevents token fixation attacks
  - `exp` - 5-minute expiration prevents replay attacks
- JWT is signed with `oauth_encryption_key`
- Callback validates signature, user_id match, and expiration

### Scopes

The app requests minimal scopes:
- `chat:write` - Only allows posting messages (cannot read messages)
- `channels:read` - Only allows listing channel names (cannot read channel content)

### Token Refresh

- Slack workspace tokens don't typically expire
- If revoked by user, the integration will fail gracefully
- Users can disconnect and reconnect to get a fresh token

---

## Production Deployment

### 1. Update Redirect URLs

Add your production redirect URL to the Slack app (Step 2.1):
```
https://api.torale.ai/api/v1/integrations/slack/callback
```

### 2. Update Environment Variables

Update your production `.env` or deployment config:

```bash
SLACK_CLIENT_ID=<same-as-dev>
SLACK_CLIENT_SECRET=<same-as-dev>
SLACK_REDIRECT_URI=https://api.torale.ai/api/v1/integrations/slack/callback
OAUTH_ENCRYPTION_KEY=<same-as-dev-or-new-secure-key>
```

⚠️ **Important:**
- Never commit secrets to version control
- Use environment variable management (e.g., GitHub Secrets, HashiCorp Vault)
- Rotate the encryption key if it's ever exposed

### 3. Run Migrations

```bash
kubectl exec -it deployment/torale-backend -- alembic upgrade head
```

Or via your deployment pipeline.

### 4. Verify Deployment

```bash
curl https://api.torale.ai/api/v1/integrations/slack/authorize \
  -H "Authorization: Bearer $PROD_TOKEN"
```

---

## Optional: App Distribution

### Submit to Slack App Directory (Optional)

If you want to make the app publicly available:

1. Complete **"Display Information"** in Slack app settings:
   - Upload app icon (512x512px)
   - Add short description
   - Add background color

2. Go to **"Manage Distribution"**

3. Click **"Distribute App"**

4. Follow Slack's review process

**Note:** This is only needed for public distribution. For private workspace use, the current setup is sufficient.

---

## Reference

### API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/integrations/slack/authorize` | GET | Initiate OAuth flow |
| `/api/v1/integrations/slack/callback` | GET | OAuth callback handler |
| `/api/v1/integrations/slack/channels` | GET | List available channels |
| `/api/v1/integrations/slack/select-channel` | POST | Select notification channel |
| `/api/v1/integrations/slack` | GET | Get integration status |
| `/api/v1/integrations/slack` | DELETE | Revoke integration |

### Database Tables

**`oauth_integrations` table:**
```sql
CREATE TABLE oauth_integrations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    provider TEXT CHECK (provider IN ('slack', 'discord')),
    access_token TEXT,        -- Encrypted
    refresh_token TEXT,
    expires_at TIMESTAMP,
    workspace_id TEXT,
    workspace_name TEXT,
    channel_id TEXT,
    channel_name TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_used_at TIMESTAMP,
    UNIQUE(user_id, provider)
);
```

---

## Next Steps

Once you've tested the integration:

1. ✅ Delete this file (it's temporary)
2. ✅ Create user-facing documentation if needed
3. ✅ Add Slack setup to onboarding flow (optional)
4. ✅ Monitor OAuth token usage and errors

---

**Questions or issues?** Check the troubleshooting section above or review the code in:
- `backend/src/torale/integrations/slack.py` - OAuth service
- `backend/src/torale/api/routers/integrations.py` - API endpoints
- `backend/src/torale/scheduler/activities.py` - Notification delivery

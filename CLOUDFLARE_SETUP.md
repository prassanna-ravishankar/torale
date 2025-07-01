# Cloudflare DNS Setup for torale.ai

This guide explains how to configure your Cloudflare DNS settings to work with Google Cloud Run.

## Prerequisites
- Domain registered on Cloudflare (torale.ai)
- Terraform deployment completed
- Cloud Run services deployed

## Step 1: Update Terraform Configuration

1. Edit your `terraform/terraform.tfvars` file:
   ```hcl
   # For apex domain (torale.ai)
   frontend_domain = "torale.ai"
   
   # OR for subdomain (app.torale.ai)
   # frontend_domain = "app.torale.ai"
   ```

2. Apply the Terraform changes:
   ```bash
   cd terraform
   terraform apply
   ```

## Step 2: Configure Cloudflare DNS

1. Log in to your Cloudflare dashboard
2. Select your domain (torale.ai)
3. Go to DNS settings

### For Apex Domain (torale.ai):

Add this DNS record:
- **Type**: CNAME
- **Name**: @ (or torale.ai)
- **Target**: ghs.googlehosted.com
- **TTL**: Auto
- **Proxy status**: DNS only (IMPORTANT: Click the orange cloud to turn it gray)

### For Subdomain (app.torale.ai):

Add this DNS record:
- **Type**: CNAME
- **Name**: app
- **Target**: ghs.googlehosted.com
- **TTL**: Auto
- **Proxy status**: DNS only (IMPORTANT: Click the orange cloud to turn it gray)

## Step 3: Important Cloudflare Settings

### SSL/TLS Settings
1. Go to SSL/TLS → Overview
2. Set encryption mode to "Full" or "Full (strict)"

### Page Rules (Optional)
If you want to redirect www to apex:
1. Go to Rules → Page Rules
2. Create rule: `www.torale.ai/*`
3. Setting: Forwarding URL (301)
4. Destination: `https://torale.ai/$1`

## Step 4: Verify Domain Mapping

1. Check domain mapping status:
   ```bash
   gcloud run domain-mappings list --region=us-central1
   ```

2. The status should show as "OK" once verified (can take up to 24 hours)

## Troubleshooting

### Domain not working after 24 hours:
1. Ensure Cloudflare proxy is DISABLED (gray cloud)
2. Check DNS propagation: `dig torale.ai`
3. Verify CNAME points to `ghs.googlehosted.com`

### SSL Certificate Issues:
- Cloud Run automatically provisions SSL certificates
- Certificates are issued by Google-managed CA
- If issues persist, check Cloudflare SSL settings

### "DNS_PROBE_FINISHED_NXDOMAIN" Error:
- DNS records haven't propagated yet (wait 5-10 minutes)
- Double-check the CNAME record in Cloudflare

## Alternative: Using Cloudflare with Proxy Enabled

If you want to use Cloudflare's CDN and security features:
1. Keep the orange cloud (proxy enabled)
2. Use Cloud Run's default URL as the origin
3. Set up a Cloudflare Worker or Page Rule to proxy to Cloud Run

Note: This is more complex and may require additional configuration.

## Next Steps

Once DNS is configured and domain is verified:
1. Access your app at https://torale.ai
2. Monitor Cloud Run logs for any issues
3. Set up monitoring and alerts in GCP
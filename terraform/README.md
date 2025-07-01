# Torale GCP Infrastructure

This Terraform configuration deploys the Torale application to Google Cloud Platform using Cloud Run with internal networking for microservices.

## Architecture

- **Frontend (Public)**: Next.js app accessible from the internet
- **Main Backend (Internal)**: FastAPI gateway that orchestrates microservices
- **Microservices (Internal)**:
  - Discovery Service: Natural language to URL discovery
  - Content Monitoring Service: Web scraping and change detection
  - Notification Service: Multi-channel notifications

## Prerequisites

1. Google Cloud Project with billing enabled
2. Terraform installed (>= 1.0)
3. `gcloud` CLI configured with appropriate permissions
4. GitHub repository connected to Cloud Build (for CI/CD)

## ⚠️ Important: Bootstrap Process Required

**DO NOT run `terraform apply` directly!** This deployment has a chicken-and-egg problem where Cloud Run services reference Docker images that don't exist yet.

## Setup Instructions

1. **Create your variables file**:
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your actual values
   ```

2. **Run the bootstrap script**:
   ```bash
   ./bootstrap.sh
   ```

   This script will:
   - Deploy basic infrastructure (APIs, Artifact Registry, networking)
   - Build and push Docker images locally
   - Deploy Cloud Run services
   
   Note: Cloud Build trigger creation is skipped initially (requires manual GitHub App setup).

### Manual Alternative

If you prefer manual control:

1. **Deploy infrastructure only**:
   ```bash
   terraform init
   terraform apply -target=google_project_service.required_apis -target=google_artifact_registry_repository.docker_repo
   ```

2. **Build and push images manually**:
   ```bash
   # Configure Docker for Artifact Registry
   gcloud auth configure-docker us-central1-docker.pkg.dev
   
   # Build and push each service...
   ```

3. **Deploy Cloud Run services**:
   ```bash
   terraform apply
   ```

## What Gets Created

- **Networking**:
  - VPC with subnet for internal communication
  - Serverless VPC Access Connector

- **Container Registry**:
  - Artifact Registry repository for Docker images

- **Cloud Run Services**:
  - Frontend (public access)
  - Main Backend (internal only)
  - Discovery Service (internal only)
  - Content Monitoring Service (internal only)
  - Notification Service (internal only)

- **IAM**:
  - Service accounts for each service
  - Appropriate permissions for service-to-service communication

- **CI/CD**:
  - Cloud Build trigger for automatic deployments

## Service URLs

After deployment, Terraform will output:
- `frontend_url`: Public URL for your application
- Internal service URLs (only accessible within VPC)

## Security

- All backend services use internal-only ingress
- Frontend communicates with backend through VPC connector
- Service-to-service authentication via IAM
- Sensitive environment variables stored as Terraform variables

## Cost Optimization

- Services scale to zero when not in use (no traffic = no cost)
- VPC connector has minimal fixed cost (~$0.05/hour)
- Artifact Registry has generous free tier

## Setting Up CI/CD (After Initial Deployment)

The bootstrap process skips Cloud Build trigger creation because it requires a manual GitHub App connection. To set up automated deployments:

1. **Connect GitHub Repository**:
   - Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers) in GCP Console
   - Click "Create Trigger" → "Connect Repository"
   - Choose "GitHub (Cloud Build GitHub App)" and follow the OAuth flow
   - Select your repository (`your-username/torale`)

2. **Enable the Trigger in Terraform**:
   ```bash
   # Edit terraform.tfvars
   create_github_trigger = true
   
   # Apply the change
   terraform apply
   ```

3. **Verify Setup**:
   - Make a commit to the `main` branch
   - Check Cloud Build history for automatic builds

## Next Steps

1. Set up CI/CD using the instructions above
2. Configure custom domain (optional)
3. Set up monitoring and alerting
4. Test your application
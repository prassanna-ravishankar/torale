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

## Setup Instructions

1. **Initialize Terraform**:
   ```bash
   cd terraform
   terraform init
   ```

2. **Create your variables file**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your actual values
   ```

3. **Plan the deployment**:
   ```bash
   terraform plan
   ```

4. **Apply the configuration**:
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

## Next Steps

1. Build and push Docker images to Artifact Registry
2. Set up Cloud Build for continuous deployment
3. Configure custom domain (optional)
4. Set up monitoring and alerting
# Torale Infrastructure Documentation

## 🏗️ **Architecture Overview**

This infrastructure uses a **modular Terraform approach** with clear separation of concerns:

```
infrastructure/
├── terraform/
│   ├── modules/                 # Reusable infrastructure components
│   │   ├── gcp-artifact-registry/  # Container registry management
│   │   ├── gcp-iam/                # Service accounts & permissions
│   │   ├── gcp-cloud-run/          # Cloud Run services
│   │   ├── gcp-cloud-build/        # CI/CD pipeline
│   │   └── cloudflare/             # DNS & CDN management
│   ├── environments/            # Environment-specific configurations
│   │   ├── dev/                    # Development environment
│   │   ├── staging/                # Staging environment (TODO)
│   │   └── prod/                   # Production environment (TODO)
│   └── shared/                  # Shared configurations & credentials
├── scripts/                     # Deployment & utility scripts
│   ├── deploy/                     # Deployment scripts
│   ├── setup/                      # Setup scripts
│   └── utils/                      # Utility scripts
└── docs/                       # Infrastructure documentation
```

## 🔧 **Modules**

### **GCP Artifact Registry Module**
- **Purpose**: Manages Docker image repository
- **Features**:
  - Automatic image cleanup (keeps 10 recent versions)
  - IAM permissions for Cloud Build and service accounts
  - Secure access controls

### **GCP IAM Module**
- **Purpose**: Manages service accounts and permissions
- **Features**:
  - Creates service accounts for each service
  - Cloud Build permissions
  - Extensible project-level IAM bindings

### **GCP Cloud Run Module**
- **Purpose**: Manages containerized microservices
- **Features**:
  - Frontend and backend services with public access
  - Microservices with IAM-based authentication
  - Configurable scaling and resource limits
  - Cross-service communication setup

### **GCP Cloud Build Module**
- **Purpose**: CI/CD pipeline management
- **Features**:
  - GitHub integration with branch triggers
  - Automated builds and deployments
  - Configurable substitutions
  - Docker image building and pushing

### **Cloudflare Module**
- **Purpose**: DNS and CDN management
- **Features**:
  - Automatic DNS record creation
  - CDN caching rules
  - Bot protection
  - SSL/TLS optimization

## 🌍 **Environments**

### **Development Environment**
- **Location**: `infrastructure/terraform/environments/dev/`
- **Purpose**: Development and testing
- **Features**:
  - Cost-optimized (scales to zero)
  - Full observability
  - Easy teardown/rebuild

### **Staging & Production** (Planned)
- **Staging**: Pre-production testing with production-like setup
- **Production**: High-availability, security-hardened configuration

## 📁 **Migration Status**

### ✅ **Migration Complete!**
- [x] **Modular structure created**
- [x] **GCP Artifact Registry module**
- [x] **GCP IAM module**  
- [x] **GCP Cloud Run module** 
- [x] **GCP Cloud Build module**
- [x] **Cloudflare module**
- [x] **Development environment fully functional**
- [x] **Scripts updated for new structure**
- [x] **Documentation framework**
- [x] **Legacy files cleaned up**

### 📋 **Next Steps**
- [ ] Staging environment setup
- [ ] Production environment setup
- [ ] Environment promotion scripts
- [ ] Monitoring and alerting modules
- [ ] Security scanning integration
- [ ] Cloudflare integration testing

## 🚀 **Quick Start**

### **1. Development Environment Setup**
```bash
cd infrastructure/terraform/environments/dev
terraform init
terraform plan
terraform apply
```

### **2. Deploy with Scripts**
```bash
# From project root
infrastructure/scripts/setup/bootstrap.sh
infrastructure/scripts/deploy/quick-deploy.sh
```

### **3. Environment Variables**
Copy and configure your environment variables:
```bash
cp infrastructure/terraform/environments/dev/terraform.tfvars.example infrastructure/terraform/environments/dev/terraform.tfvars
# Edit with your values
```

## 🔐 **Security Best Practices**

1. **Separate credentials per environment**
2. **IAM-based service authentication** (no VPC costs!)
3. **Least-privilege access** for service accounts
4. **Encrypted secrets** in Terraform state
5. **Cloudflare proxy** for DDoS protection

## 💰 **Cost Optimization**

- **VPC-free architecture**: ~$518/month savings
- **Scale-to-zero**: Only pay for active usage
- **Shared Artifact Registry**: Efficient image storage
- **Environment isolation**: Prevent resource conflicts

## 🛠️ **Development Workflow**

1. **Make changes** in appropriate module
2. **Test in dev environment** first
3. **Promote to staging** when stable
4. **Deploy to production** after validation

## 📚 **Additional Resources**

- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloudflare Terraform Provider](https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs) 
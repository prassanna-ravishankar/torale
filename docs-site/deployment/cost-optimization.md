# Cost Optimization

## Spot VMs

All services use Spot VMs:
- 60-91% cost savings
- Automatic migration on preemption
- Suitable for stateless workloads

## Resource Right-Sizing

Minimal resource requests:
- API: 100m CPU, 256Mi RAM
- Workers: 100m CPU, 256Mi RAM
- Frontend/Docs: 50m CPU, 64Mi RAM

## Regional Strategy

Single region deployment:
- us-central1 for everything
- Zonal Cloud SQL
- No cross-region traffic

**Result:** ~$50-100/month for production

## Next Steps

- View [Kubernetes Deployment](/deployment/kubernetes)
- Read [Production Best Practices](/deployment/production)

# Discovery Service Deployment Guide

## Overview

The Discovery Service is a standalone FastAPI microservice that converts natural language queries into monitorable URLs using AI providers (Perplexity or OpenAI).

## Local Development

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Perplexity API key

### Setup
```bash
cd discovery-service
cp .env.example .env
# Edit .env with your API keys
uv sync
uv run uvicorn main:app --reload --port 8001
```

### Testing
```bash
# Health check
curl http://localhost:8001/health

# Discovery test
curl -X POST http://localhost:8001/api/v1/discover \
  -H "Content-Type: application/json" \
  -d '{"raw_query": "latest updates from OpenAI"}'
```

## Docker Deployment

### Build Image
```bash
cd discovery-service
docker build -t torale-discovery:latest .
```

### Run Container
```bash
docker run -d \
  --name torale-discovery \
  -p 8001:8001 \
  -e PERPLEXITY_API_KEY=your_key_here \
  -e AI_PROVIDER=perplexity \
  -e LOG_LEVEL=INFO \
  torale-discovery:latest
```

### Docker Compose
```yaml
# In root docker-compose.yml
services:
  discovery-service:
    build: ./discovery-service
    ports:
      - "8001:8001"
    environment:
      - PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
      - AI_PROVIDER=perplexity
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Cloud Deployment

### Railway (Recommended for simplicity)
1. Connect GitHub repository
2. Select `discovery-service` folder
3. Set environment variables:
   - `PERPLEXITY_API_KEY`
   - `AI_PROVIDER=perplexity`
   - `SERVICE_PORT=8001`
4. Railway auto-detects Python and uses `uv`

### Google Cloud Run
```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/torale-discovery

# Deploy
gcloud run deploy torale-discovery \
  --image gcr.io/PROJECT_ID/torale-discovery \
  --platform managed \
  --region us-central1 \
  --port 8001 \
  --set-env-vars PERPLEXITY_API_KEY=your_key,AI_PROVIDER=perplexity
```

### AWS ECS/Fargate
1. Push image to ECR
2. Create ECS task definition with environment variables
3. Create ECS service with desired count
4. Configure ALB for load balancing

### Vercel (Alternative)
```json
// vercel.json
{
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}
```

## Environment Variables

### Required
- `PERPLEXITY_API_KEY`: Your Perplexity API key
- `AI_PROVIDER`: Set to "perplexity" or "openai"

### Optional
- `SERVICE_PORT`: Port to run on (default: 8001)
- `LOG_LEVEL`: Logging level (default: INFO)
- `CORS_ORIGINS`: Comma-separated allowed origins
- `AI_MODEL`: Override default model for provider

### Production Example
```bash
PERPLEXITY_API_KEY=pplx-your-api-key
AI_PROVIDER=perplexity
SERVICE_PORT=8001
LOG_LEVEL=INFO
CORS_ORIGINS=https://app.torale.com,https://api.torale.com
```

## Monitoring

### Health Checks
- **Endpoint**: `GET /health`
- **Response**: `{"status": "healthy", "service": "discovery-service"}`
- **Use**: Load balancer health checks, uptime monitoring

### Logging
- Structured JSON logs via `structlog`
- Key events: service startup, requests, errors, AI provider calls
- Log levels: DEBUG, INFO, WARNING, ERROR

### Metrics (Future)
- Request count and latency
- AI provider response times
- Error rates by endpoint
- Cache hit/miss rates

## Performance

### Scaling Considerations
- **Stateless**: Safe to run multiple instances
- **Horizontal scaling**: Use load balancer with multiple instances
- **Resource usage**: ~50MB RAM, minimal CPU when idle
- **Latency**: 2-5 seconds (dominated by AI provider API calls)

### Production Recommendations
- Run 2+ instances for availability
- Set up health check monitoring
- Configure request timeouts (30s recommended)
- Monitor AI provider rate limits

## Security

### API Security
- CORS configured for known origins only
- No sensitive data in logs
- Input validation on all endpoints

### Secrets Management
- Never commit API keys to repository
- Use environment variables or secret management services
- Rotate API keys regularly

## Troubleshooting

### Common Issues

**Service won't start**
- Check Python version (3.12+ required)
- Verify `uv` is installed
- Check environment variables are set

**AI provider errors**
- Verify API key is correct and active
- Check model name is supported
- Monitor rate limits

**Connection issues**
- Verify port 8001 is accessible
- Check firewall/security group settings
- Confirm CORS origins are configured

### Debug Mode
```bash
# Local debugging
LOG_LEVEL=DEBUG uv run uvicorn main:app --reload --port 8001

# View detailed logs
tail -f logs/discovery-service.log
```

## Integration

### Backend Integration
The main Torale backend automatically discovers and uses this service:

```python
# Backend configuration
DISCOVERY_SERVICE_URL=http://discovery-service:8001  # Docker
# or
DISCOVERY_SERVICE_URL=http://localhost:8001  # Local development
```

### Frontend Integration
Frontend calls discovery service through the main backend API, no direct integration needed.

## Backup and Recovery

### Stateless Design
- No data to backup (service is stateless)
- Configuration in environment variables
- Quick recovery by redeploying container

### Disaster Recovery
1. Deploy new instance with same environment variables
2. Update load balancer/DNS to point to new instance
3. Service is immediately available
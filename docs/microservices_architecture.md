# Torale Microservices Architecture with Supabase

## Overview

This document outlines the microservices architecture for Torale, integrating Supabase as the unified authentication and database solution. The architecture breaks down the monolithic backend into logical, scalable services while maintaining data consistency and security.

## Architecture Diagram

```
┌─────────────────┐     ┌─────────────────┐
│   Next.js App   │────▶│  API Gateway    │
│  (Supabase SDK) │     │   (FastAPI)     │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐ ┌───▼────┐ ┌────▼──────┐
              │ Discovery │ │Content │ │Notification│
              │ Service   │ │Processor│ │ Service   │
              └─────┬─────┘ └───┬────┘ └────┬──────┘
                    │           │           │
                    └───────────┼───────────┘
                                │
                         ┌──────▼──────┐
                         │  Supabase   │
                         │  - Auth     │
                         │  - Database │
                         │  - Realtime │
                         │  - Storage  │
                         │  - Functions│
                         └─────────────┘
```

## Service Breakdown

### 1. API Gateway Service (FastAPI)
**Repository**: `backend/` (enhanced)
**Responsibilities**:
- Authentication & authorization via Supabase JWT
- Request routing and orchestration
- User query management
- Monitored source CRUD operations
- Change alert management
- Rate limiting and request validation

**Key Changes**:
- ✅ Supabase JWT verification middleware
- ✅ User-scoped data access with RLS
- ✅ UUID-based models
- ✅ Async database operations

**Database Tables Owned**:
- `user_queries`
- `monitored_sources` 
- `change_alerts`

### 2. Discovery Service (Stateless)
**Repository**: `services/discovery/` (to be extracted)
**Responsibilities**:
- Natural language query refinement
- URL identification from queries
- AI provider abstraction (Perplexity/OpenAI)
- Stateless computation service

**Key Features**:
- No database dependencies
- Horizontal scaling
- AI provider switching
- Cache-friendly responses

**API Interface**:
```
POST /discover-sources/
- Input: raw query + user context
- Output: list of monitorable URLs
```

### 3. Content Processing Service
**Repository**: `services/content-processor/` (to be extracted)
**Responsibilities**:
- Web scraping and content extraction
- Content preprocessing and cleaning
- Embedding generation via OpenAI
- Content deduplication

**Database Tables Owned**:
- `scraped_contents`
- `content_embeddings`

**Key Features**:
- Background job processing
- Vector similarity operations
- Content storage optimization
- Error handling and retries

### 4. Change Detection Service
**Repository**: `services/change-detector/` (to be extracted)
**Responsibilities**:
- Embedding comparison for changes
- Semantic change analysis
- Alert generation logic
- Change severity assessment

**Key Features**:
- pgvector similarity queries
- Configurable thresholds
- AI-powered change summarization
- Event-driven processing

### 5. Notification Service
**Repository**: `services/notifications/` (to be extracted)
**Responsibilities**:
- Email notifications via SendGrid
- Webhook delivery
- Notification preferences
- Delivery status tracking

**Key Features**:
- Multiple delivery channels
- Template management
- Retry logic with exponential backoff
- User preference handling

## Database Architecture

### Supabase PostgreSQL Schema

```sql
-- Core tables with RLS enabled
user_queries (user_id, raw_query, status, config_hints_json)
monitored_sources (user_id, user_query_id, url, status, config)
scraped_contents (monitored_source_id, content, embeddings)
content_embeddings (scraped_content_id, vector, model_name)
change_alerts (user_id, monitored_source_id, summary, details)
```

### Row Level Security (RLS)
- All tables enforce user-scoped access
- Service role can bypass RLS for background tasks
- Automatic user context injection via JWT

### Vector Search with pgvector
- Efficient similarity queries for change detection
- Indexed vector operations
- Support for multiple embedding models

## Authentication & Authorization

### Supabase Integration
1. **Frontend**: Supabase SDK handles auth flows
2. **Backend**: JWT verification with Supabase public key
3. **Database**: RLS policies enforce data isolation
4. **Services**: Service role for background operations

### Security Features
- JWT token validation on all endpoints
- User-scoped database access
- Secure API key management
- CORS configuration

## Migration Path

### Phase 1: Supabase Integration ✅
- [x] Database schema migration
- [x] Authentication system
- [x] Updated models and endpoints
- [x] RLS policies implementation

### Phase 2: Service Extraction (Next)
1. **Extract Discovery Service**
   - Containerize source discovery logic
   - Create REST API interface
   - Add service-to-service auth

2. **Extract Notification Service**
   - Implement message queue (Redis/SQS)
   - Create notification worker
   - Add delivery tracking

### Phase 3: Background Processing
1. **Replace FastAPI BackgroundTasks**
   - Implement Celery + Redis
   - Create periodic task scheduler
   - Add job monitoring

2. **Extract Content Services**
   - Separate scraping and embedding services
   - Implement event-driven architecture
   - Add horizontal scaling

### Phase 4: Advanced Features
1. **Real-time Updates**
   - Supabase Realtime for live alerts
   - WebSocket connections
   - Push notifications

2. **Analytics & Monitoring**
   - Service mesh (Istio/Linkerd)
   - Distributed tracing
   - Performance monitoring

## Development Workflow

### Local Development
```bash
# Start Supabase (local)
supabase start

# Start API Gateway
cd backend && uv run uvicorn app.main:app --reload

# Start individual services (future)
docker-compose up discovery-service
docker-compose up content-processor
```

### Testing Strategy
- **Unit Tests**: Service-specific logic
- **Integration Tests**: Service-to-service communication
- **E2E Tests**: Full user workflows
- **Load Tests**: Service scalability

### Deployment
- **API Gateway**: Traditional deployment (Railway/Fly.io)
- **Services**: Containerized (Docker + Kubernetes)
- **Database**: Supabase hosted
- **Message Queue**: Redis Cloud/AWS SQS

## Configuration Management

### Environment Variables
```env
# Supabase
SUPABASE_URL=https://project.supabase.co
SUPABASE_SERVICE_KEY=service_key
SUPABASE_JWT_SECRET=jwt_secret

# Service URLs (for microservices)
DISCOVERY_SERVICE_URL=http://discovery:8001
CONTENT_PROCESSOR_URL=http://processor:8002
NOTIFICATION_SERVICE_URL=http://notifications:8003

# AI Providers
OPENAI_API_KEY=sk-...
PERPLEXITY_API_KEY=pplx-...
```

### Service Discovery
- Environment-based configuration initially
- Kubernetes service discovery for production
- Health checks and circuit breakers

## Benefits of This Architecture

### Scalability
- Scale services independently based on load
- Discovery service can handle burst traffic
- Content processing can run on high-memory instances

### Reliability
- Service isolation prevents cascading failures
- Database-level security with RLS
- Graceful degradation capabilities

### Development Velocity
- Teams can work on services independently
- Clear service boundaries and APIs
- Easier testing and deployment

### Cost Optimization
- Pay-as-you-scale for individual services
- Supabase handles database management
- Efficient resource allocation

## Monitoring & Observability

### Metrics
- Service-specific metrics (response time, error rate)
- Database query performance
- AI provider API usage
- User engagement analytics

### Logging
- Structured logging across all services
- Centralized log aggregation
- User-scoped log filtering

### Alerting
- Service health monitoring
- Error rate thresholds
- Performance degradation alerts
- AI provider quota monitoring

## Next Steps

1. **Immediate**: Test current Supabase integration
2. **Week 1**: Extract Discovery Service
3. **Week 2**: Implement proper job queue
4. **Week 3**: Extract Notification Service
5. **Month 1**: Complete microservices extraction
6. **Month 2**: Production deployment and monitoring
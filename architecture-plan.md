# Torale Architecture Plan: Microservices Migration

## Current State

Torale is a natural language-powered alerting service that monitors websites for meaningful changes. The current monolithic architecture consists of:

- **Backend**: FastAPI monolith with all services bundled together
- **Frontend**: Next.js 15 application with Supabase Auth
- **Database**: Supabase (PostgreSQL with pgvector)

## Target Architecture: Synchronous-First Microservices

### Design Principles

1. **Start Simple**: Synchronous HTTP communication initially
2. **Service Boundaries**: Clear domain separation based on existing code structure
3. **Progressive Enhancement**: Add async/event-driven patterns only when needed
4. **Production Ready**: Each milestone delivers deployable value

### Core Microservices

#### 1. Discovery Service
- **Purpose**: Convert natural language queries to monitorable URLs
- **Technology**: Python/FastAPI (existing code)
- **API**: `POST /discover` → Returns list of URLs
- **Scaling**: Stateless, horizontally scalable
- **Dependencies**: Perplexity/OpenAI APIs

#### 2. Content Processing Service
- **Purpose**: Web scraping and embedding generation
- **Technology**: Python (consider Go/Rust for performance)
- **API**: Synchronous endpoints with configurable timeouts
- **Scaling**: CPU/memory intensive, scale based on load
- **Dependencies**: OpenAI embeddings API

#### 3. Change Detection Service
- **Purpose**: Compare embeddings and detect significant changes
- **Technology**: Python with pgvector
- **API**: Similarity computation endpoints
- **Scaling**: Vector operations benefit from vertical scaling
- **Dependencies**: Supabase/pgvector

#### 4. Notification Service
- **Purpose**: Multi-channel alert delivery
- **Technology**: Any language (Node.js/Go recommended)
- **API**: `POST /notify` with channel configuration
- **Scaling**: Queue-based with retry logic
- **Dependencies**: SendGrid, webhooks

#### 5. API Gateway
- **Purpose**: Request routing, auth, aggregation
- **Technology**: Existing FastAPI app evolves into gateway
- **Features**: Rate limiting, caching, request transformation
- **Scaling**: Lightweight, highly scalable

## Implementation Milestones

### Milestone 1: Discovery Service Extraction (1-2 weeks)
**Deliverable**: Standalone discovery microservice

**Implementation**:
```
discovery-service/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── main.py           # FastAPI app
│   ├── api/
│   │   └── discovery.py  # Discovery endpoints
│   ├── services/
│   │   └── discovery.py  # Core logic (from existing)
│   └── clients/
│       └── ai.py         # Perplexity/OpenAI clients
└── tests/
```

**Tasks**:
1. Create new repository/directory structure
2. Extract discovery logic with clean REST API
3. Add health checks and metrics endpoints
4. Deploy as container (Docker/Cloud Run/Railway)
5. Update main app to call discovery service via HTTP
6. Add response caching for performance

**Benefits**:
- Independent scaling for NLP workload
- Can be reused by other projects
- No async complexity
- Simple deployment

### Milestone 2: Notification Service (1 week)
**Deliverable**: Centralized notification microservice

**Implementation**:
```
notification-service/
├── Dockerfile
├── package.json          # If using Node.js
├── src/
│   ├── server.js         # Express/Fastify app
│   ├── channels/
│   │   ├── email.js      # SendGrid integration
│   │   └── webhook.js    # Webhook delivery
│   ├── templates/        # Notification templates
│   └── queue/           # In-memory retry queue
└── tests/
```

**Tasks**:
1. Create notification service with POST endpoint
2. Implement multi-channel support (email, webhooks)
3. Add template management
4. Internal retry queue (in-memory initially)
5. Deploy and update main app to use it

**Benefits**:
- Centralized notification logic
- Easy to add new channels
- Isolated from main application
- Better error handling

### Milestone 3: Content Processing Service (1-2 weeks)
**Deliverable**: Dedicated scraping/processing service

**Implementation**:
```
content-processor/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── scraping.py   # Scraping endpoints
│   │   └── embeddings.py # Embedding endpoints
│   ├── services/
│   │   ├── scraper.py    # Web scraping logic
│   │   └── embedder.py   # Embedding generation
│   └── utils/
│       └── text.py       # Text processing
└── tests/
```

**Tasks**:
1. Extract content ingestion logic
2. Add configurable timeouts for scraping
3. Implement batch processing support
4. Direct database writes for content
5. Deploy with appropriate resource limits

**Benefits**:
- Isolated resource-intensive operations
- Can use different runtime if needed
- Better error handling for scraping
- Independent scaling

### Milestone 4: Smart API Gateway (1 week)
**Deliverable**: Intelligent request routing layer

**Implementation**:
```
# Evolve existing main.py into gateway
backend/
├── app/
│   ├── main.py           # API Gateway
│   ├── gateway/
│   │   ├── router.py     # Service routing logic
│   │   ├── aggregator.py # Response aggregation
│   │   └── cache.py      # Caching layer
│   └── clients/
│       ├── discovery.py  # Discovery service client
│       ├── content.py    # Content service client
│       └── notify.py     # Notification client
```

**Tasks**:
1. Refactor main app as API gateway
2. Implement service routing logic
3. Add response aggregation for complex queries
4. Implement circuit breakers
5. Add caching layer

**Benefits**:
- Single entry point for frontend
- Service orchestration
- Centralized auth/rate limiting
- Better resilience

### Milestone 5: Real-time Features (1 week)
**Deliverable**: Live updates without polling

**Implementation**:
- Use Supabase Realtime for database changes
- Frontend WebSocket subscriptions
- No custom WebSocket server needed
- Fallback to polling if needed

**Benefits**:
- Instant UI updates
- Reduced API load
- Uses existing infrastructure
- Simple implementation

### Milestone 6: Async & Event-Driven Architecture (2 weeks)
**Deliverable**: Full async architecture (when needed)

**Implementation**:
```
# Add message queue infrastructure
infrastructure/
├── docker-compose.yml
├── redis/               # Or RabbitMQ
└── monitoring/
    ├── prometheus/
    └── grafana/
```

**Tasks**:
1. Add message queue (Redis/RabbitMQ)
2. Convert service calls to events
3. Implement saga pattern for workflows
4. Add event replay capability
5. Update services to consume events

**Benefits**:
- True service decoupling
- Better fault tolerance
- Horizontal scaling of workers
- Event sourcing capabilities

## Migration Strategy

### Phase 1: Extraction (Milestones 1-3)
- Extract services one by one
- Maintain synchronous communication
- Minimal changes to main application
- Each service independently deployable

### Phase 2: Enhancement (Milestones 4-5)
- Add gateway capabilities
- Implement real-time features
- Optimize service communication
- Add monitoring/observability

### Phase 3: Evolution (Milestone 6)
- Add async when bottlenecks appear
- Implement event-driven patterns
- Advanced scaling strategies
- Full microservices maturity

## Key Decisions

### Why Synchronous First?
1. **Simpler debugging**: Stack traces cross service boundaries
2. **Faster development**: No message queue complexity
3. **Easier deployment**: Less infrastructure to manage
4. **Progressive enhancement**: Add async only where needed

### Service Boundaries
Based on existing code structure:
- Discovery: Pure computation, no state
- Notifications: External dependencies
- Content Processing: Resource intensive
- Change Detection: Database intensive

### Technology Choices
- **Keep Python**: For most services (existing expertise)
- **Consider Go/Rust**: For content processing (performance)
- **Node.js**: For notification service (npm ecosystem)
- **Existing tools**: Supabase, Docker, FastAPI

## Success Metrics

1. **Independent deployments**: Deploy services without affecting others
2. **Improved performance**: Measure latency improvements
3. **Better scalability**: Scale services based on actual load
4. **Increased reliability**: Measure uptime per service
5. **Developer velocity**: Faster feature development

## Risks & Mitigations

### Risk: Increased complexity
**Mitigation**: Start simple, add complexity only when needed

### Risk: Network latency
**Mitigation**: Synchronous first, optimize hot paths

### Risk: Distributed debugging
**Mitigation**: Comprehensive logging, distributed tracing later

### Risk: Data consistency
**Mitigation**: Keep database centralized initially

## Next Steps

1. **Create service repositories/directories**
2. **Extract Discovery Service first** (lowest risk, highest value)
3. **Set up CI/CD for microservices**
4. **Document service APIs**
5. **Plan monitoring strategy**

This plan provides a pragmatic path from monolith to microservices, delivering value at each milestone while avoiding premature complexity.
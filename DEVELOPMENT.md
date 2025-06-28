# Torale Development Guide

This guide covers development workflows, code standards, testing practices, and contribution guidelines for the Torale project.

## 🏗️ Architecture Overview

Torale uses a **selective microservices architecture** with clear service boundaries:

### Services

- **Frontend** (`:3000`): Next.js 15 app with React 19, TypeScript, Tailwind CSS
- **Main Backend** (`:8000`): FastAPI gateway handling auth, user management, orchestration  
- **Discovery Service** (`:8001`): AI-powered natural language → URL discovery
- **Content Monitoring Service** (`:8002`): Web scraping, embeddings, change detection
- **Notification Service** (`:8003`): Email delivery, template management, multi-channel alerts

### Communication Patterns

- **Frontend ↔ Backend**: REST API with Supabase Auth JWT
- **Backend ↔ Microservices**: HTTP REST with circuit breakers
- **All Services ↔ Database**: Direct Supabase connections with RLS
- **Real-time Updates**: Supabase Realtime for live UI updates

## 🚀 Development Workflow

### Getting Started

1. **Setup environment**:
   ```bash
   # Using just (recommended)
   just setup
   
   # Manual setup
   cd backend && uv sync
   cd ../frontend && npm install
   cd ../discovery-service && uv sync
   cd ../content-monitoring-service && uv sync
   cd ../notification-service && uv sync
   ```

2. **Start development servers**:
   ```bash
   # All services with hot reload
   just dev
   
   # Individual services
   just dev-backend      # :8000
   just dev-frontend     # :3000
   just dev-discovery    # :8001
   just dev-monitoring   # :8002
   just dev-notifications # :8003
   ```

3. **Verify setup**:
   ```bash
   just health  # Check all services
   curl http://localhost:3000  # Frontend
   curl http://localhost:8000/docs  # Backend API docs
   ```

### Development Environment

**Recommended tools:**
- **Editor**: VS Code with Python, TypeScript, and Tailwind extensions
- **Terminal**: iTerm2/Windows Terminal with multiple panes
- **API Testing**: Use built-in FastAPI docs at `/docs` endpoints
- **Database**: Supabase dashboard for SQL queries and data inspection

**Environment files:**
```bash
# Root level
.env                    # All service environment variables

# Service level (for individual development)
backend/.env.example
frontend/.env.local.example
discovery-service/.env.example
content-monitoring-service/.env.example
notification-service/.env.example
```

## 🧪 Testing Strategy

### Test Structure

Each service has its own test suite following these patterns:

**Backend (pytest)**:
```bash
backend/tests/
├── unit/              # Unit tests for services, models
├── integration/       # API endpoint tests  
├── test_*.py         # Individual test files
└── conftest.py       # Shared fixtures
```

**Frontend (vitest)**:
```bash
frontend/src/
├── components/
│   └── Component.test.tsx
├── hooks/
│   └── useHook.test.ts
└── test/
    └── setup.ts
```

**Microservices (pytest)**:
```bash
service-name/tests/
├── test_api/         # API endpoint tests
├── test_services/    # Business logic tests
└── conftest.py       # Service-specific fixtures
```

### Running Tests

```bash
# All tests
just test

# Individual services
just test-backend
just test-frontend
just test-discovery
just test-monitoring
just test-notifications

# With coverage
cd backend && uv run pytest --cov=app --cov-report=term-missing
cd frontend && npm run coverage

# Watch mode for development
cd backend && uv run pytest --watch
cd frontend && npm run test:watch
```

### Test Guidelines

**Unit Tests:**
- Test individual functions and classes in isolation
- Mock external dependencies (APIs, database)
- Focus on business logic and edge cases
- Aim for >90% coverage on critical paths

**Integration Tests:**
- Test API endpoints end-to-end
- Use test database with real Supabase connection
- Test service-to-service communication
- Verify data persistence and retrieval

**Frontend Tests:**
- Test component rendering and interactions
- Mock API calls and external dependencies
- Test custom hooks and utilities
- Focus on user workflows and edge cases

## 📝 Code Standards

### Python (Backend & Microservices)

**Style Guide:**
```python
# Use type hints everywhere
async def process_content(source_id: str, user_id: str) -> ProcessingResult:
    """Process content with proper docstring."""
    
# Prefer async/await for I/O operations
async with aiohttp.ClientSession() as session:
    response = await session.get(url)
    
# Use Pydantic models for validation
class MonitoredSource(BaseModel):
    url: HttpUrl
    name: str = Field(..., min_length=1, max_length=100)
    
# Error handling with custom exceptions
try:
    result = await dangerous_operation()
except APIError as e:
    logger.error(f"API error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Service unavailable")
```

**Code Quality Tools:**
```bash
# Formatting (black-compatible)
uv run ruff format .

# Linting
uv run ruff check .

# Type checking
uv run mypy .

# Import sorting
uv run ruff check --select I
```

**Architecture Patterns:**
- **Repository Pattern**: Database operations isolated in repository classes
- **Service Layer**: Business logic in service classes  
- **Dependency Injection**: Use FastAPI's dependency system
- **Error Handling**: Structured exceptions with proper HTTP status codes

### TypeScript (Frontend)

**Style Guide:**
```typescript
// Use strict TypeScript
interface NotificationAlert {
  id: string
  user_id: string
  change_summary: string
  detected_at: string
}

// Prefer functional components with hooks
const AlertList: React.FC<{ userId: string }> = ({ userId }) => {
  const { data: alerts, isLoading } = useAlerts(userId)
  
  if (isLoading) return <LoadingSpinner />
  
  return (
    <div className="space-y-4">
      {alerts?.map(alert => (
        <AlertCard key={alert.id} alert={alert} />
      ))}
    </div>
  )
}

// Use proper error boundaries
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <Navigation />
      <main>{children}</main>
    </ErrorBoundary>
  )
}
```

**Code Quality:**
```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Formatting (Prettier via ESLint)
npm run lint:fix
```

**Architecture Patterns:**
- **Server Components**: Default for pages, client components only when needed
- **Custom Hooks**: Encapsulate complex state logic
- **TanStack Query**: Server state management with caching
- **Context**: Minimal usage, prefer prop drilling or query state

### Database

**Schema Design:**
- Use descriptive table and column names
- Include proper indexes for query performance
- Implement Row Level Security (RLS) for data isolation
- Use migrations for all schema changes

**Migration Guidelines:**
```sql
-- Always include rollback instructions
-- migration: 20250628001_add_user_preferences.sql

-- Forward migration
ALTER TABLE users ADD COLUMN preferences JSONB DEFAULT '{}';
CREATE INDEX IF NOT EXISTS idx_users_preferences ON users USING GIN (preferences);

-- Rollback (in comments):
-- DROP INDEX IF EXISTS idx_users_preferences;
-- ALTER TABLE users DROP COLUMN IF EXISTS preferences;
```

## 🔄 Git Workflow

### Branch Strategy

```bash
# Branch naming
feature/user-authentication
bugfix/notification-delivery
hotfix/critical-security-issue
chore/update-dependencies

# Development workflow
git checkout main
git pull origin main
git checkout -b feature/awesome-feature

# Make changes, commit frequently
git add .
git commit -m "Add user preference validation"

# Push and create PR
git push origin feature/awesome-feature
# Create PR via GitHub UI
```

### Commit Messages

Follow conventional commits:
```bash
# Format: type(scope): description

feat(auth): add OAuth login support
fix(notifications): resolve email template rendering issue  
docs(api): update endpoint documentation
test(discovery): add integration tests for AI processing
chore(deps): update FastAPI to latest version
```

### Pull Request Process

1. **Create descriptive PR**:
   - Clear title and description
   - Link to relevant issues
   - Include screenshots for UI changes
   - Add testing instructions

2. **Ensure quality**:
   ```bash
   # Before creating PR
   just test     # All tests pass
   just lint     # No linting errors
   just build    # Production build succeeds
   ```

3. **Code review**:
   - At least one approval required
   - Address all review comments
   - Keep PRs focused and reasonably sized

4. **Merge**:
   - Squash and merge for feature branches
   - Use merge commits for release branches

## 🏗️ Adding New Features

### Backend API Endpoints

1. **Define schemas** in `backend/app/schemas/`:
   ```python
   # schemas/new_feature_schemas.py
   class CreateFeatureRequest(BaseModel):
       name: str = Field(..., min_length=1)
       description: str | None = None
       
   class FeatureResponse(BaseModel):
       id: str
       name: str
       created_at: datetime
   ```

2. **Create service** in `backend/app/services/`:
   ```python
   # services/feature_service.py
   class FeatureService:
       def __init__(self, supabase: Client):
           self.supabase = supabase
           
       async def create_feature(self, request: CreateFeatureRequest, user_id: str) -> FeatureResponse:
           # Implementation
   ```

3. **Add endpoint** in `backend/app/api/endpoints/`:
   ```python
   # api/endpoints/features.py
   @router.post("/", response_model=FeatureResponse)
   async def create_feature(
       request: CreateFeatureRequest,
       current_user: User = Depends(get_current_user),
       feature_service: FeatureService = Depends(get_feature_service)
   ):
       return await feature_service.create_feature(request, current_user.id)
   ```

4. **Add tests**:
   ```python
   # tests/test_features.py
   async def test_create_feature(client: TestClient, user_token: str):
       response = client.post(
           "/api/features/",
           json={"name": "Test Feature"},
           headers={"Authorization": f"Bearer {user_token}"}
       )
       assert response.status_code == 201
   ```

### Frontend Components

1. **Create component** in `frontend/src/components/`:
   ```typescript
   // components/FeatureForm.tsx
   interface FeatureFormProps {
     onSubmit: (data: CreateFeatureRequest) => Promise<void>
     isLoading?: boolean
   }
   
   export const FeatureForm: React.FC<FeatureFormProps> = ({ onSubmit, isLoading }) => {
     // Implementation with react-hook-form + zod
   }
   ```

2. **Add API hook**:
   ```typescript
   // hooks/useFeatures.ts
   export const useCreateFeature = () => {
     return useMutation({
       mutationFn: (data: CreateFeatureRequest) => 
         axiosInstance.post('/api/features/', data),
       onSuccess: () => {
         toast.success('Feature created successfully')
       }
     })
   }
   ```

3. **Create page** in `frontend/src/app/`:
   ```typescript
   // app/features/new/page.tsx
   export default function NewFeaturePage() {
     const createFeature = useCreateFeature()
     
     return (
       <div>
         <h1>Create Feature</h1>
         <FeatureForm onSubmit={createFeature.mutateAsync} />
       </div>
     )
   }
   ```

### Database Migrations

1. **Create migration file**:
   ```sql
   -- supabase/migrations/20250628001_add_features_table.sql
   CREATE TABLE features (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       name TEXT NOT NULL,
       description TEXT,
       user_id UUID NOT NULL REFERENCES auth.users(id),
       created_at TIMESTAMPTZ DEFAULT NOW(),
       updated_at TIMESTAMPTZ DEFAULT NOW()
   );
   
   -- RLS policies
   ALTER TABLE features ENABLE ROW LEVEL SECURITY;
   
   CREATE POLICY "Users can manage their own features" ON features
       FOR ALL USING (auth.uid() = user_id);
   ```

2. **Test migration**:
   ```bash
   # Run in Supabase SQL Editor
   # Verify tables created correctly
   # Test RLS policies work as expected
   ```

## 🚀 Deployment

### Development Deployment

```bash
# Local development with hot reload
just dev

# Docker development environment
just up

# Individual service deployment
docker-compose up backend discovery-service
```

### Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with production config
docker-compose -f docker-compose.prod.yml up -d

# Health checks
just health-prod
```

### Environment Management

**Development**:
- Use `.env.local` for frontend
- Use service-specific `.env` files for individual development
- Use root `.env` for docker-compose development

**Production**:
- Use environment variables injection (not `.env` files)
- Secure secret management (Azure Key Vault, AWS Secrets Manager)
- Separate environments for staging/production

## 📊 Monitoring & Debugging

### Logging

**Backend Services**:
```python
import structlog

logger = structlog.get_logger(__name__)

# Structured logging
logger.info(
    "user_action_completed",
    user_id=user.id,
    action="create_monitor",
    duration_ms=duration,
    success=True
)
```

**Frontend**:
```typescript
// Error reporting
import { captureException } from '@sentry/nextjs'

try {
  await riskyOperation()
} catch (error) {
  console.error('Operation failed:', error)
  captureException(error)
  toast.error('Something went wrong. Please try again.')
}
```

### Performance Monitoring

```bash
# Docker resource usage
docker stats

# Service health checks
just health

# Database performance
# Check slow queries in Supabase dashboard

# Frontend performance
# Use browser dev tools Performance tab
# Monitor Core Web Vitals
```

### Debugging

**Backend**:
```python
# Use debugger
import pdb; pdb.set_trace()

# Rich logging for development
import rich
rich.print(complex_data_structure)

# FastAPI automatic docs
# Visit http://localhost:8000/docs
```

**Frontend**:
```typescript
// React DevTools
// TanStack Query DevTools (enabled in development)

// Browser debugging
console.log('Debug data:', { user, alerts, isLoading })

// Network tab for API calls
```

## 🤝 Contributing Guidelines

### Before Contributing

1. **Read documentation**: Understand the architecture and patterns
2. **Check issues**: Look for existing issues or create one for new features
3. **Discuss approach**: For large changes, discuss in GitHub Discussions

### Code Review Checklist

**For Authors**:
- [ ] Tests added/updated for new functionality
- [ ] Documentation updated (if needed)
- [ ] No breaking changes (or clearly documented)
- [ ] All CI checks passing
- [ ] PR description is clear and complete

**For Reviewers**:
- [ ] Code follows project standards
- [ ] Tests adequately cover new functionality
- [ ] No security vulnerabilities introduced
- [ ] Performance impact considered
- [ ] User experience is improved or maintained

### Getting Help

- **Architecture questions**: Create GitHub Discussion
- **Bug reports**: Create GitHub Issue with reproduction steps
- **Feature requests**: Create GitHub Issue with use case description
- **Code questions**: Comment on relevant PR or Discussion

---

**Happy coding!** 🚀 The Torale team appreciates all contributions to making website monitoring smarter and more accessible.
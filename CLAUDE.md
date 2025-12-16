# CLAUDE.md - Torale Project Context

## Identity

Torale is a **grounded search monitoring platform**. Users create tasks that watch for conditions using Google Search + LLM analysis, then get notified when conditions are met. Think "alert me when the iPhone release date is announced."

**Scale**: Early-stage, small user base. This doc assumes single-developer velocity. Revisit if team or user scale increases significantly.

**Domain**: torale.ai (prod), staging.torale.ai (staging)

## Codebase

**Stack**: Python FastAPI + React/TypeScript + GKE + Temporal Cloud + Clerk Auth + Gemini

**Structure**:
```
torale/
├── backend/                 # Python FastAPI + Temporal workers
│   ├── src/torale/api/      # API endpoints
│   ├── src/torale/workers/  # Temporal workflows
│   ├── src/torale/executors/# Search + LLM logic
│   └── alembic/             # DB migrations
├── frontend/                # React + TypeScript + Vite
│   └── src/components/      # UI components
│       └── torale/          # Design system components
├── helm/                    # Kubernetes Helm charts
├── .github/workflows/       # CI/CD (GitHub Actions)
└── docs-site/               # Documentation (VitePress)
```

**Tooling**: `uv` (backend), `npm` (frontend), `vite` (docs-site), `justfile` for commands:
- `just dev-noauth` - Run local dev without auth
- `just test` - Run tests
- `just test-integration` - Run integration tests
- `just lint` - Run all linting (backend + frontend + TypeScript)

**Architecture**: Frontend → FastAPI → Temporal (scheduling) → Workers → Gemini + Google Search → Notifications

See `docs-site/architecture/` for detailed docs.

## Development Flow

**CI handles everything**: Build, test, deploy. Push to branch triggers checks, merge to main deploys to prod.

**Common workflow**:
1. Create branch
2. Build and iterate locally (`just dev-noauth`)
3. **Always run `just lint` before committing** - catches errors CI will catch
4. Push, let CI build
5. Gemini reviews PR automatically - address feedback
6. Merge when green

**Workflows**: `.github/workflows/` - `backend-pr.yml` + `frontend-pr.yml` (checks), `production.yml` (prod), `staging.yml` (staging)

## Design Principles

### Guiding Laws
- **Tesler's Law**: Complexity is conserved—move it into components, out of usage sites
- **Jakob's Law**: Developers expect familiar patterns. Boring beats brilliant.
- **Occam's Razor**: Simplest pattern that solves the problem wins

### From Software Engineering
- **"Make the change easy, then make the easy change"** (Kent Beck)
- **Principle of Least Astonishment**: Code should do what it looks like it does
- **Third time, extract**: Abstract after repetition, not before

### Application
- Absorb complexity into components, export simple interfaces
- Prefer composition over inheritance
- Design clean interfaces that support future extensions without current complexity

## Skills & Patterns

See `.claude/skills/` for implementation guidance:
- **`torale-design-patterns.md`** - UI patterns, anti-patterns, StatusBadge usage
- **`torale-component-library.md`** - When to use shared components vs custom

## Critical Patterns

### Frontend Auth (common mistake)
```typescript
// WRONG - Breaks in local dev (VITE_TORALE_NOAUTH=1)
import { useUser } from '@clerk/clerk-react'

// CORRECT - Works in both prod and local dev
import { useAuth } from '@/contexts/AuthContext'
const { user } = useAuth()
```

### Conventional Commits
```
feat: add new feature
fix: bug fix
docs: documentation
refactor: code change that neither fixes nor adds
```

## Quick Pointers

| What | Where |
|------|-------|
| API endpoints | `backend/src/torale/api/routers/` |
| DB schema | `docs-site/architecture/database-schema.md` |
| Migrations | `backend/alembic/versions/` |
| UI components | `frontend/src/components/torale/` |
| Changelog | `frontend/public/changelog.json` (auto-rendered) |
| Deployment | `docs-site/deployment/` |
| Architecture | `docs-site/architecture/` |

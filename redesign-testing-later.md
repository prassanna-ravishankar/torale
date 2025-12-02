# Redesign Testing Checklist

## Phase 2: Landing + Dashboard

### ✅ Verified Working
- Dynamic pricing displays correctly ("Free for 1 remaining user")
- API endpoints working (`/public/stats` returns correct data)
- Backend integration functional
- Sign in redirects to /dashboard correctly

### 🔲 Still Need to Test

#### Visual Testing
- [ ] Fonts load correctly (Space Grotesk, JetBrains Mono, Inter)
- [ ] Animations perform at 60fps
  - ParticleNetwork canvas animation
  - UniversalEventStream entry/exit animations
  - SystemTrace scroll-triggered progression
  - Dashboard Signal Card hover animations
- [ ] Colors match design system (canvas #fafafa, accent red, brutalist shadows)

#### Functional Testing - Landing
- [ ] Navigation links work (Use Cases, Pricing anchors, Changelog route)
- [ ] Sign In → /sign-in → after auth → /dashboard
- [ ] Start Monitoring → /dashboard (requires auth)
- [ ] Footer links (docs, API reference, status, GitHub)

#### Functional Testing - Dashboard
- [ ] Dashboard loads tasks correctly
- [ ] Signal Cards display all task info (name, query, schedule, status)
- [ ] StatCard metrics accurate (Active, Total, Completed, Paused counts)
- [ ] Filter buttons work (All, Active, Completed, Paused)
- [ ] Search filters tasks by name/query
- [ ] View toggle (Grid/List) - note: list view not implemented yet
- [ ] Create task button opens dialog
- [ ] Task actions work (Edit, Run, Pause/Resume, Delete)
- [ ] Empty state shows "Deploy New Monitor" when no tasks

#### Mobile Responsive Testing
- [ ] Mobile (375px): Navigation, hero, cards stack properly
- [ ] Tablet (768px): 2-column grid, SystemTrace visible
- [ ] Desktop (1024px+): Full 3-column grid, all animations

#### Performance
- [ ] Lighthouse score >90
- [ ] ParticleNetwork doesn't impact scroll performance
- [ ] Bundle size acceptable (current: CSS 86KB, JS 926KB)

### Browser Testing
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Mobile Safari
- [ ] Chrome Mobile

## Phase 3: Task Flows (Not Yet Started)

These still have OLD design and need to be redesigned:
- TaskCreationDialog (create task form)
- TaskEditDialog (edit task form)
- TaskPreviewModal (run/preview results)
- CustomScheduleDialog (schedule builder)
- TaskDetail page (task detail view)
- ExecutionTimeline (execution history)

## Phase 4: Settings & Admin

✅ **Completed:**
- Changelog.tsx - Neo-brutalist timeline with animated cards, decorative corners, spring physics
- ChangelogEntryCard.tsx - Brutalist card styling with type badges and GitHub PR links

🔲 **Still Need to Test:**
- Changelog.tsx route (/changelog)
- Timeline animations (stagger, scroll-triggered)
- Type badges (feature/improvement/fix/infra/research)
- Mobile responsiveness (timeline shifts to left on mobile)
- PR links to GitHub
- "End of Line" marker at bottom

## Troubleshooting

### Port Conflict on 8000
**Symptom**: API endpoints return 404 even though backend is running
**Cause**: Another process using port 8000 (check with `lsof -i :8000`)
**Fix**: Kill conflicting process or restart docker-compose

### Sign In Loops to Landing
**Symptom**: After signing in, redirects back to landing page
**Cause**: AuthRedirect component sending to `/` instead of `/dashboard`
**Fix**: Already fixed in latest code (App.tsx line 67)

### CORS Errors
**Symptom**: CORS errors for `/api` or `/public` requests
**Cause**: Backend not running or Vite proxy not configured
**Fix**: Ensure backend running, restart Vite dev server for proxy changes

## Commands

```bash
# Start everything (backend + frontend)
just dev-all

# Or separately:
# Terminal 1: Backend
docker compose up -d

# Terminal 2: Frontend
cd frontend && npm run dev

# Check running services
docker compose ps

# Check port conflicts
lsof -i :8000

# Test API directly
curl http://localhost:8000/public/stats
```

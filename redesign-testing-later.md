# Redesign Testing Checklist

## Landing Page Testing (Phase 2)

### Visual Testing
- [ ] **Fonts load correctly**
  - Space Grotesk for headings (hero, section titles)
  - JetBrains Mono for badges, terminal, code snippets
  - Check Network tab for Google Fonts CDN requests

- [ ] **Animations perform at 60fps**
  - ParticleNetwork canvas animation (should be smooth)
  - UniversalEventStream entry/exit animations (spring physics)
  - SystemTrace scroll-triggered progression
  - Hero fade-in on mount

- [ ] **Colors match design system**
  - Canvas background: #fafafa (zinc-50)
  - Accent red: hsl(10, 90%, 55%)
  - Status badge pulse animation
  - Brutalist shadows on buttons

### Functional Testing
- [ ] **Navigation links work**
  - Logo � / (landing page)
  - Use Cases � #use-cases anchor scroll
  - Pricing � #pricing anchor scroll
  - Changelog � /changelog route
  - Sign In � /sign-in route
  - Start Monitoring � /dashboard (redirects to /sign-in if not authed)

- [ ] **Footer links work**
  - Product > Use Cases � #use-cases
  - Product > Changelog � /changelog
  - Developers > Documentation � https://docs.torale.ai (new tab)
  - Developers > API Reference � https://api.torale.ai/redoc (new tab)
  - Developers > Status � https://torale.openstatus.dev (new tab)
  - Community > GitHub � https://github.com/torale (new tab)
  - Footer icons � GitHub, OpenStatus (new tabs)

- [ ] **Dynamic pricing displays**
  - Start backend: `just dev` or `docker-compose up`
  - Restart frontend: `npm run dev` (for Vite proxy)
  - Check pricing shows: "Free for X remaining users"
  - If backend down: shows "Free while in beta"

- [ ] **Routing behavior**
  - `/` shows Landing (even if authenticated)
  - `/dashboard` shows Dashboard (requires auth)
  - Clicking "Create Monitor" � /dashboard � /sign-in redirect if not authed

### Mobile Responsive Testing
Test at breakpoints:
- [ ] **Mobile (375px)**
  - Navigation collapses properly
  - Hero stacks vertically
  - UniversalEventStream hidden on mobile (<lg)
  - Use case cards stack (1 col)
  - Terminal section responsive
  - Pricing card fits screen

- [ ] **Tablet (768px)**
  - 2-column use case grid
  - SystemTrace shows (hidden on mobile)

- [ ] **Desktop (1024px+)**
  - Full layout with UniversalEventStream
  - Sticky scroll SystemTrace terminal
  - 2-column use case grid

### Performance Testing
- [ ] **Bundle size acceptable**
  - Current: CSS 83.89 kB, JS 917.27 kB
  - Fonts from CDN shouldn't impact bundle
  - ParticleNetwork canvas should be lightweight

- [ ] **Lighthouse audit**
  - Performance > 90
  - Accessibility > 90
  - Best Practices > 90

### Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

## Anti-Patterns Check

###  Good Patterns Used
- Using Motion.dev compatibility layer (easy migration path)
- Component extraction (ParticleNetwork, UniversalEventStream, etc.)
- Using relative URLs with Vite proxy (CORS-free in dev)
- Proper TypeScript types
- Mobile-first responsive design
- Semantic HTML

### � Potential Issues to Watch
- **Font loading via CDN inline style**: Could cause FOUT (Flash of Unstyled Text)
  - Mitigation: Fonts load fast from Google CDN, acceptable for now
  - Alternative: Could switch to @fontsource later if needed

- **Canvas animations**: ParticleNetwork could impact performance on low-end devices
  - Mitigation: Particle count limited by screen width (`Math.min(width / 25, 60)`)
  - Consider: Add prefers-reduced-motion media query if needed

- **No error boundaries**: If components crash, whole page breaks
  - TODO: Add error boundary around Landing component sections

- **No loading states**: Pricing shows nothing while fetching capacity
  - Current: Falls back to "Free while in beta" (acceptable)
  - Consider: Add skeleton/pulse animation during fetch

### L Anti-Patterns Avoided
-  Not using `any` types (all properly typed)
-  Not mixing motion libraries (only Motion.dev)
-  Not hardcoding API URLs (using window.CONFIG + env vars)
-  Not using inline styles except for dynamic canvas/patterns
-  Not over-engineering (kept it simple)

## Known Issues

### CORS in Local Dev
**Issue**: `/public/stats` fetch fails with CORS error if backend not running
**Fix Applied**: Added `/public` proxy to vite.config.ts
**Action Required**: Restart Vite dev server after pulling this code

### Motion.dev API Differences
**Potential Issue**: Motion.dev might have slight API differences from Framer Motion
**Mitigation**: Using compatibility layer in `lib/motion-compat.ts`
**Watch for**:
- `scrollYProgress.onChange()` � `scrollYProgress.on('change', ...)`
- Layout animations might behave differently

**Testing Required**:
1. Test all scroll animations in SystemTrace
2. Test AnimatePresence in UniversalEventStream
3. Verify spring physics feel the same

## Next Phase: Dashboard Redesign

When ready to continue:
- [ ] Implement MockDashboard.tsx design
- [ ] Create StatCard component (KPI metrics)
- [ ] Transform TaskCard to Signal Card
- [ ] Update Header component
- [ ] Add Mission Control layout

## Commands to Remember

```bash
# IMPORTANT: Start backend FIRST (required for dashboard to work)
cd backend
just dev
# This starts: PostgreSQL, Temporal, API server, Workers

# Then start frontend (restart if proxy added)
cd frontend
npm run dev

# Build and check bundle size
npm run build

# Run Lighthouse
npx lighthouse http://localhost:3000 --view
```

## Critical: Backend Must Be Running

**The dashboard will NOT work without the backend running!**

Why:
- Dashboard needs to fetch tasks from `/api/v1/tasks`
- Task creation needs `/api/v1/templates` for templates
- User sync needs `/api/v1/auth/sync-user`
- All these are proxied by Vite in dev mode

**Symptoms if backend is down:**
- CORS errors in console
- "Failed to sync user" error
- "Failed to load tasks" error
- "Failed to load templates" error
- Empty dashboard

**Fix:**
```bash
cd backend && just dev
# Wait for "Application startup complete" message
# Then refresh frontend
```

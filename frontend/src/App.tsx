import React, { lazy, Suspense, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate, useParams, useLocation } from 'react-router-dom'
import { AppShell, type Crumb } from '@/components/app/AppShell'
import { Toaster } from '@/components/ui/sonner'
import { Loader2 } from 'lucide-react'
import { useApiSetup } from '@/hooks/useApi'
import { useAuth } from '@/contexts/AuthContext'
import { captureEvent, initPostHog } from '@/lib/posthog'
import { sanitizePath } from '@/lib/analytics'
import { OrganizationJsonLd } from '@/components/OrganizationJsonLd'

// Lazy load heavy components for better performance
const Dashboard = lazy(() => import('@/components/Dashboard').then(m => ({ default: m.Dashboard })))
const TaskDetail = lazy(() => import('@/components/TaskDetail').then(m => ({ default: m.TaskDetail })))
const Landing = lazy(() => import('@/components/Landing'))
const Changelog = lazy(() => import('@/components/Changelog'))
const Admin = lazy(() => import('@/route-views/Admin').then(m => ({ default: m.Admin })))
const NotificationSettingsPage = lazy(() => import('@/route-views/NotificationSettingsPage').then(m => ({ default: m.NotificationSettingsPage })))
const ConnectorsPage = lazy(() => import('@/route-views/ConnectorsPage').then(m => ({ default: m.ConnectorsPage })))
import { connectorsEnabled } from '@/components/connectors/connectorsFlag'
const TermsOfService = lazy(() => import('@/route-views/TermsOfService').then(m => ({ default: m.TermsOfService })))
const PrivacyPolicy = lazy(() => import('@/route-views/PrivacyPolicy').then(m => ({ default: m.PrivacyPolicy })))
const NotFound = lazy(() => import('@/route-views/NotFound'))
const CapacityGate = lazy(() => import('@/components/CapacityGate').then(m => ({ default: m.CapacityGate })))
const WaitlistPage = lazy(() => import('@/components/WaitlistPage').then(m => ({ default: m.WaitlistPage })))
const Explore = lazy(() => import('@/route-views/Explore').then(m => ({ default: m.Explore })))
const ComparePage = lazy(() => import('@/route-views/ComparePage').then(m => ({ default: m.ComparePage })))
const UseCasePage = lazy(() => import('@/route-views/UseCasePage').then(m => ({ default: m.UseCasePage })))
const ConceptPage = lazy(() => import('@/route-views/ConceptPage').then(m => ({ default: m.ConceptPage })))
const Welcome = lazy(() => import('@/components/Welcome').then(m => ({ default: m.Welcome })))
const SignInPage = lazy(() => import('@/route-views/SignInPage'))
const SignUpPage = lazy(() => import('@/route-views/SignUpPage'))

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isLoaded, isAuthenticated } = useAuth()

  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/sign-in" replace />
  }

  return <>{children}</>
}

function ConnectorsRoute() {
  const { isLoaded, user } = useAuth()
  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }
  if (!connectorsEnabled(user)) {
    return <Navigate to="/settings/notifications" replace />
  }
  return <ConnectorsPage />
}

function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30">
      {children}
    </div>
  )
}

/**
 * Thin wrapper around AppShell for routes that just need static crumbs + no
 * page-supplied actions. Pages that own their own crumbs/actions/watches data
 * can render <AppShell> directly and skip this.
 */
function AppLayout({ children, crumbs }: { children: React.ReactNode; crumbs: Crumb[] }) {
  return <AppShell crumbs={crumbs}>{children}</AppShell>
}

function AuthRedirect({ children }: { children: React.ReactNode }) {
  const { isLoaded, isAuthenticated } = useAuth()

  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}

function ScrollToTop() {
  const { pathname } = useLocation()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return null
}

export default function App() {
  const navigate = useNavigate()
  const location = useLocation()

  // Initialize API client with Clerk authentication
  useApiSetup()

  // Initialize PostHog early for anonymous tracking
  // Will be re-identified when user logs in via auth providers
  useEffect(() => {
    initPostHog()
  }, [])

  // Track page views
  useEffect(() => {
    captureEvent('$pageview', {
      path: sanitizePath(location.pathname),
    })
  }, [location.pathname])

  const handleTaskClick = (taskId: string, justCreated?: boolean) => {
    navigate(`/tasks/${taskId}${justCreated ? '?justCreated=true' : ''}`)
  }

  const handleBackToDashboard = () => {
    navigate('/')
  }

  return (
    <>
      <ScrollToTop />
      <OrganizationJsonLd />
      <Suspense fallback={
        <div className="min-h-screen flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      }>
        <Routes>
        <Route
          path="/sign-in/*"
          element={
            <AuthRedirect>
              <AuthLayout>
                <SignInPage />
              </AuthLayout>
            </AuthRedirect>
          }
        />
        <Route
          path="/sign-up/*"
          element={
            <AuthRedirect>
              <AuthLayout>
                <CapacityGate fallback={<Navigate to="/waitlist" replace />}>
                  <SignUpPage />
                </CapacityGate>
              </AuthLayout>
            </AuthRedirect>
          }
        />
        <Route
          path="/waitlist"
          element={
            <AuthRedirect>
              <CapacityGate fallback={<WaitlistPage />}>
                <Navigate to="/sign-up" replace />
              </CapacityGate>
            </AuthRedirect>
          }
        />
        <Route
          path="/changelog"
          element={<Changelog />}
        />
        <Route
          path="/terms"
          element={<TermsOfService />}
        />
        <Route
          path="/privacy"
          element={<PrivacyPolicy />}
        />
        <Route
          path="/explore"
          element={
            <AppLayout crumbs={[{ label: 'Explore' }]}>
              <Explore />
            </AppLayout>
          }
        />
        <Route
          path="/compare/:tool"
          element={<ComparePage />}
        />
        <Route
          path="/use-cases/:usecase"
          element={<UseCasePage />}
        />
        <Route
          path="/concepts/:concept"
          element={<ConceptPage />}
        />
        <Route
          path="/"
          element={<HomeRoute />}
        />
        <Route
          path="/welcome"
          element={
            <ProtectedRoute>
              <AppLayout crumbs={[{ label: 'Welcome' }]}>
                <Welcome />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              {/* Dashboard owns its AppShell so the Sidebar can read watches data. */}
              <Dashboard onTaskClick={handleTaskClick} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/tasks/:taskId"
          element={
            // TaskDetail owns its AppShell (renders watch-specific crumbs + actions).
            <TaskDetailRoute onBack={handleBackToDashboard} onDeleted={handleBackToDashboard} />
          }
        />
        <Route
          path="/watches/:taskId"
          element={<WatchRouteRedirect />}
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AppLayout crumbs={[{ label: 'Admin' }]}>
                <Admin />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={<Navigate to="/settings/notifications" replace />}
        />
        <Route
          path="/settings/notifications"
          element={
            <ProtectedRoute>
              <AppLayout crumbs={[{ label: 'Settings', href: '/settings' }, { label: 'Notifications' }]}>
                <NotificationSettingsPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings/connectors"
          element={
            <ProtectedRoute>
              <AppLayout crumbs={[{ label: 'Settings', href: '/settings' }, { label: 'Connectors' }]}>
                <ConnectorsRoute />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        {/* Catch-all 404 — emits noindex so unknown URLs don't get indexed as
            soft-404s. Must be last. See #305. */}
        <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
      <Toaster />
    </>
  )
}

function TaskDetailRoute({ onBack, onDeleted }: { onBack: () => void; onDeleted: () => void }) {
  const { taskId } = useParams()
  const { user } = useAuth()

  if (!taskId) {
    return <Navigate to="/" replace />
  }

  return (
    <TaskDetail
      taskId={taskId}
      onBack={onBack}
      onDeleted={onDeleted}
      currentUserId={user?.id ?? undefined}
    />
  )
}

function WatchRouteRedirect() {
  const { taskId } = useParams()
  const location = useLocation()

  if (!taskId) {
    return <Navigate to="/" replace />
  }

  return <Navigate to={`/tasks/${encodeURIComponent(taskId)}${location.search}`} replace />
}

function HomeRoute() {
  // Always show Landing page at / (even if authenticated)
  return <Landing />
}

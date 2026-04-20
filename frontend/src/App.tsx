import React, { lazy, Suspense, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate, useParams, useLocation } from 'react-router-dom'
import { Header } from '@/components/Header'
import { MobileNav } from '@/components/MobileNav'
import { Toaster } from '@/components/ui/sonner'
import { Loader2 } from 'lucide-react'
import { useApiSetup } from '@/hooks/useApi'
import { useAuth } from '@/contexts/AuthContext'
import { captureEvent, initPostHog } from '@/lib/posthog'
import { sanitizePath } from '@/lib/analytics'

// Lazy load heavy components for better performance
const Dashboard = lazy(() => import('@/components/Dashboard').then(m => ({ default: m.Dashboard })))
const TaskDetail = lazy(() => import('@/components/TaskDetail').then(m => ({ default: m.TaskDetail })))
const Landing = lazy(() => import('@/components/Landing'))
const Changelog = lazy(() => import('@/components/Changelog'))
const Admin = lazy(() => import('@/pages/Admin').then(m => ({ default: m.Admin })))
const NotificationSettingsPage = lazy(() => import('@/pages/NotificationSettingsPage').then(m => ({ default: m.NotificationSettingsPage })))
const ConnectorsPage = lazy(() => import('@/pages/ConnectorsPage').then(m => ({ default: m.ConnectorsPage })))
import { connectorsEnabled } from '@/components/connectors/connectorsFlag'
const TermsOfService = lazy(() => import('@/pages/TermsOfService').then(m => ({ default: m.TermsOfService })))
const PrivacyPolicy = lazy(() => import('@/pages/PrivacyPolicy').then(m => ({ default: m.PrivacyPolicy })))
const CapacityGate = lazy(() => import('@/components/CapacityGate').then(m => ({ default: m.CapacityGate })))
const WaitlistPage = lazy(() => import('@/components/WaitlistPage').then(m => ({ default: m.WaitlistPage })))
const Explore = lazy(() => import('@/pages/Explore').then(m => ({ default: m.Explore })))
const ComparePage = lazy(() => import('@/pages/ComparePage').then(m => ({ default: m.ComparePage })))
const UseCasePage = lazy(() => import('@/pages/UseCasePage').then(m => ({ default: m.UseCasePage })))
const ConceptPage = lazy(() => import('@/pages/ConceptPage').then(m => ({ default: m.ConceptPage })))
const Welcome = lazy(() => import('@/components/Welcome').then(m => ({ default: m.Welcome })))
const SignInPage = lazy(() => import('@/pages/SignInPage'))
const SignUpPage = lazy(() => import('@/pages/SignUpPage'))

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

function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-8 pb-24 md:pb-8">
        {children}
      </main>
      <MobileNav />
    </div>
  )
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
            <AppLayout>
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
              <AppLayout>
                <Welcome />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Dashboard onTaskClick={handleTaskClick} />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/tasks/:taskId"
          element={
            <AppLayout>
              <TaskDetailRoute onBack={handleBackToDashboard} onDeleted={handleBackToDashboard} />
            </AppLayout>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AppLayout>
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
              <AppLayout>
                <NotificationSettingsPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings/connectors"
          element={
            <ProtectedRoute>
              <AppLayout>
                <ConnectorsRoute />
              </AppLayout>
            </ProtectedRoute>
          }
        />
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
      currentUserId={user?.id}
    />
  )
}

function HomeRoute() {
  // Always show Landing page at / (even if authenticated)
  return <Landing />
}

import React from 'react'
import { Routes, Route, Navigate, useNavigate, useParams } from 'react-router-dom'
import { SignIn, SignUp } from '@clerk/clerk-react'
import { Dashboard } from '@/components/Dashboard'
import { TaskDetail } from '@/components/TaskDetail'
import Landing from '@/components/Landing'
import Changelog from '@/components/Changelog'
import { Header } from '@/components/Header'
import { Admin } from '@/pages/Admin'
import { NotificationSettingsPage } from '@/pages/NotificationSettingsPage'
import { CapacityGate } from '@/components/CapacityGate'
import { WaitlistPage } from '@/components/WaitlistPage'
import { Toaster } from '@/components/ui/sonner'
import { Loader2 } from 'lucide-react'
import { useApiSetup } from '@/hooks/useApi'
import { useAuth } from '@/contexts/AuthContext'

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
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>
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

export default function App() {
  const navigate = useNavigate()

  // Initialize API client with Clerk authentication
  useApiSetup()

  const handleTaskClick = (taskId: string, justCreated?: boolean) => {
    navigate(`/tasks/${taskId}${justCreated ? '?justCreated=true' : ''}`)
  }

  const handleBackToDashboard = () => {
    navigate('/')
  }

  return (
    <>
      <Routes>
        <Route
          path="/sign-in/*"
          element={
            <AuthRedirect>
              <AuthLayout>
                <SignIn
                  routing="path"
                  path="/sign-in"
                  signUpUrl="/sign-up"
                  forceRedirectUrl="/dashboard"
                  fallbackRedirectUrl="/dashboard"
                />
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
                  <SignUp
                    routing="path"
                    path="/sign-up"
                    signInUrl="/sign-in"
                    forceRedirectUrl="/dashboard"
                    fallbackRedirectUrl="/dashboard"
                  />
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
          path="/"
          element={<HomeRoute onTaskClick={handleTaskClick} />}
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
            <ProtectedRoute>
              <AppLayout>
                <TaskDetailRoute onBack={handleBackToDashboard} onDeleted={handleBackToDashboard} />
              </AppLayout>
            </ProtectedRoute>
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
          path="/settings/notifications"
          element={
            <ProtectedRoute>
              <AppLayout>
                <NotificationSettingsPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
      <Toaster />
    </>
  )
}

function TaskDetailRoute({ onBack, onDeleted }: { onBack: () => void; onDeleted: () => void }) {
  const { taskId } = useParams()
  if (!taskId) {
    return <Navigate to="/" replace />
  }
  return <TaskDetail taskId={taskId} onBack={onBack} onDeleted={onDeleted} />
}

function HomeRoute({ onTaskClick }: { onTaskClick: (taskId: string) => void }) {
  // Always show Landing page at / (even if authenticated)
  return <Landing />
}

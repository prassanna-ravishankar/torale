import React from 'react'
import { Routes, Route, Navigate, useNavigate, useParams } from 'react-router-dom'
import { SignedIn, SignedOut, SignIn, SignUp, useAuth as useClerkAuth } from '@clerk/clerk-react'
import { Dashboard } from '@/components/Dashboard'
import { TaskDetail } from '@/components/TaskDetail'
import Landing from '@/components/Landing'
import { Header } from '@/components/Header'
import { Toaster } from '@/components/ui/sonner'
import { Loader2 } from 'lucide-react'
import { useApiSetup } from '@/hooks/useApi'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isLoaded, userId } = useClerkAuth()

  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!userId) {
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
  const { isLoaded, userId } = useClerkAuth()

  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (userId) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

export default function App() {
  const navigate = useNavigate()

  // Initialize API client with Clerk authentication
  useApiSetup()

  const handleTaskClick = (taskId: string) => {
    navigate(`/tasks/${taskId}`)
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
                <SignIn routing="path" path="/sign-in" signUpUrl="/sign-up" />
              </AuthLayout>
            </AuthRedirect>
          }
        />
        <Route
          path="/sign-up/*"
          element={
            <AuthRedirect>
              <AuthLayout>
                <SignUp routing="path" path="/sign-up" signInUrl="/sign-in" />
              </AuthLayout>
            </AuthRedirect>
          }
        />
        <Route
          path="/"
          element={<HomeRoute onTaskClick={handleTaskClick} />}
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
  const { isLoaded, userId } = useClerkAuth()

  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (userId) {
    return (
      <AppLayout>
        <Dashboard onTaskClick={onTaskClick} />
      </AppLayout>
    )
  }

  return <Landing />
}

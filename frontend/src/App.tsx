import React from 'react'
import { Routes, Route, Navigate, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { LoginForm } from '@/components/LoginForm'
import { RegisterForm } from '@/components/RegisterForm'
import { Dashboard } from '@/components/Dashboard'
import { TaskDetail } from '@/components/TaskDetail'
import { Header } from '@/components/Header'
import { Toaster } from '@/components/ui/sonner'
import { Loader2 } from 'lucide-react'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
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
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (user) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

export default function App() {
  const navigate = useNavigate()

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
          path="/login"
          element={
            <AuthRedirect>
              <AuthLayout>
                <LoginForm onSwitchToRegister={() => navigate('/register')} />
              </AuthLayout>
            </AuthRedirect>
          }
        />
        <Route
          path="/register"
          element={
            <AuthRedirect>
              <AuthLayout>
                <RegisterForm onSwitchToLogin={() => navigate('/login')} />
              </AuthLayout>
            </AuthRedirect>
          }
        />
        <Route
          path="/"
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

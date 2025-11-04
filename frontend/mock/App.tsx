import React, { useState } from "react";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { LoginForm } from "./components/auth/LoginForm";
import { RegisterForm } from "./components/auth/RegisterForm";
import { Dashboard } from "./components/dashboard/Dashboard";
import { TaskDetail } from "./components/tasks/TaskDetail";
import { Header } from "./components/layout/Header";
import { Loader2 } from "lucide-react";

type View = "dashboard" | "task-detail";

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [authView, setAuthView] = useState<"login" | "register">("login");
  const [currentView, setCurrentView] = useState<View>("dashboard");
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  const handleTaskClick = (taskId: string) => {
    setSelectedTaskId(taskId);
    setCurrentView("task-detail");
  };

  const handleBackToDashboard = () => {
    setCurrentView("dashboard");
    setSelectedTaskId(null);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/30">
        {authView === "login" ? (
          <LoginForm onSwitchToRegister={() => setAuthView("register")} />
        ) : (
          <RegisterForm onSwitchToLogin={() => setAuthView("login")} />
        )}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-8">
        {currentView === "dashboard" && (
          <Dashboard onTaskClick={handleTaskClick} />
        )}
        {currentView === "task-detail" && selectedTaskId && (
          <TaskDetail
            taskId={selectedTaskId}
            onBack={handleBackToDashboard}
            onDeleted={handleBackToDashboard}
          />
        )}
      </main>
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

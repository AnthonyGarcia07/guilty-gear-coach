import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Shell } from "./components/Shell";
import { useAuth } from "./auth/AuthContext";
import { Coaching } from "./pages/Coaching";
import { Dashboard } from "./pages/Dashboard";
import { Landing } from "./pages/Landing";
import { Login } from "./pages/Login";
import { MatchDetail } from "./pages/MatchDetail";
import { MatchFormPage } from "./pages/MatchFormPage";
import { MatchHistory } from "./pages/MatchHistory";

function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-screen">Loading fight data...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Shell>{children}</Shell>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login mode="login" />} />
      <Route path="/signup" element={<Login mode="signup" />} />
      <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
      <Route path="/coaching" element={<Protected><Coaching /></Protected>} />
      <Route path="/matches" element={<Protected><MatchHistory /></Protected>} />
      <Route path="/matches/new" element={<Protected><MatchFormPage /></Protected>} />
      <Route path="/matches/:id" element={<Protected><MatchDetail /></Protected>} />
    </Routes>
  );
}

import { ArrowRight, ShieldCheck, Swords, TrendingUp } from "lucide-react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function Landing() {
  const { user, loading } = useAuth();
  if (!loading && user) return <Navigate to="/dashboard" replace />;

  return (
    <main className="landing">
      <section className="landing-hero">
        <div className="hero-copy">
          <span className="eyebrow">Phase 1 manual match intelligence</span>
          <h1>Guilty Gear Coach</h1>
          <p>Track sets, expose habits, and turn match notes into a practice plan before AI coaching ever enters the ring.</p>
          <div className="hero-actions">
            <Link className="primary-button" to="/signup">Start tracking <ArrowRight size={18} /></Link>
            <Link className="secondary-button" to="/login">Log in</Link>
          </div>
        </div>
        <div className="scoreboard-panel">
          <div className="round-header"><span>Sol Badguy</span><strong>63%</strong><span>vs Ky</span></div>
          <div className="meter-line"><span style={{ width: "63%" }} /></div>
          <div className="coach-grid">
            <div><Swords size={20} /><strong>12</strong><span>Recent matches</span></div>
            <div><TrendingUp size={20} /><strong>+8%</strong><span>7-day win rate</span></div>
            <div><ShieldCheck size={20} /><strong>Anti-air</strong><span>Practice focus</span></div>
          </div>
        </div>
      </section>
    </main>
  );
}

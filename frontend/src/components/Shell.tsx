import type { ReactNode } from "react";
import { BarChart3, Lightbulb, LogOut, Plus, Swords } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function Shell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <span className="brand-mark">GG</span>
          <div>
            <strong>Guilty Gear Coach</strong>
            <span>{user?.username}</span>
          </div>
        </div>
        <nav>
          <NavLink to="/dashboard"><BarChart3 size={18} /> Dashboard</NavLink>
          <NavLink to="/matches"><Swords size={18} /> Match History</NavLink>
          <NavLink to="/coaching"><Lightbulb size={18} /> Coaching</NavLink>
          <NavLink to="/matches/new"><Plus size={18} /> Add Match</NavLink>
        </nav>
        <button className="ghost-button" onClick={() => { logout(); navigate("/"); }}>
          <LogOut size={18} /> Sign out
        </button>
      </aside>
      <main className="main-panel">{children}</main>
    </div>
  );
}

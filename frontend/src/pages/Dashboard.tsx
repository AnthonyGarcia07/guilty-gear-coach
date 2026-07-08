import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { DashboardStats } from "../types";

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    api.stats().then(setStats);
  }, []);

  if (!stats) return <div className="loading-panel">Loading dashboard...</div>;

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <span className="eyebrow">Match intelligence</span>
          <h1>Dashboard</h1>
        </div>
        <Link className="primary-button" to="/matches/new">Add Match</Link>
      </div>
      <div className="stat-grid">
        <article><span>Total matches</span><strong>{stats.total_matches}</strong></article>
        <article><span>Win rate</span><strong>{stats.win_rate}%</strong></article>
        <article><span>Wins / losses</span><strong>{stats.wins} / {stats.losses}</strong></article>
        <article><span>Top loss reason</span><strong>{stats.most_common_reason_for_loss?.label ?? "No losses logged"}</strong></article>
      </div>
      <div className="dashboard-grid">
        <section className="panel">
          <h2>Win rate by opponent</h2>
          <div className="bar-list">{stats.win_rate_by_opponent.map((item) => <div className="bar-row" key={item.opponent_character}><div><strong>{item.opponent_character}</strong><span>{item.matches} matches</span></div><div className="bar-track"><span style={{ width: `${item.win_rate}%` }} /></div><b>{item.win_rate}%</b></div>)}</div>
        </section>
        <section className="panel">
          <h2>Most common mistakes</h2>
          <div className="tag-cloud">{stats.most_common_mistake_tags.length ? stats.most_common_mistake_tags.map((tag) => <span key={tag.label}>{tag.label} <b>{tag.count}</b></span>) : <p className="muted">Mistake tags will appear as you log matches.</p>}</div>
        </section>
      </div>
      <section className="panel">
        <h2>Recent match history</h2>
        <div className="match-list">{stats.recent_matches.map((match) => <Link to={`/matches/${match.id}`} className="match-row" key={match.id}><span className={match.result}>{match.result}</span><strong>{match.player_character} vs {match.opponent_character}</strong><small>{match.played_on}</small><small>{match.practice_next || "No practice note yet"}</small></Link>)}</div>
      </section>
    </section>
  );
}

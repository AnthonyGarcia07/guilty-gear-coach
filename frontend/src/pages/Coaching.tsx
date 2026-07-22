import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { CoachingInsights } from "../types";

function displayValue(value: string | number | null) {
  return value ?? "Not enough data";
}

function streakLabel(type: CoachingInsights["current_streak_type"], count: number) {
  if (!type || count === 0) return "No matches";
  const suffix = count === 1 ? type : `${type}s`;
  return `${count} ${suffix}`;
}

export function Coaching() {
  const [insights, setInsights] = useState<CoachingInsights | null>(null);

  useEffect(() => {
    api.coachingInsights().then(setInsights);
  }, []);

  if (!insights) return <div className="loading-panel">Loading coaching insights...</div>;

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <span className="eyebrow">Coaching foundation</span>
          <h1>Deterministic Coaching</h1>
          <p className="muted">Insights generated from your match history only. No AI, no replay parsing.</p>
        </div>
      </div>
      <div className="coach-grid">
        <div><span>Current win rate</span><strong>{insights.overallWinRate}%</strong></div>
        <div><span>Current streak</span><strong>{streakLabel(insights.current_streak_type, insights.current_streak_count)}</strong></div>
        <div><span>Total matches</span><strong>{insights.totalMatches}</strong></div>
        <div><span>Most played character</span><strong>{displayValue(insights.mostPlayedCharacter)}</strong></div>
        <div><span>Best matchup</span><strong>{displayValue(insights.bestMatchup)}</strong></div>
        <div><span>Worst matchup</span><strong>{displayValue(insights.worstMatchup)}</strong></div>
        <div><span>Longest win streak</span><strong>{insights.longest_win_streak}</strong></div>
        <div><span>Longest losing streak</span><strong>{insights.longest_losing_streak}</strong></div>
      </div>
    </section>
  );
}

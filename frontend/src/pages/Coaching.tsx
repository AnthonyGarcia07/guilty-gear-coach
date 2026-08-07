import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { CoachingInsights, MatchupInsight } from "../types";

function displayPercent(value: number | null) {
  return value === null ? "Not enough data" : `${value}%`;
}

function displayValue(value: string | number | null) {
  return value ?? "Not enough data";
}

function streakLabel(type: CoachingInsights["streaks"]["current_streak_type"], count: number) {
  if (!type || count === 0) return "No matches";
  const suffix = count === 1 ? type : `${type}s`;
  return `${count} ${suffix}`;
}

function trendLabel(trend: CoachingInsights["performance"]["performance_trend"]) {
  if (!trend) return "More match history needed";
  return trend;
}

function matchupLine(matchup: MatchupInsight | null) {
  if (!matchup) return "Not enough qualified matchup data";
  return `${matchup.opponent_character}: ${matchup.wins}-${matchup.losses} (${matchup.win_rate}%)`;
}

export function CoachingContent({ insights }: { insights: CoachingInsights }) {
  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <span className="eyebrow">Advanced deterministic coaching</span>
          <h1>Coaching</h1>
          <p className="muted">Structured insights from your match history only. No AI, no replay parsing.</p>
        </div>
      </div>

      <section className="panel">
        <h2>Performance</h2>
        <div className="coach-grid">
          <div><span>Overall win rate</span><strong>{displayPercent(insights.performance.overall_win_rate)}</strong><small>{insights.performance.matches_analyzed} sets analyzed</small></div>
          <div><span>Recent 5 win rate</span><strong>{displayPercent(insights.performance.recent_5_win_rate)}</strong><small>Last 5 sets</small></div>
          <div><span>Recent 10 win rate</span><strong>{displayPercent(insights.performance.recent_10_win_rate)}</strong><small>Last 10 sets</small></div>
          <div><span>Previous 10 win rate</span><strong>{displayPercent(insights.performance.previous_10_win_rate)}</strong><small>Baseline before the recent 10</small></div>
          <div><span>Performance trend</span><strong>{trendLabel(insights.performance.performance_trend)}</strong><small>{insights.performance.performance_trend ? `${insights.performance.trend_threshold}% threshold` : "Need 20 sets to compare windows"}</small></div>
        </div>
      </section>

      <section className="panel">
        <h2>Streaks</h2>
        <div className="coach-grid">
          <div><span>Current streak</span><strong>{streakLabel(insights.streaks.current_streak_type, insights.streaks.current_streak_count)}</strong></div>
          <div><span>Longest win streak</span><strong>{insights.streaks.longest_win_streak}</strong></div>
          <div><span>Longest losing streak</span><strong>{insights.streaks.longest_losing_streak}</strong></div>
        </div>
      </section>

      <section className="panel">
        <h2>Matchups</h2>
        <div className="coach-grid">
          <div><span>Most played character</span><strong>{displayValue(insights.character.most_played_character)}</strong><small>{insights.character.matches ? `${insights.character.matches} sets` : "No character data yet"}</small></div>
          <div><span>Strongest qualified matchup</span><strong>{matchupLine(insights.matchups.strongest_qualified_matchup)}</strong><small>Minimum {insights.matchups.minimum_sample_size} sets</small></div>
          <div><span>Weakest qualified matchup</span><strong>{matchupLine(insights.matchups.weakest_qualified_matchup)}</strong><small>Minimum {insights.matchups.minimum_sample_size} sets</small></div>
          <div><span>Most played matchup</span><strong>{matchupLine(insights.matchups.most_played_matchup)}</strong></div>
          <div><span>Most losses</span><strong>{matchupLine(insights.matchups.matchup_with_most_losses)}</strong></div>
        </div>
        {insights.matchups.recent_matchup_trends.length > 0 ? (
          <div className="tag-cloud coaching-list">
            {insights.matchups.recent_matchup_trends.map((trend) => <span key={trend.opponent_character}>{trend.opponent_character}: {trend.previous_win_rate}% → {trend.recent_win_rate}% ({trend.trend})</span>)}
          </div>
        ) : <p className="muted">Play at least 6 sets against a character to unlock a matchup trend.</p>}
        {insights.matchups.matchups_needing_more_data.length > 0 && <p className="muted">Needs more data: {insights.matchups.matchups_needing_more_data.map((matchup) => `${matchup.opponent_character} (${matchup.matches}/${insights.matchups.minimum_sample_size})`).join(", ")}</p>}
      </section>

      <section className="panel">
        <h2>Patterns</h2>
        <div className="coach-grid">
          <div><span>Top repeated mistake</span><strong>{insights.patterns.top_mistake ? insights.patterns.top_mistake.tag : "No repeated mistake yet"}</strong><small>{insights.patterns.top_mistake ? `${insights.patterns.top_mistake.count} tagged losses` : "Tag losses to reveal patterns"}</small></div>
          <div><span>Recent losses analyzed</span><strong>{insights.patterns.recent_loss_count}</strong><small>Recent loss window</small></div>
        </div>
        {insights.patterns.recent_loss_mistakes.length > 0 ? (
          <div className="tag-cloud coaching-list">
            {insights.patterns.recent_loss_mistakes.map((mistake) => <span key={mistake.tag}>{mistake.tag}: {mistake.count}/{mistake.losses_analyzed} losses{mistake.percentage_of_recent_losses !== null ? ` (${mistake.percentage_of_recent_losses}%)` : ""}</span>)}
          </div>
        ) : <p className="muted">Repeated mistake tags from recent losses will appear here.</p>}
      </section>

      <section className="panel">
        <h2>Practice Priorities</h2>
        {insights.patterns.practice_priorities.length > 0 ? (
          <div className="tag-cloud coaching-list">
            {insights.patterns.practice_priorities.map((priority) => <span key={priority.practice_next}>{priority.practice_next}: {priority.count}</span>)}
          </div>
        ) : <p className="muted">Repeated practice notes from losses will appear after enough match history.</p>}
      </section>

      <section className="panel">
        <h2>Recommended Focus</h2>
        {insights.recommendations.length > 0 ? (
          <div className="recommendation-list">
            {insights.recommendations.map((recommendation) => (
              <article className="recommendation-card" key={`${recommendation.type}-${recommendation.title}`}>
                <span className={`priority ${recommendation.priority}`}>{recommendation.priority}</span>
                <strong>{recommendation.title}</strong>
                <p>{recommendation.message}</p>
                <small>Evidence sample: {recommendation.sample_size}</small>
              </article>
            ))}
          </div>
        ) : <p className="muted">More match history is needed to produce evidence-based recommendations.</p>}
      </section>
    </section>
  );
}

export function Coaching() {
  const [insights, setInsights] = useState<CoachingInsights | null>(null);

  useEffect(() => {
    api.coachingInsights().then(setInsights);
  }, []);

  if (!insights) return <div className="loading-panel">Loading coaching insights...</div>;

  return <CoachingContent insights={insights} />;
}

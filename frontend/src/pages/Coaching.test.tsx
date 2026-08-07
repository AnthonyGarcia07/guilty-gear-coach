import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { CoachingContent } from "./Coaching";
import type { CoachingInsights } from "../types";

function makeInsights(overrides: Partial<CoachingInsights> = {}): CoachingInsights {
  const insights: CoachingInsights = {
    total_matches: 20,
    performance: {
      overall_win_rate: 55,
      recent_5_win_rate: 80,
      recent_10_win_rate: 70,
      previous_10_win_rate: 40,
      performance_trend: "improving",
      matches_analyzed: 20,
      trend_sample_size: 20,
      trend_threshold: 15
    },
    streaks: {
      longest_win_streak: 4,
      longest_losing_streak: 2,
      current_streak_type: "win",
      current_streak_count: 3
    },
    character: {
      most_played_character: "Bridget",
      matches: 18
    },
    matchups: {
      minimum_sample_size: 3,
      strongest_qualified_matchup: { opponent_character: "Ky Kiske", matches: 5, wins: 4, losses: 1, win_rate: 80, qualified: true },
      weakest_qualified_matchup: { opponent_character: "Slayer", matches: 8, wins: 2, losses: 6, win_rate: 25, qualified: true },
      most_played_matchup: { opponent_character: "Slayer", matches: 8, wins: 2, losses: 6, win_rate: 25, qualified: true },
      matchup_with_most_losses: { opponent_character: "Slayer", matches: 8, wins: 2, losses: 6, win_rate: 25, qualified: true },
      matchups_needing_more_data: [{ opponent_character: "May", matches: 1, wins: 0, losses: 1, win_rate: 0, qualified: false }],
      matchup_records: [],
      recent_matchup_trends: [{ opponent_character: "Slayer", overall_win_rate: 30, recent_win_rate: 60, previous_win_rate: 10, recent_matches: 3, previous_matches: 3, trend: "improving" }],
      best_matchup: "Ky Kiske",
      worst_matchup: "Slayer"
    },
    patterns: {
      top_mistake: { tag: "missed anti-air", count: 4, losses_analyzed: 6, percentage_of_recent_losses: 66.7 },
      overall_mistakes: [],
      recent_loss_mistakes: [{ tag: "missed anti-air", count: 4, losses_analyzed: 6, percentage_of_recent_losses: 66.7 }],
      recent_loss_count: 6,
      practice_priorities: [{ practice_next: "anti-air practice", count: 3, losses_analyzed: 6 }]
    },
    recommendations: [
      {
        type: "repeated_mistake",
        priority: "high",
        title: "Work on missed anti-air",
        message: "missed anti-air appeared in 4 of your last 6 losses.",
        evidence: { tag: "missed anti-air" },
        sample_size: 6
      }
    ]
  };
  return { ...insights, ...overrides };
}

describe("CoachingContent", () => {
  it("renders advanced coaching sections and recommendations", () => {
    const html = renderToStaticMarkup(<CoachingContent insights={makeInsights()} />);

    expect(html).toContain("Performance");
    expect(html).toContain("Streaks");
    expect(html).toContain("Matchups");
    expect(html).toContain("Patterns");
    expect(html).toContain("Practice Priorities");
    expect(html).toContain("Recommended Focus");
    expect(html).toContain("Work on missed anti-air");
    expect(html).toContain("Slayer: 10% → 60% (improving)");
  });

  it("renders insufficient-data states without misleading zeros", () => {
    const html = renderToStaticMarkup(<CoachingContent insights={makeInsights({
      total_matches: 0,
      performance: {
        overall_win_rate: null,
        recent_5_win_rate: null,
        recent_10_win_rate: null,
        previous_10_win_rate: null,
        performance_trend: null,
        matches_analyzed: 0,
        trend_sample_size: 0,
        trend_threshold: 15
      },
      streaks: {
        longest_win_streak: 0,
        longest_losing_streak: 0,
        current_streak_type: null,
        current_streak_count: 0
      },
      character: { most_played_character: null, matches: 0 },
      matchups: {
        minimum_sample_size: 3,
        strongest_qualified_matchup: null,
        weakest_qualified_matchup: null,
        most_played_matchup: null,
        matchup_with_most_losses: null,
        matchups_needing_more_data: [],
        matchup_records: [],
        recent_matchup_trends: [],
        best_matchup: null,
        worst_matchup: null
      },
      patterns: {
        top_mistake: null,
        overall_mistakes: [],
        recent_loss_mistakes: [],
        recent_loss_count: 0,
        practice_priorities: []
      },
      recommendations: []
    })} />);

    expect(html).toContain("Not enough data");
    expect(html).toContain("More match history needed");
    expect(html).toContain("More match history is needed to produce evidence-based recommendations.");
  });

  it("renders matchup, trend, pattern, and practice insights", () => {
    const html = renderToStaticMarkup(<CoachingContent insights={makeInsights()} />);

    expect(html).toContain("Slayer: 2-6 (25%)");
    expect(html).toContain("missed anti-air: 4/6 losses");
    expect(html).toContain("anti-air practice: 3");
    expect(html).toContain("improving");
  });
});

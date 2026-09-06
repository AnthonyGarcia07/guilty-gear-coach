import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { DashboardContent } from "./Dashboard";
import type { DashboardStats } from "../types";

function makeStats(overrides: Partial<DashboardStats> = {}): DashboardStats {
  return {
    total_matches: 0,
    wins: 0,
    losses: 0,
    win_rate: 0,
    win_rate_by_opponent: [],
    most_common_mistake_tags: [],
    most_common_reason_for_loss: null,
    recent_matches: [],
    ...overrides,
  };
}

function renderDashboard(stats: DashboardStats) {
  return renderToStaticMarkup(
    <MemoryRouter>
      <DashboardContent stats={stats} />
    </MemoryRouter>
  );
}

describe("Dashboard loss reason fallback", () => {
  it("shows that loss reasons are missing when losses exist without a reason", () => {
    const html = renderDashboard(makeStats({ total_matches: 3, wins: 1, losses: 2, win_rate: 33.3 }));

    expect(html).toContain("No loss reasons logged");
    expect(html).not.toContain("No losses logged");
  });

  it("shows that no losses are logged when the player has no losses", () => {
    const html = renderDashboard(makeStats({ total_matches: 3, wins: 3, losses: 0, win_rate: 100 }));

    expect(html).toContain("No losses logged");
    expect(html).not.toContain("No loss reasons logged");
  });
});

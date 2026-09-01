import { describe, expect, it } from "vitest";
import { matchDeleteConfirmation, shouldRenderMatchForRoute } from "./MatchDetail";
import type { Match } from "../types";

function makeMatch(id: number): Match {
  return {
    id,
    player_character: "Sol Badguy",
    opponent_character: "Ky Kiske",
    result: "win",
    played_on: "2026-07-01",
    rank_floor: "Gold",
    duration_seconds: 180,
    rounds_won: 2,
    rounds_lost: 1,
    first_to: 2,
    notes: `Match ${id}`,
    mistake_tags: [],
    strength_tags: [],
    reason_for_loss: null,
    practice_next: null,
    replay_filename: id === 1 ? "legacy-a.rep" : null,
    created_at: "2026-07-01T00:00:00Z",
    updated_at: "2026-07-01T00:00:00Z"
  };
}

describe("MatchDetail route identity rendering", () => {
  it("does not render Match A content while the route is loading Match B", () => {
    expect(shouldRenderMatchForRoute(makeMatch(1), "2")).toBe(false);
  });

  it("renders Match B only after the loaded match matches the route", () => {
    expect(shouldRenderMatchForRoute(makeMatch(2), "2")).toBe(true);
  });

  it("uses the loading state when no route-matching match is available", () => {
    expect(shouldRenderMatchForRoute(null, "2")).toBe(false);
    expect(shouldRenderMatchForRoute(makeMatch(1), undefined)).toBe(false);
  });

  it("uses destructive match delete confirmation wording", () => {
    expect(matchDeleteConfirmation).toEqual({
      title: "Delete match?",
      message: "This will permanently delete this match and all associated replay videos. This action cannot be undone.",
      confirmLabel: "Delete Match"
    });
  });
});

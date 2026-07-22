import { describe, expect, it, vi } from "vitest";
import { submitMatchUpdate, submitNewMatch } from "./matchSubmit";
import type { Match, MatchInput } from "../types";

const payload: MatchInput = {
  player_character: "Sol Badguy",
  opponent_character: "Ky Kiske",
  result: "win",
  played_on: "2026-07-01",
  rank_floor: "Iron",
  duration_seconds: 180,
  rounds_won: 2,
  rounds_lost: 1,
  first_to: 2,
  notes: "clean hit",
  mistake_tags: [],
  strength_tags: [],
  reason_for_loss: null,
  practice_next: null,
  replay_filename: null
};

const match: Match = {
  id: 7,
  ...payload,
  created_at: "2026-07-01T00:00:00Z",
  updated_at: "2026-07-01T00:00:00Z"
};

describe("match submit flows", () => {
  it("creates a match once and redirects to match history", async () => {
    const createMatch = vi.fn().mockResolvedValue(match);
    const updateMatch = vi.fn();
    const navigate = vi.fn();

    await submitNewMatch(payload, { createMatch, updateMatch }, navigate);

    expect(createMatch).toHaveBeenCalledTimes(1);
    expect(createMatch).toHaveBeenCalledWith(payload);
    expect(updateMatch).not.toHaveBeenCalled();
    expect(navigate).toHaveBeenCalledWith("/matches", { state: { message: "Match created successfully." } });
  });

  it("updates an existing match without creating a second record", async () => {
    const createMatch = vi.fn();
    const updateMatch = vi.fn().mockResolvedValue(match);
    const navigate = vi.fn();

    await submitMatchUpdate(7, payload, { createMatch, updateMatch }, navigate);

    expect(updateMatch).toHaveBeenCalledTimes(1);
    expect(updateMatch).toHaveBeenCalledWith(7, payload);
    expect(createMatch).not.toHaveBeenCalled();
    expect(navigate).toHaveBeenCalledWith("/matches", { state: { message: "Match updated successfully." } });
  });
});

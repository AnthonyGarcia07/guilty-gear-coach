import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import { MatchForm, sanitizeForm, type MatchFormState } from "./MatchForm";
import type { Match } from "../types";

const legacyMatch: Match = {
  id: 12,
  player_character: "Sol Badguy",
  opponent_character: "Ky Kiske",
  result: "win",
  played_on: "2026-07-01",
  rank_floor: "Gold",
  duration_seconds: 180,
  rounds_won: 2,
  rounds_lost: 1,
  first_to: 2,
  notes: "Legacy replay field test.",
  mistake_tags: [],
  strength_tags: [],
  reason_for_loss: null,
  practice_next: null,
  replay_filename: "legacy-set.rep",
  created_at: "2026-07-01T00:00:00Z",
  updated_at: "2026-07-01T00:00:00Z"
};

describe("MatchForm legacy replay field handling", () => {
  it("does not render the legacy replay placeholder input", () => {
    const html = renderToStaticMarkup(<MatchForm initial={legacyMatch} submitLabel="Update match" onSubmit={vi.fn()} />);

    expect(html).not.toContain("Replay / video placeholder");
    expect(html).not.toContain("legacy-set.rep");
  });

  it("preserves an existing legacy replay filename when sanitizing edit payloads", () => {
    const form: MatchFormState = {
      player_character: " Sol Badguy ",
      opponent_character: "Ky Kiske",
      result: "win",
      played_on: "2026-07-01",
      rank_floor: "Gold",
      duration_seconds: "180",
      rounds_won: "2",
      rounds_lost: "1",
      first_to: "2",
      notes: " Updated notes ",
      mistake_tags: [],
      strength_tags: [],
      reason_for_loss: "",
      practice_next: "",
      replay_filename: "legacy-set.rep"
    };

    expect(sanitizeForm(form).replay_filename).toBe("legacy-set.rep");
  });

  it("keeps new match payloads from creating legacy replay metadata", () => {
    const form: MatchFormState = {
      player_character: "Sol Badguy",
      opponent_character: "Ky Kiske",
      result: "win",
      played_on: "2026-07-01",
      rank_floor: "Gold",
      duration_seconds: "180",
      rounds_won: "2",
      rounds_lost: "1",
      first_to: "2",
      notes: "",
      mistake_tags: [],
      strength_tags: [],
      reason_for_loss: "",
      practice_next: "",
      replay_filename: ""
    };

    expect(sanitizeForm(form).replay_filename).toBeNull();
  });
});

import { describe, expect, it } from "vitest";
import { getMatchHistoryReturnFromState, matchHistoryReturnPath, safeMatchHistoryReturnPath } from "./matchHistoryReturn";

describe("match history return paths", () => {
  it("preserves page and oldest-played sort from match history", () => {
    expect(matchHistoryReturnPath("?page=2&sort=oldest_played")).toBe("/matches?page=2&sort=oldest_played");
    expect(safeMatchHistoryReturnPath("/matches?page=2&sort=oldest_played")).toBe("/matches?page=2&sort=oldest_played");
  });

  it("preserves last-updated sort without forcing the default sort", () => {
    expect(safeMatchHistoryReturnPath("/matches?sort=last_updated")).toBe("/matches?sort=last_updated");
  });

  it("falls back when no return state is present", () => {
    expect(getMatchHistoryReturnFromState(null)).toBe("/matches");
    expect(getMatchHistoryReturnFromState({})).toBe("/matches");
  });

  it("rejects unsafe external or unrelated return locations", () => {
    expect(safeMatchHistoryReturnPath("https://evil.example/matches?page=2")).toBe("/matches");
    expect(safeMatchHistoryReturnPath("//evil.example/matches?page=2")).toBe("/matches");
    expect(safeMatchHistoryReturnPath("/dashboard")).toBe("/matches");
    expect(safeMatchHistoryReturnPath("/matches/7")).toBe("/matches");
  });
});

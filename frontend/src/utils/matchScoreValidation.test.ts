import { describe, expect, it } from "vitest";
import { validateMatchScore } from "./matchScoreValidation";

describe("match score validation", () => {
  it.each([
    ["win", "2", "0", "2"],
    ["win", "2", "1", "2"],
    ["loss", "0", "2", "2"],
    ["loss", "1", "2", "2"],
    ["win", "3", "2", "3"],
    ["loss", "1", "3", "3"]
  ] as const)("accepts realistic completed %s score %s-%s FT%s", (result, roundsWon, roundsLost, firstTo) => {
    expect(validateMatchScore({ result, roundsWon, roundsLost, firstTo })).toEqual({});
  });

  it.each([
    ["win", "2323", "0", "2", "10 or lower"],
    ["win", "1", "1", "2", "cannot be tied"],
    ["loss", "2", "2", "3", "cannot be tied"],
    ["win", "1", "2", "2", "win must have your score ahead"],
    ["loss", "2", "1", "2", "loss must have the opponent score ahead"],
    ["win", "-1", "2", "2", "0 or greater"],
    ["win", "2", "0", "0", "greater than 0"],
    ["win", "1", "0", "2", "exactly one side reaching"]
  ] as const)("rejects invalid score %s %s-%s FT%s", (result, roundsWon, roundsLost, firstTo, message) => {
    const errors = validateMatchScore({ result, roundsWon, roundsLost, firstTo });

    expect(Object.values(errors).join(" ")).toContain(message);
  });
});

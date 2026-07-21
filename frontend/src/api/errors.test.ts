import { describe, expect, it } from "vitest";
import { normalizeErrorPayload, normalizeUnknownError } from "./errors";

describe("API error normalization", () => {
  it("uses a string detail as the message", () => {
    expect(normalizeErrorPayload({ detail: "Simple error" })).toEqual({
      message: "Simple error",
      fieldErrors: {}
    });
  });

  it("extracts messages and field errors from validation detail arrays", () => {
    expect(normalizeErrorPayload({
      detail: [
        { loc: ["body", "duration_seconds"], msg: "Duration must be between 1 and 1800 seconds", type: "value_error" }
      ]
    })).toEqual({
      message: "Duration must be between 1 and 1800 seconds",
      fieldErrors: { duration_seconds: "Duration must be between 1 and 1800 seconds" }
    });
  });

  it("combines multiple validation detail messages", () => {
    expect(normalizeErrorPayload({
      detail: [
        { loc: ["body", "played_on"], msg: "Date cannot be in the future" },
        { loc: ["body", "rank_floor"], msg: "Invalid rank" }
      ]
    })).toEqual({
      message: "Date cannot be in the future Invalid rank",
      fieldErrors: {
        played_on: "Date cannot be in the future",
        rank_floor: "Invalid rank"
      }
    });
  });

  it("falls back for object detail without rendering it", () => {
    expect(normalizeErrorPayload({ detail: { unexpected: "shape" } })).toEqual({
      message: "Unable to update match.",
      fieldErrors: {}
    });
  });

  it("falls back for an empty response body", () => {
    expect(normalizeErrorPayload(undefined)).toEqual({
      message: "Unable to update match.",
      fieldErrors: {}
    });
  });

  it("keeps readable network error messages", () => {
    expect(normalizeUnknownError(new TypeError("Failed to fetch"))).toEqual({
      message: "Failed to fetch",
      fieldErrors: {}
    });
  });
});

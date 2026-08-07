import { describe, expect, it } from "vitest";
import { matchHistorySearch, paginationItems, parseMatchHistoryParams, sortChangeSearch } from "./matchHistoryPagination";

describe("match history pagination helpers", () => {
  it("uses default page and sort for empty or invalid query params", () => {
    expect(parseMatchHistoryParams("")).toEqual({ page: 1, sort: "recently_played" });
    expect(parseMatchHistoryParams("?page=0&sort=bad")).toEqual({ page: 1, sort: "recently_played" });
    expect(parseMatchHistoryParams("?sort=unsafe")).toEqual({ page: 1, sort: "recently_played" });
  });

  it("parses valid page and sort query params", () => {
    expect(parseMatchHistoryParams("?page=3&sort=oldest_played")).toEqual({ page: 3, sort: "oldest_played" });
  });

  it("omits default params from canonical match history search", () => {
    expect(matchHistorySearch(1, "recently_played")).toBe("");
    expect(matchHistorySearch(3, "oldest_played")).toBe("?page=3&sort=oldest_played");
  });

  it("resets the page when changing sort", () => {
    expect(sortChangeSearch("oldest_played")).toBe("?sort=oldest_played");
    expect(sortChangeSearch("recently_played")).toBe("");
  });

  it("creates compact pagination items for long page ranges", () => {
    expect(paginationItems(5, 10)).toEqual([1, 2, "...", 4, 5, 6, "...", 9, 10]);
  });

  it("shows every page when the range is already compact", () => {
    expect(paginationItems(2, 3)).toEqual([1, 2, 3]);
  });
});

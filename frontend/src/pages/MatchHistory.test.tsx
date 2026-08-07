import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { MatchHistoryContent, requestMatchHistoryPage } from "./MatchHistory";
import type { Match, MatchListResponse, MatchSort } from "../types";

function makeMatch(overrides: Partial<Match> = {}): Match {
  return {
    id: 1,
    player_character: "Bridget",
    opponent_character: "Ky Kiske",
    result: "win",
    played_on: "2026-07-15",
    rank_floor: "Gold",
    duration_seconds: 240,
    rounds_won: 2,
    rounds_lost: 1,
    first_to: 2,
    notes: "Good pressure.",
    mistake_tags: ["missed anti-air"],
    strength_tags: ["corner pressure"],
    reason_for_loss: null,
    practice_next: "anti-air practice",
    replay_filename: null,
    created_at: "2026-07-15T12:00:00Z",
    updated_at: "2026-07-15T12:00:00Z",
    ...overrides
  };
}

function makePagination(overrides: Partial<MatchListResponse> = {}): MatchListResponse {
  return {
    items: [makeMatch()],
    page: 1,
    page_size: 20,
    total_items: 25,
    total_pages: 2,
    sort: "recently_played",
    ...overrides
  };
}

function renderContent(pagination: MatchListResponse | null = makePagination(), matches = pagination?.items ?? [], requestedSort: MatchSort = "recently_played", loading = false) {
  return renderToStaticMarkup(
    <MemoryRouter>
      <MatchHistoryContent
        matches={matches}
        pagination={pagination}
        requestedSort={requestedSort}
        loading={loading}
        query=""
        message=""
        onDismissMessage={vi.fn()}
        onQueryChange={vi.fn()}
        onPageChange={vi.fn()}
        onSortChange={vi.fn()}
      />
    </MemoryRouter>
  );
}

describe("MatchHistoryContent", () => {
  it("requests oldest played from the URL on the first match-history request", async () => {
    const listMatches = vi.fn().mockResolvedValue(makePagination({ sort: "oldest_played" }));

    await requestMatchHistoryPage("?page=2&sort=oldest_played", listMatches);

    expect(listMatches).toHaveBeenCalledTimes(1);
    expect(listMatches).toHaveBeenCalledWith({ page: 2, sort: "oldest_played" });
    expect(listMatches).not.toHaveBeenCalledWith(expect.objectContaining({ sort: "recently_played" }));
  });

  it("requests last updated from the URL on the first match-history request", async () => {
    const listMatches = vi.fn().mockResolvedValue(makePagination({ sort: "last_updated" }));

    await requestMatchHistoryPage("?sort=last_updated", listMatches);

    expect(listMatches).toHaveBeenCalledTimes(1);
    expect(listMatches).toHaveBeenCalledWith({ page: 1, sort: "last_updated" });
    expect(listMatches).not.toHaveBeenCalledWith(expect.objectContaining({ sort: "recently_played" }));
  });

  it("falls back to recently played for missing or invalid URL sort requests", async () => {
    const listMatches = vi.fn().mockResolvedValue(makePagination());

    await requestMatchHistoryPage("?sort=unsafe", listMatches);

    expect(listMatches).toHaveBeenCalledWith({ page: 1, sort: "recently_played" });
  });

  it("does not render stale rows while the requested query is loading", () => {
    const html = renderContent(null, [makeMatch()], "oldest_played", true);

    expect(html).toContain("Loading match history...");
    expect(html).not.toContain("Bridget vs Ky Kiske");
    expect(html).toContain("<option value=\"oldest_played\" selected=\"\">Oldest played</option>");
  });

  it("selects oldest played immediately before pagination loads", () => {
    const html = renderContent(null, [], "oldest_played");

    expect(html).toContain("<option value=\"oldest_played\" selected=\"\">Oldest played</option>");
  });

  it("selects last updated immediately before pagination loads", () => {
    const html = renderContent(null, [], "last_updated");

    expect(html).toContain("<option value=\"last_updated\" selected=\"\">Last updated</option>");
  });

  it("defaults to recently played when no requested sort is provided", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <MatchHistoryContent
          matches={[]}
          pagination={null}
          query=""
          message=""
          onDismissMessage={vi.fn()}
          onQueryChange={vi.fn()}
          onPageChange={vi.fn()}
          onSortChange={vi.fn()}
        />
      </MemoryRouter>
    );

    expect(html).toContain("<option value=\"recently_played\" selected=\"\">Recently played</option>");
  });

  it("renders the server-backed sort select and pagination summary", () => {
    const html = renderContent();

    expect(html).toContain("Recently played");
    expect(html).toContain("Last updated");
    expect(html).toContain("Oldest played");
    expect(html).toContain("Showing page 1 of 2");
    expect(html).toContain("25 recorded sets");
  });

  it("renders previous and next disabled states", () => {
    const firstPage = renderContent(makePagination({ page: 1, total_pages: 3 }));
    const finalPage = renderContent(makePagination({ page: 3, total_pages: 3 }));

    expect(firstPage).toContain("<button type=\"button\" disabled=\"\">Previous</button>");
    expect(finalPage).toContain("<button type=\"button\" disabled=\"\">Next</button>");
  });

  it("does not render pagination controls for a single page", () => {
    const html = renderContent(makePagination({ total_items: 1, total_pages: 1 }));

    expect(html).not.toContain("Match history pagination");
  });

  it("renders a helpful empty state when there are no matches", () => {
    const html = renderContent(makePagination({ items: [], total_items: 0, total_pages: 1 }), []);

    expect(html).toContain("No matches yet. Add your first set to start building match history.");
  });
});

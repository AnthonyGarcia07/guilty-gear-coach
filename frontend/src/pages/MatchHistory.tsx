import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Match, MatchListResponse, MatchSort } from "../types";
import { matchHistorySearch, paginationItems, parseMatchHistoryParams, sortChangeSearch } from "../utils/matchHistoryPagination";
import { matchHistoryReturnPath } from "../utils/matchHistoryReturn";

const sortLabels: Record<MatchSort, string> = {
  recently_played: "Recently played",
  last_updated: "Last updated",
  oldest_played: "Oldest played"
};

type ListMatches = (params?: { page?: number; page_size?: number; sort?: MatchSort }) => Promise<MatchListResponse>;

export function requestMatchHistoryPage(search: string, listMatches: ListMatches) {
  const params = parseMatchHistoryParams(search);
  return listMatches({ page: params.page, sort: params.sort });
}

export function MatchHistoryContent({
  matches,
  pagination,
  requestedSort = "recently_played",
  loading = false,
  query,
  message,
  onDismissMessage,
  onQueryChange,
  onPageChange,
  onSortChange
}: {
  matches: Match[];
  pagination: MatchListResponse | null;
  requestedSort?: MatchSort;
  loading?: boolean;
  query: string;
  message: string;
  onDismissMessage: () => void;
  onQueryChange: (query: string) => void;
  onPageChange: (page: number) => void;
  onSortChange: (sort: MatchSort) => void;
}) {
  const sort = pagination?.sort ?? requestedSort;
  const page = pagination?.page ?? 1;
  const totalPages = pagination?.total_pages ?? 1;
  const totalItems = pagination?.total_items ?? matches.length;
  const returnTo = matchHistoryReturnPath(pagination ? matchHistorySearch(page, sort) : "");
  const filtered = useMemo(() => matches.filter((match) => `${match.player_character} ${match.opponent_character} ${match.rank_floor} ${match.mistake_tags.join(" ")}`.toLowerCase().includes(query.toLowerCase())), [matches, query]);

  return (
    <section className="page-stack">
      <div className="page-header">
        <div><span className="eyebrow">Review lab</span><h1>Match History</h1></div>
        <Link className="primary-button" to="/matches/new">Add Match</Link>
      </div>
      {message && <p className="form-success" role="status">{message}<button type="button" onClick={onDismissMessage}>Dismiss</button></p>}
      <div className="history-toolbar">
        <input className="search-input" value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="Filter current page by character, rank, or tag" />
        <label>Sort<select value={sort} onChange={(event) => onSortChange(event.target.value as MatchSort)}>{Object.entries(sortLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
      </div>
      {loading ? <p className="muted">Loading match history...</p> : totalItems === 0 ? <p className="muted">No matches yet. Add your first set to start building match history.</p> : <p className="muted">Showing page {page} of {totalPages} · {totalItems} recorded sets</p>}
      {!loading && <div className="match-list large">{filtered.map((match) => <Link to={`/matches/${match.id}`} state={{ returnTo }} className="match-row" key={match.id}><span className={match.result}>{match.result}</span><strong>{match.player_character} vs {match.opponent_character}</strong><small>{match.rank_floor || "Unranked"} · {match.played_on}</small><small>{match.reason_for_loss || match.strength_tags.join(", ") || "Open notes"}</small></Link>)}</div>}
      {!loading && totalItems > 0 && filtered.length === 0 && <p className="muted">No matches on this page match the current filter.</p>}
      {!loading && totalPages > 1 && <PaginationControls currentPage={page} totalPages={totalPages} onPageChange={onPageChange} />}
    </section>
  );
}

function PaginationControls({ currentPage, totalPages, onPageChange }: { currentPage: number; totalPages: number; onPageChange: (page: number) => void }) {
  return (
    <nav className="pagination" aria-label="Match history pagination">
      <button type="button" disabled={currentPage === 1} onClick={() => onPageChange(currentPage - 1)}>Previous</button>
      {paginationItems(currentPage, totalPages).map((item, index) => item === "..." ? <span className="pagination-ellipsis" key={`ellipsis-${index}`}>...</span> : (
        <button type="button" className={item === currentPage ? "active" : ""} aria-current={item === currentPage ? "page" : undefined} onClick={() => onPageChange(item)} key={item}>{item}</button>
      ))}
      <button type="button" disabled={currentPage === totalPages} onClick={() => onPageChange(currentPage + 1)}>Next</button>
    </nav>
  );
}

export function MatchHistory() {
  const [history, setHistory] = useState<{ matches: Match[]; pagination: MatchListResponse; queryKey: string } | null>(null);
  const [query, setQuery] = useState("");
  const location = useLocation();
  const navigate = useNavigate();
  const [message, setMessage] = useState(() => typeof location.state === "object" && location.state && "message" in location.state ? String(location.state.message) : "");
  const params = useMemo(() => parseMatchHistoryParams(location.search), [location.search]);
  const queryKey = matchHistorySearch(params.page, params.sort);
  const currentHistory = history?.queryKey === queryKey ? history : null;

  useEffect(() => {
    let active = true;
    requestMatchHistoryPage(location.search, api.listMatches).then((response) => {
      if (!active) return;
      const canonicalSearch = matchHistorySearch(response.page, response.sort);
      setHistory({ matches: response.items, pagination: response, queryKey: canonicalSearch });
      if (canonicalSearch !== location.search) {
        navigate(`/matches${canonicalSearch}`, { replace: true });
      }
    });
    return () => {
      active = false;
    };
  }, [location.search, navigate, params.page, params.sort]);

  useEffect(() => {
    if (message && location.state) {
      navigate(`/matches${location.search}`, { replace: true });
    }
  }, [location.search, location.state, message, navigate]);

  return (
    <MatchHistoryContent
      matches={currentHistory?.matches ?? []}
      pagination={currentHistory?.pagination ?? null}
      requestedSort={params.sort}
      loading={!currentHistory}
      query={query}
      message={message}
      onDismissMessage={() => setMessage("")}
      onQueryChange={setQuery}
      onPageChange={(page) => navigate(`/matches${matchHistorySearch(page, params.sort)}`)}
      onSortChange={(sort) => navigate(`/matches${sortChangeSearch(sort)}`)}
    />
  );
}

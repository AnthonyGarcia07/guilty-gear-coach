import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Match } from "../types";

export function MatchHistory() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    api.listMatches().then(setMatches);
  }, []);

  const filtered = useMemo(() => matches.filter((match) => `${match.player_character} ${match.opponent_character} ${match.rank_floor} ${match.mistake_tags.join(" ")}`.toLowerCase().includes(query.toLowerCase())), [matches, query]);

  return (
    <section className="page-stack">
      <div className="page-header">
        <div><span className="eyebrow">Review lab</span><h1>Match History</h1></div>
        <Link className="primary-button" to="/matches/new">Add Match</Link>
      </div>
      <input className="search-input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter by character, floor, or tag" />
      <div className="match-list large">{filtered.map((match) => <Link to={`/matches/${match.id}`} className="match-row" key={match.id}><span className={match.result}>{match.result}</span><strong>{match.player_character} vs {match.opponent_character}</strong><small>{match.rank_floor || "Unranked"} · {match.played_on}</small><small>{match.reason_for_loss || match.strength_tags.join(", ") || "Open notes"}</small></Link>)}</div>
    </section>
  );
}

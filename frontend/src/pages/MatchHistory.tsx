import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Match } from "../types";

export function MatchHistory() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [query, setQuery] = useState("");
  const location = useLocation();
  const navigate = useNavigate();
  const [message, setMessage] = useState(() => typeof location.state === "object" && location.state && "message" in location.state ? String(location.state.message) : "");

  useEffect(() => {
    api.listMatches().then(setMatches);
  }, []);

  useEffect(() => {
    if (message && location.state) {
      navigate("/matches", { replace: true });
    }
  }, [location.state, message, navigate]);

  const filtered = useMemo(() => matches.filter((match) => `${match.player_character} ${match.opponent_character} ${match.rank_floor} ${match.mistake_tags.join(" ")}`.toLowerCase().includes(query.toLowerCase())), [matches, query]);

  return (
    <section className="page-stack">
      <div className="page-header">
        <div><span className="eyebrow">Review lab</span><h1>Match History</h1></div>
        <Link className="primary-button" to="/matches/new">Add Match</Link>
      </div>
      {message && <p className="form-success" role="status">{message}<button type="button" onClick={() => setMessage("")}>Dismiss</button></p>}
      <input className="search-input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter by character, rank, or tag" />
      <div className="match-list large">{filtered.map((match) => <Link to={`/matches/${match.id}`} className="match-row" key={match.id}><span className={match.result}>{match.result}</span><strong>{match.player_character} vs {match.opponent_character}</strong><small>{match.rank_floor || "Unranked"} · {match.played_on}</small><small>{match.reason_for_loss || match.strength_tags.join(", ") || "Open notes"}</small></Link>)}</div>
    </section>
  );
}

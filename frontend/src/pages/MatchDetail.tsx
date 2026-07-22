import { Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { MatchForm } from "../components/MatchForm";
import { submitMatchUpdate } from "./matchSubmit";
import type { Match, MatchInput } from "../types";

export function MatchDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [match, setMatch] = useState<Match | null>(null);

  useEffect(() => {
    if (id) api.getMatch(id).then(setMatch);
  }, [id]);

  if (!match) return <div className="loading-panel">Loading match...</div>;

  return (
    <section className="page-stack">
      <div className="page-header">
        <div><span className={match.result}>{match.result}</span><h1>{match.player_character} vs {match.opponent_character}</h1></div>
        <button className="danger-button" onClick={async () => { await api.deleteMatch(match.id); navigate("/matches"); }}><Trash2 size={18} /> Delete</button>
      </div>
      <div className="detail-grid">
        <article><span>Date</span><strong>{match.played_on}</strong></article>
        <article><span>Rank</span><strong>{match.rank_floor || "Not logged"}</strong></article>
        <article><span>Duration</span><strong>{match.duration_seconds ? `${match.duration_seconds}s` : "Not logged"}</strong></article>
      </div>
      <section className="panel">
        <h2>Edit match notes</h2>
        <MatchForm initial={match} submitLabel="Update match" onSubmit={async (payload: MatchInput) => {
          await submitMatchUpdate(match.id, payload, api, navigate);
        }} />
      </section>
    </section>
  );
}

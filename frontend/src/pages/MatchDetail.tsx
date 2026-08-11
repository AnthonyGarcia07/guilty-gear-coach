import { Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { MatchForm } from "../components/MatchForm";
import { ReplayMetadataSection } from "../components/ReplayMetadataSection";
import { submitMatchUpdate } from "./matchSubmit";
import type { Match, MatchInput } from "../types";
import { getMatchHistoryReturnFromState } from "../utils/matchHistoryReturn";

export function shouldRenderMatchForRoute(match: Match | null, routeMatchId: string | undefined) {
  return Boolean(match && routeMatchId && match.id === Number(routeMatchId));
}

export function MatchDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [match, setMatch] = useState<Match | null>(null);
  const returnTo = getMatchHistoryReturnFromState(location.state);

  useEffect(() => {
    if (!id) return;
    let active = true;
    setMatch(null);
    api.getMatch(id).then((loadedMatch) => {
      if (active) setMatch(loadedMatch);
    });
    return () => {
      active = false;
    };
  }, [id]);

  const routeMatch = shouldRenderMatchForRoute(match, id) ? match : null;

  if (!routeMatch) return <div className="loading-panel">Loading match...</div>;

  return (
    <section className="page-stack">
      <div className="page-header">
        <div><span className={routeMatch.result}>{routeMatch.result}</span><h1>{routeMatch.player_character} vs {routeMatch.opponent_character}</h1></div>
        <button className="danger-button" onClick={async () => { await api.deleteMatch(routeMatch.id); navigate("/matches"); }}><Trash2 size={18} /> Delete</button>
      </div>
      <div className="detail-grid">
        <article><span>Date</span><strong>{routeMatch.played_on}</strong></article>
        <article><span>Rank</span><strong>{routeMatch.rank_floor || "Not logged"}</strong></article>
        <article><span>Duration</span><strong>{routeMatch.duration_seconds ? `${routeMatch.duration_seconds}s` : "Not logged"}</strong></article>
      </div>
      <section className="panel">
        <h2>Edit match notes</h2>
        <MatchForm key={routeMatch.id} initial={routeMatch} submitLabel="Update match" onSubmit={async (payload: MatchInput) => {
          await submitMatchUpdate(routeMatch.id, payload, api, navigate, returnTo);
        }} />
      </section>
      <ReplayMetadataSection matchId={routeMatch.id} />
    </section>
  );
}

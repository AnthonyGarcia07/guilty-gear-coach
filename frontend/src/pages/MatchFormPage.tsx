import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { MatchForm } from "../components/MatchForm";
import { submitNewMatch } from "./matchSubmit";
import type { MatchInput } from "../types";

export function MatchFormPage() {
  const navigate = useNavigate();
  return (
    <section className="page-stack">
      <div className="page-header"><div><span className="eyebrow">Manual analysis</span><h1>Add Match</h1></div></div>
      <section className="panel">
        <MatchForm submitLabel="Save match" onSubmit={async (payload: MatchInput) => {
          await submitNewMatch(payload, api, navigate);
        }} />
      </section>
    </section>
  );
}

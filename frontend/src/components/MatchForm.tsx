import { useState } from "react";
import type { Match, MatchInput, Result } from "../types";

const characters = [
  "Sol Badguy", "Ky Kiske", "May", "Axl Low", "Chipp Zanuff", "Potemkin", "Faust", "Millia Rage",
  "Zato-1", "Ramlethal Valentine", "Leo Whitefang", "Nagoriyuki", "Giovanna", "Anji Mito", "I-No",
  "Goldlewis Dickinson", "Jack-O", "Happy Chaos", "Baiken", "Testament", "Bridget", "Sin Kiske",
  "Bedman?", "Asuka R#", "Johnny", "Elphelt Valentine", "A.B.A", "Slayer", "Dizzy", "Venom", "Unika"
];

const mistakePresets = ["corner escape", "anti-air", "meter spend", "burst timing", "dropped conversion", "predictable okizeme"];
const strengthPresets = ["round start", "strike/throw", "whiff punish", "resource control", "corner pressure", "defense"];

const blankMatch: MatchInput = {
  player_character: "Sol Badguy",
  opponent_character: "Ky Kiske",
  result: "win",
  played_on: new Date().toISOString().slice(0, 10),
  rank_floor: "",
  duration_seconds: 120,
  notes: "",
  mistake_tags: [],
  strength_tags: [],
  reason_for_loss: "",
  practice_next: "",
  replay_filename: ""
};

function tagString(tags: string[]) {
  return tags.join(", ");
}

function parseTags(value: string) {
  return value.split(",").map((tag) => tag.trim()).filter(Boolean);
}

export function MatchForm({ initial, onSubmit, submitLabel }: { initial?: Match; onSubmit: (payload: MatchInput) => Promise<void>; submitLabel: string }) {
  const [form, setForm] = useState<MatchInput>(initial ? {
    player_character: initial.player_character,
    opponent_character: initial.opponent_character,
    result: initial.result,
    played_on: initial.played_on,
    rank_floor: initial.rank_floor ?? "",
    duration_seconds: initial.duration_seconds ?? 120,
    notes: initial.notes ?? "",
    mistake_tags: initial.mistake_tags,
    strength_tags: initial.strength_tags,
    reason_for_loss: initial.reason_for_loss ?? "",
    practice_next: initial.practice_next ?? "",
    replay_filename: initial.replay_filename ?? ""
  } : blankMatch);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const setField = <K extends keyof MatchInput>(field: K, value: MatchInput[K]) => setForm((current) => ({ ...current, [field]: value }));
  const toggleTag = (field: "mistake_tags" | "strength_tags", tag: string) => {
    setForm((current) => ({
      ...current,
      [field]: current[field].includes(tag) ? current[field].filter((item) => item !== tag) : [...current[field], tag]
    }));
  };

  return (
    <form className="form-grid" onSubmit={async (event) => {
      event.preventDefault();
      setSaving(true);
      setError("");
      try {
        await onSubmit(form);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not save match");
      } finally {
        setSaving(false);
      }
    }}>
      {error && <p className="form-error">{error}</p>}
      <label>Player character<select value={form.player_character} onChange={(event) => setField("player_character", event.target.value)}>{characters.map((character) => <option key={character}>{character}</option>)}</select></label>
      <label>Opponent character<select value={form.opponent_character} onChange={(event) => setField("opponent_character", event.target.value)}>{characters.map((character) => <option key={character}>{character}</option>)}</select></label>
      <label>Result<select value={form.result} onChange={(event) => setField("result", event.target.value as Result)}><option value="win">Win</option><option value="loss">Loss</option></select></label>
      <label>Date<input type="date" value={form.played_on} onChange={(event) => setField("played_on", event.target.value)} /></label>
      <label>Rank / floor<input value={form.rank_floor ?? ""} onChange={(event) => setField("rank_floor", event.target.value)} placeholder="Floor 10, Celestial, Park set" /></label>
      <label>Duration seconds<input type="number" min={1} value={form.duration_seconds ?? ""} onChange={(event) => setField("duration_seconds", Number(event.target.value))} /></label>
      <label className="wide">Mistake tags<input value={tagString(form.mistake_tags)} onChange={(event) => setField("mistake_tags", parseTags(event.target.value))} placeholder="anti-air, burst timing" /></label>
      <div className="tag-row wide">{mistakePresets.map((tag) => <button type="button" className={form.mistake_tags.includes(tag) ? "chip selected" : "chip"} key={tag} onClick={() => toggleTag("mistake_tags", tag)}>{tag}</button>)}</div>
      <label className="wide">Strength tags<input value={tagString(form.strength_tags)} onChange={(event) => setField("strength_tags", parseTags(event.target.value))} placeholder="corner pressure, whiff punish" /></label>
      <div className="tag-row wide">{strengthPresets.map((tag) => <button type="button" className={form.strength_tags.includes(tag) ? "chip selected" : "chip"} key={tag} onClick={() => toggleTag("strength_tags", tag)}>{tag}</button>)}</div>
      <label className="wide">Reason for loss<input value={form.reason_for_loss ?? ""} onChange={(event) => setField("reason_for_loss", event.target.value)} placeholder="Lost neutral after backing into corner" /></label>
      <label className="wide">Thing to practice next<textarea value={form.practice_next ?? ""} onChange={(event) => setField("practice_next", event.target.value)} placeholder="Lab anti-air conversion after 6P counter hit" /></label>
      <label className="wide">Notes<textarea value={form.notes ?? ""} onChange={(event) => setField("notes", event.target.value)} placeholder="What happened in the set?" /></label>
      <label className="wide">Replay / video placeholder<input value={form.replay_filename ?? ""} onChange={(event) => setField("replay_filename", event.target.value)} placeholder="my-set-vs-ky.mp4 or replay-id" /></label>
      <button className="primary-button wide" disabled={saving}>{saving ? "Saving..." : submitLabel}</button>
    </form>
  );
}

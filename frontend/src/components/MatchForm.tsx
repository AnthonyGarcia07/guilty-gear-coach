import { useState } from "react";
import { normalizeUnknownError } from "../api/errors";
import { striveCharacters, striveRanks } from "../constants/match";
import type { Match, MatchInput, Result } from "../types";

const mistakePresets = ["corner escape", "anti-air", "meter spend", "burst timing", "dropped conversion", "predictable okizeme"];
const strengthPresets = ["round start", "strike/throw", "whiff punish", "resource control", "corner pressure", "defense"];
const minMatchDate = "2021-06-11";
const maxDurationSeconds = 1800;
const maxNotesLength = 2000;
const maxReasonLength = 160;
const maxPracticeLength = 1000;
const maxTagLength = 40;
const maxTags = 12;

type MatchFormState = Omit<MatchInput, "duration_seconds"> & {
  duration_seconds: string;
};

type FieldErrors = Partial<Record<keyof MatchInput, string>>;

const blankMatch: MatchFormState = {
  player_character: "Sol Badguy",
  opponent_character: "Ky Kiske",
  result: "win",
  played_on: new Date().toISOString().slice(0, 10),
  rank_floor: "Iron",
  duration_seconds: "120",
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

function todayString() {
  return new Date().toISOString().slice(0, 10);
}

function uniqueTrimmedTags(tags: string[]) {
  return Array.from(new Set(tags.map((tag) => tag.trim()).filter(Boolean)));
}

function normalizeRankForEdit(rank: string | null | undefined) {
  return rank && striveRanks.includes(rank as (typeof striveRanks)[number]) ? rank : "";
}

function sanitizeForm(form: MatchFormState): MatchInput {
  return {
    ...form,
    player_character: form.player_character.trim(),
    opponent_character: form.opponent_character.trim(),
    rank_floor: form.rank_floor?.trim() || null,
    duration_seconds: form.duration_seconds.trim() ? Number(form.duration_seconds) : null,
    notes: form.notes?.trim() || null,
    mistake_tags: uniqueTrimmedTags(form.mistake_tags),
    strength_tags: uniqueTrimmedTags(form.strength_tags),
    reason_for_loss: form.reason_for_loss?.trim() || null,
    practice_next: form.practice_next?.trim() || null,
    replay_filename: form.replay_filename?.trim() || null
  };
}

function validateForm(form: MatchFormState): FieldErrors {
  const errors: FieldErrors = {};
  const today = todayString();

  if (!striveCharacters.includes(form.player_character as (typeof striveCharacters)[number])) errors.player_character = "Select a supported Guilty Gear Strive character.";
  if (!striveCharacters.includes(form.opponent_character as (typeof striveCharacters)[number])) errors.opponent_character = "Select a supported Guilty Gear Strive character.";
  if (!form.played_on) errors.played_on = "Match date is required.";
  else if (form.played_on < minMatchDate) errors.played_on = "Match date cannot be before June 11, 2021.";
  else if (form.played_on > today) errors.played_on = "Match date cannot be in the future.";
  if (!form.rank_floor?.trim()) errors.rank_floor = "Select a rank.";
  else if (!striveRanks.includes(form.rank_floor.trim() as (typeof striveRanks)[number])) errors.rank_floor = "Select a valid Guilty Gear Strive rank.";
  if (!form.duration_seconds.trim()) {
    errors.duration_seconds = "Match duration is required.";
  } else if (!Number.isFinite(Number(form.duration_seconds))) {
    errors.duration_seconds = "Match duration must be a number.";
  } else if (Number(form.duration_seconds) < 1) {
    errors.duration_seconds = "Match duration must be at least 1 second.";
  } else if (Number(form.duration_seconds) > maxDurationSeconds) {
    errors.duration_seconds = "Match duration must be 30 minutes or less.";
  }
  if ((form.notes?.trim().length ?? 0) > maxNotesLength) errors.notes = `Notes must be ${maxNotesLength} characters or fewer.`;
  if ((form.reason_for_loss?.trim().length ?? 0) > maxReasonLength) errors.reason_for_loss = `Reason for loss must be ${maxReasonLength} characters or fewer.`;
  if ((form.practice_next?.trim().length ?? 0) > maxPracticeLength) errors.practice_next = `Practice field must be ${maxPracticeLength} characters or fewer.`;
  if (form.mistake_tags.length > maxTags) errors.mistake_tags = `Use no more than ${maxTags} mistake tags.`;
  if (form.strength_tags.length > maxTags) errors.strength_tags = `Use no more than ${maxTags} strength tags.`;
  if (form.mistake_tags.some((tag) => tag.trim().length > maxTagLength)) errors.mistake_tags = `Mistake tags must be ${maxTagLength} characters or fewer.`;
  if (form.strength_tags.some((tag) => tag.trim().length > maxTagLength)) errors.strength_tags = `Strength tags must be ${maxTagLength} characters or fewer.`;

  return errors;
}

function characterOptions(initial?: Match) {
  const extraValues = [initial?.player_character, initial?.opponent_character].filter((value): value is string => Boolean(value && !striveCharacters.includes(value as (typeof striveCharacters)[number])));
  return [...striveCharacters, ...extraValues];
}

export function MatchForm({ initial, onSubmit, submitLabel }: { initial?: Match; onSubmit: (payload: MatchInput) => Promise<void>; submitLabel: string }) {
  const [form, setForm] = useState<MatchFormState>(initial ? {
    player_character: initial.player_character,
    opponent_character: initial.opponent_character,
    result: initial.result,
    played_on: initial.played_on,
    rank_floor: normalizeRankForEdit(initial.rank_floor),
    duration_seconds: initial.duration_seconds?.toString() ?? "120",
    notes: initial.notes ?? "",
    mistake_tags: initial.mistake_tags,
    strength_tags: initial.strength_tags,
    reason_for_loss: initial.reason_for_loss ?? "",
    practice_next: initial.practice_next ?? "",
    replay_filename: initial.replay_filename ?? ""
  } : blankMatch);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const options = characterOptions(initial);

  const setField = <K extends keyof MatchFormState>(field: K, value: MatchFormState[K]) => setForm((current) => ({ ...current, [field]: value }));
  const toggleTag = (field: "mistake_tags" | "strength_tags", tag: string) => {
    setForm((current) => ({
      ...current,
      [field]: current[field].includes(tag) ? current[field].filter((item) => item !== tag) : [...current[field], tag]
    }));
  };

  return (
    <form className="form-grid" noValidate onSubmit={async (event) => {
      event.preventDefault();
      setSaving(true);
      setError("");
      const errors = validateForm(form);
      setFieldErrors(errors);
      if (Object.keys(errors).length > 0) {
        setSaving(false);
        return;
      }
      try {
        await onSubmit(sanitizeForm(form));
      } catch (err) {
        const normalized = normalizeUnknownError(err, "Unable to update match.");
        setFieldErrors((current) => ({ ...current, ...normalized.fieldErrors }));
        setError(normalized.message);
      } finally {
        setSaving(false);
      }
    }}>
      {error && <p className="form-error">{error}</p>}
      <label>Player character<select value={form.player_character} onChange={(event) => setField("player_character", event.target.value)}>{options.map((character) => <option key={character}>{character}</option>)}</select>{fieldErrors.player_character && <span className="field-error">{fieldErrors.player_character}</span>}</label>
      <label>Opponent character<select value={form.opponent_character} onChange={(event) => setField("opponent_character", event.target.value)}>{options.map((character) => <option key={character}>{character}</option>)}</select>{fieldErrors.opponent_character && <span className="field-error">{fieldErrors.opponent_character}</span>}</label>
      <label>Result<select value={form.result} onChange={(event) => setField("result", event.target.value as Result)}><option value="win">Win</option><option value="loss">Loss</option></select></label>
      <label>Date<input type="date" value={form.played_on} onChange={(event) => setField("played_on", event.target.value)} />{fieldErrors.played_on && <span className="field-error">{fieldErrors.played_on}</span>}</label>
      <label>Rank<select value={form.rank_floor ?? ""} onChange={(event) => setField("rank_floor", event.target.value)}><option value="">Select rank</option>{striveRanks.map((rank) => <option key={rank} value={rank}>{rank}</option>)}</select>{initial?.rank_floor && !striveRanks.includes(initial.rank_floor as (typeof striveRanks)[number]) && !form.rank_floor && <span className="field-hint">Current legacy rank: {initial.rank_floor}. Select a new rank before saving.</span>}{fieldErrors.rank_floor && <span className="field-error">{fieldErrors.rank_floor}</span>}</label>
      <label>Duration seconds<input type="number" min={1} max={maxDurationSeconds} value={form.duration_seconds} onChange={(event) => setField("duration_seconds", event.target.value)} />{fieldErrors.duration_seconds && <span className="field-error">{fieldErrors.duration_seconds}</span>}</label>
      <label className="wide">Mistake tags<input value={tagString(form.mistake_tags)} onChange={(event) => setField("mistake_tags", parseTags(event.target.value))} placeholder="anti-air, burst timing" />{fieldErrors.mistake_tags && <span className="field-error">{fieldErrors.mistake_tags}</span>}</label>
      <div className="tag-row wide">{mistakePresets.map((tag) => <button type="button" className={form.mistake_tags.includes(tag) ? "chip selected" : "chip"} key={tag} onClick={() => toggleTag("mistake_tags", tag)}>{tag}</button>)}</div>
      <label className="wide">Strength tags<input value={tagString(form.strength_tags)} onChange={(event) => setField("strength_tags", parseTags(event.target.value))} placeholder="corner pressure, whiff punish" />{fieldErrors.strength_tags && <span className="field-error">{fieldErrors.strength_tags}</span>}</label>
      <div className="tag-row wide">{strengthPresets.map((tag) => <button type="button" className={form.strength_tags.includes(tag) ? "chip selected" : "chip"} key={tag} onClick={() => toggleTag("strength_tags", tag)}>{tag}</button>)}</div>
      <label className="wide">Reason for loss<input maxLength={maxReasonLength} value={form.reason_for_loss ?? ""} onChange={(event) => setField("reason_for_loss", event.target.value)} placeholder="Lost neutral after backing into corner" />{fieldErrors.reason_for_loss && <span className="field-error">{fieldErrors.reason_for_loss}</span>}</label>
      <label className="wide">Thing to practice next<textarea maxLength={maxPracticeLength} value={form.practice_next ?? ""} onChange={(event) => setField("practice_next", event.target.value)} placeholder="Lab anti-air conversion after 6P counter hit" />{fieldErrors.practice_next && <span className="field-error">{fieldErrors.practice_next}</span>}</label>
      <label className="wide">Notes<textarea maxLength={maxNotesLength} value={form.notes ?? ""} onChange={(event) => setField("notes", event.target.value)} placeholder="What happened in the set?" />{fieldErrors.notes && <span className="field-error">{fieldErrors.notes}</span>}</label>
      <label className="wide">Replay / video placeholder<input value={form.replay_filename ?? ""} onChange={(event) => setField("replay_filename", event.target.value)} placeholder="my-set-vs-ky.mp4 or replay-id" /></label>
      <button className="primary-button wide" disabled={saving}>{saving ? "Saving..." : submitLabel}</button>
    </form>
  );
}

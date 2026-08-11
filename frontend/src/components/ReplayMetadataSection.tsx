import { useEffect, useState } from "react";
import { normalizeUnknownError } from "../api/errors";
import { api } from "../api/client";
import type { Replay, ReplayCreateInput, ReplaySourceType, ReplayUpdateInput } from "../types";

const maxFilenameLength = 255;
const replaySourceOptions: Array<{ value: ReplaySourceType; label: string }> = [
  { value: "replay_file", label: "Replay file" },
  { value: "video", label: "Video" },
  { value: "external_reference", label: "External reference" }
];

type ReplayFormState = {
  source_type: ReplaySourceType;
  original_filename: string;
};

type ReplayApi = {
  listReplays: (matchId: number) => Promise<Replay[]>;
  createReplay: (matchId: number, payload: ReplayCreateInput) => Promise<Replay>;
  updateReplay: (matchId: number, replayId: number, payload: ReplayUpdateInput) => Promise<Replay>;
  deleteReplay: (matchId: number, replayId: number) => Promise<void>;
};

const blankReplayForm: ReplayFormState = {
  source_type: "replay_file",
  original_filename: ""
};

export function sourceTypeLabel(sourceType: ReplaySourceType) {
  return replaySourceOptions.find((option) => option.value === sourceType)?.label ?? sourceType;
}

export function validateReplayForm(form: ReplayFormState) {
  if (!replaySourceOptions.some((option) => option.value === form.source_type)) {
    return "Select a supported replay source type.";
  }
  if (form.original_filename.trim().length > maxFilenameLength) {
    return `Original filename must be ${maxFilenameLength} characters or fewer.`;
  }
  return "";
}

export function replayPayloadFromForm(form: ReplayFormState): ReplayCreateInput {
  return {
    source_type: form.source_type,
    original_filename: form.original_filename.trim() || null
  };
}

export function ReplayMetadataSection({ matchId, replayApi = api }: { matchId: number; replayApi?: ReplayApi }) {
  const [replays, setReplays] = useState<Replay[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<ReplayFormState>(blankReplayForm);
  const [fieldError, setFieldError] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<ReplayFormState>(blankReplayForm);
  const [editFieldError, setEditFieldError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    setSuccess("");
    setReplays([]);
    setEditingId(null);
    replayApi.listReplays(matchId).then((items) => {
      if (!active) return;
      setReplays(items);
    }).catch((err) => {
      if (!active) return;
      setError(normalizeUnknownError(err, "Unable to load replay metadata.").message);
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => {
      active = false;
    };
  }, [matchId, replayApi]);

  async function handleCreate() {
    const validation = validateReplayForm(form);
    setFieldError(validation);
    setError("");
    setSuccess("");
    if (validation) return;

    setSaving(true);
    try {
      const replay = await replayApi.createReplay(matchId, replayPayloadFromForm(form));
      setReplays((current) => [...current, replay]);
      setForm(blankReplayForm);
      setSuccess("Replay metadata added.");
    } catch (err) {
      setError(normalizeUnknownError(err, "Unable to add replay metadata.").message);
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdate(replayId: number) {
    const validation = validateReplayForm(editForm);
    setEditFieldError(validation);
    setError("");
    setSuccess("");
    if (validation) return;

    setSaving(true);
    try {
      const replay = await replayApi.updateReplay(matchId, replayId, replayPayloadFromForm(editForm));
      setReplays((current) => current.map((item) => (item.id === replay.id ? replay : item)));
      setEditingId(null);
      setSuccess("Replay metadata updated.");
    } catch (err) {
      setError(normalizeUnknownError(err, "Unable to update replay metadata.").message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(replayId: number) {
    const confirmed = window.confirm("Delete this replay metadata? The parent match will not be deleted.");
    if (!confirmed) return;
    setError("");
    setSuccess("");
    try {
      await replayApi.deleteReplay(matchId, replayId);
      setReplays((current) => current.filter((item) => item.id !== replayId));
      setSuccess("Replay metadata deleted.");
    } catch (err) {
      setError(normalizeUnknownError(err, "Unable to delete replay metadata.").message);
    }
  }

  function startEditing(replay: Replay) {
    setEditingId(replay.id);
    setEditFieldError("");
    setEditForm({
      source_type: replay.source_type,
      original_filename: replay.original_filename ?? ""
    });
  }

  return (
    <ReplayMetadataContent
      replays={replays}
      loading={loading}
      error={error}
      success={success}
      form={form}
      fieldError={fieldError}
      editForm={editForm}
      editFieldError={editFieldError}
      editingId={editingId}
      saving={saving}
      onFormChange={setForm}
      onEditFormChange={setEditForm}
      onCreate={handleCreate}
      onStartEdit={startEditing}
      onCancelEdit={() => setEditingId(null)}
      onUpdate={handleUpdate}
      onDelete={handleDelete}
    />
  );
}

export function ReplayMetadataContent({
  replays,
  loading,
  error,
  success,
  form,
  fieldError,
  editForm,
  editFieldError,
  editingId,
  saving,
  onFormChange,
  onEditFormChange,
  onCreate,
  onStartEdit,
  onCancelEdit,
  onUpdate,
  onDelete
}: {
  replays: Replay[];
  loading: boolean;
  error: string;
  success: string;
  form: ReplayFormState;
  fieldError: string;
  editForm: ReplayFormState;
  editFieldError: string;
  editingId: number | null;
  saving: boolean;
  onFormChange: (form: ReplayFormState) => void;
  onEditFormChange: (form: ReplayFormState) => void;
  onCreate: () => void;
  onStartEdit: (replay: Replay) => void;
  onCancelEdit: () => void;
  onUpdate: (replayId: number) => void;
  onDelete: (replayId: number) => void;
}) {
  return (
    <section className="panel replay-panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Replay metadata</span>
          <h2>Replay Sources</h2>
        </div>
        <p className="muted">Metadata only — no file is uploaded or analyzed in this phase.</p>
      </div>

      {error && <p className="form-error">{error}</p>}
      {success && <p className="form-success" role="status">{success}</p>}
      {loading && <p className="muted">Loading replay metadata...</p>}
      {!loading && replays.length === 0 && <p className="muted">No replay metadata attached to this set yet.</p>}

      {!loading && replays.length > 0 && (
        <div className="replay-list">
          {replays.map((replay) => (
            <article className="replay-card" key={replay.id}>
              {editingId === replay.id ? (
                <div className="replay-edit-grid">
                  <ReplayFields form={editForm} onChange={onEditFormChange} />
                  {editFieldError && <span className="field-error wide">{editFieldError}</span>}
                  <button className="primary-button" type="button" disabled={saving} onClick={() => onUpdate(replay.id)}>Save metadata</button>
                  <button className="ghost-button" type="button" disabled={saving} onClick={onCancelEdit}>Cancel</button>
                </div>
              ) : (
                <>
                  <div>
                    <strong>{sourceTypeLabel(replay.source_type)}</strong>
                    <p className="muted">{replay.original_filename || "No filename or reference saved"}</p>
                  </div>
                  <div className="replay-card-actions">
                    <button className="secondary-button" type="button" onClick={() => onStartEdit(replay)}>Edit</button>
                    <button className="danger-button" type="button" onClick={() => onDelete(replay.id)}>Delete</button>
                  </div>
                </>
              )}
            </article>
          ))}
        </div>
      )}

      <div className="replay-create-box">
        <h3>Add replay metadata</h3>
        <ReplayFields form={form} onChange={onFormChange} />
        <span className="field-hint wide">Metadata only — no file is uploaded in this phase.</span>
        {fieldError && <span className="field-error wide">{fieldError}</span>}
        <button className="primary-button wide" type="button" disabled={saving} onClick={onCreate}>{saving ? "Saving..." : "Add replay metadata"}</button>
      </div>
    </section>
  );
}

function ReplayFields({ form, onChange }: { form: ReplayFormState; onChange: (form: ReplayFormState) => void }) {
  return (
    <>
      <label>Source type<select value={form.source_type} onChange={(event) => onChange({ ...form, source_type: event.target.value as ReplaySourceType })}>{replaySourceOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
      <label>Original filename or reference<input maxLength={maxFilenameLength} value={form.original_filename} onChange={(event) => onChange({ ...form, original_filename: event.target.value })} placeholder="match-vs-sol-2026-08-09.rep" /></label>
    </>
  );
}

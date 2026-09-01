import { useEffect, useRef, useState } from "react";
import { normalizeUnknownError } from "../api/errors";
import { api, uploadReplayFileToStorage } from "../api/client";
import { ConfirmDialog } from "./ConfirmDialog";
import type {
  Replay,
  ReplayCreateInput,
  ReplayDownloadUrlResponse,
  ReplayInspectResponse,
  ReplayProcessingStatus,
  ReplaySourceType,
  ReplayUpdateInput,
  ReplayUploadConfirmResponse,
  ReplayUploadInitInput,
  ReplayUploadInitResponse,
  ReplayUploadStatus
} from "../types";

const maxFilenameLength = 255;
export const maxMp4UploadSizeBytes = 2 * 1024 * 1024 * 1024;
const replaySourceOptions: Array<{ value: ReplaySourceType; label: string }> = [
  { value: "replay_file", label: "Replay file" },
  { value: "video", label: "Video" },
  { value: "external_reference", label: "External reference" }
];

export const replayDeleteConfirmation = {
  title: "Delete replay?",
  message: "This will permanently delete this replay and its uploaded video. This action cannot be undone.",
  confirmLabel: "Delete Replay"
};

type ReplayFormState = {
  source_type: ReplaySourceType;
  original_filename: string;
};

type ReplayApi = {
  listReplays: (matchId: number) => Promise<Replay[]>;
  createReplay: (matchId: number, payload: ReplayCreateInput) => Promise<Replay>;
  updateReplay: (matchId: number, replayId: number, payload: ReplayUpdateInput) => Promise<Replay>;
  deleteReplay: (matchId: number, replayId: number) => Promise<void>;
  initializeReplayUpload: (matchId: number, payload: ReplayUploadInitInput) => Promise<ReplayUploadInitResponse>;
  confirmReplayUpload: (matchId: number, replayId: number) => Promise<ReplayUploadConfirmResponse>;
  getReplayDownloadUrl: (matchId: number, replayId: number) => Promise<ReplayDownloadUrlResponse>;
  inspectReplay: (matchId: number, replayId: number) => Promise<ReplayInspectResponse>;
  sampleReplayFrame: (matchId: number, replayId: number, timestampSeconds: number) => Promise<Blob>;
};

const blankReplayForm: ReplayFormState = {
  source_type: "replay_file",
  original_filename: ""
};

export function sourceTypeLabel(sourceType: ReplaySourceType) {
  return replaySourceOptions.find((option) => option.value === sourceType)?.label ?? sourceType;
}

export function uploadStatusLabel(status: ReplayUploadStatus) {
  const labels: Record<ReplayUploadStatus, string> = {
    metadata_only: "Metadata only",
    pending_upload: "Upload pending",
    uploaded: "Uploaded video"
  };
  return labels[status];
}

export function processingStatusLabel(status: ReplayProcessingStatus) {
  const labels: Record<ReplayProcessingStatus, string> = {
    not_processed: "Not inspected",
    processing: "Inspecting metadata",
    processed: "Metadata inspected",
    failed: "Inspection failed"
  };
  return labels[status];
}

export function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export function validateMp4File(file: Pick<File, "name" | "size" | "type"> | null) {
  if (!file) return "Select an MP4 file.";
  if (file.type !== "video/mp4") return "Replay video must be an MP4 file.";
  if (file.size <= 0) return "Replay video must be larger than 0 bytes.";
  if (file.size > maxMp4UploadSizeBytes) return `Replay video must be ${formatFileSize(maxMp4UploadSizeBytes)} or smaller.`;
  return "";
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

export function validateFrameTimestampInput(value: string, durationSeconds: number | null | undefined) {
  const trimmed = value.trim();
  if (!trimmed) return "Enter a timestamp in seconds.";
  const timestamp = Number(trimmed);
  if (!Number.isFinite(timestamp) || timestamp < 0) return "Timestamp must be a number greater than or equal to 0.";
  if (durationSeconds === null || durationSeconds === undefined) return "Inspect video metadata before sampling a frame.";
  if (timestamp >= durationSeconds) return "Timestamp must be before the end of the video.";
  return "";
}

export function replaceSampleFrameUrl({
  current,
  replayId,
  blob,
  createObjectURL,
  revokeObjectURL
}: {
  current: Record<number, string>;
  replayId: number;
  blob: Blob;
  createObjectURL: (blob: Blob) => string;
  revokeObjectURL: (url: string) => void;
}) {
  const previousUrl = current[replayId];
  if (previousUrl) revokeObjectURL(previousUrl);
  return { ...current, [replayId]: createObjectURL(blob) };
}

export function canSampleFrame(replay: Replay) {
  return (
    replay.upload_status === "uploaded" &&
    Boolean(replay.storage_key) &&
    replay.processing_status === "processed" &&
    replay.video_duration_seconds !== null &&
    replay.video_duration_seconds !== undefined
  );
}

export function replayPayloadFromForm(form: ReplayFormState): ReplayCreateInput {
  return {
    source_type: form.source_type,
    original_filename: form.original_filename.trim() || null
  };
}

export async function uploadMp4Replay({
  matchId,
  file,
  replayApi,
  putFile = uploadReplayFileToStorage
}: {
  matchId: number;
  file: File;
  replayApi: Pick<ReplayApi, "initializeReplayUpload" | "confirmReplayUpload">;
  putFile?: (uploadUrl: string, file: File) => Promise<void>;
}) {
  const initialized = await replayApi.initializeReplayUpload(matchId, {
    original_filename: file.name,
    content_type: "video/mp4",
    size_bytes: file.size
  });
  await putFile(initialized.upload_url, file);
  const confirmed = await replayApi.confirmReplayUpload(matchId, initialized.replay.id);
  return { initialized, confirmed };
}

export async function openReplayDownload({
  matchId,
  replayId,
  replayApi,
  openUrl
}: {
  matchId: number;
  replayId: number;
  replayApi: Pick<ReplayApi, "getReplayDownloadUrl">;
  openUrl: (url: string) => void | Window | null;
}) {
  const response = await replayApi.getReplayDownloadUrl(matchId, replayId);
  openUrl(response.download_url);
  return response;
}

export function ReplayMetadataSection({
  matchId,
  replayApi = api,
  putFile = uploadReplayFileToStorage,
  openUrl = (url: string) => window.open(url, "_blank", "noopener,noreferrer")
}: {
  matchId: number;
  replayApi?: ReplayApi;
  putFile?: (uploadUrl: string, file: File) => Promise<void>;
  openUrl?: (url: string) => void | Window | null;
}) {
  const [replays, setReplays] = useState<Replay[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [inspectingId, setInspectingId] = useState<number | null>(null);
  const [samplingId, setSamplingId] = useState<number | null>(null);
  const [sampleTimestamps, setSampleTimestamps] = useState<Record<number, string>>({});
  const [sampleErrors, setSampleErrors] = useState<Record<number, string>>({});
  const [sampleFrameUrls, setSampleFrameUrls] = useState<Record<number, string>>({});
  const sampleFrameUrlsRef = useRef<Record<number, string>>({});
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadFieldError, setUploadFieldError] = useState("");
  const [form, setForm] = useState<ReplayFormState>(blankReplayForm);
  const [fieldError, setFieldError] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [deleteReplayId, setDeleteReplayId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [editForm, setEditForm] = useState<ReplayFormState>(blankReplayForm);
  const [editFieldError, setEditFieldError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    setSuccess("");
    setReplays([]);
    setEditingId(null);
    setDeleteReplayId(null);
    setDeleting(false);
    setInspectingId(null);
    setSamplingId(null);
    setSampleTimestamps({});
    setSampleErrors({});
    updateSampleFrameUrls((current) => {
      Object.values(current).forEach((url) => URL.revokeObjectURL(url));
      return {};
    });
    setSelectedFile(null);
    setUploadFieldError("");
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

  useEffect(() => {
    return () => {
      Object.values(sampleFrameUrlsRef.current).forEach((url) => URL.revokeObjectURL(url));
    };
  }, []);

  function updateSampleFrameUrls(updater: (current: Record<number, string>) => Record<number, string>) {
    setSampleFrameUrls((current) => {
      const next = updater(current);
      sampleFrameUrlsRef.current = next;
      return next;
    });
  }

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
    setError("");
    setSuccess("");
    setDeleting(true);
    try {
      await replayApi.deleteReplay(matchId, replayId);
      setReplays((current) => current.filter((item) => item.id !== replayId));
      setDeleteReplayId(null);
      setSuccess("Replay metadata deleted.");
    } catch (err) {
      setError(normalizeUnknownError(err, "Unable to delete replay metadata.").message);
      setDeleteReplayId(null);
    } finally {
      setDeleting(false);
    }
  }

  async function handleUpload() {
    const validation = validateMp4File(selectedFile);
    setUploadFieldError(validation);
    setError("");
    setSuccess("");
    if (validation || !selectedFile) return;

    setUploading(true);
    try {
      const { initialized, confirmed } = await uploadMp4Replay({ matchId, file: selectedFile, replayApi, putFile });
      setReplays((current) => [...current, initialized.replay].map((item) => (item.id === confirmed.replay.id ? confirmed.replay : item)));
      setSelectedFile(null);
      setSuccess("MP4 replay uploaded.");
    } catch (err) {
      setError(normalizeUnknownError(err, "Unable to upload MP4 replay.").message);
    } finally {
      setUploading(false);
    }
  }

  async function handleDownload(replayId: number) {
    setError("");
    setSuccess("");
    try {
      await openReplayDownload({ matchId, replayId, replayApi, openUrl });
    } catch (err) {
      setError(normalizeUnknownError(err, "Unable to open replay video.").message);
    }
  }

  async function handleInspect(replayId: number) {
    setError("");
    setSuccess("");
    setInspectingId(replayId);
    try {
      const response = await replayApi.inspectReplay(matchId, replayId);
      setReplays((current) => current.map((item) => (item.id === response.replay.id ? response.replay : item)));
      setSuccess("Video metadata inspected.");
    } catch (err) {
      const normalized = normalizeUnknownError(err, "Unable to inspect video metadata.");
      setError(normalized.message);
    } finally {
      setInspectingId(null);
    }
  }

  async function handleSampleFrame(replay: Replay) {
    const timestampInput = sampleTimestamps[replay.id] ?? "";
    const validation = validateFrameTimestampInput(timestampInput, replay.video_duration_seconds);
    setSampleErrors((current) => ({ ...current, [replay.id]: validation }));
    setError("");
    setSuccess("");
    if (validation) return;

    setSamplingId(replay.id);
    try {
      const blob = await replayApi.sampleReplayFrame(matchId, replay.id, Number(timestampInput.trim()));
      updateSampleFrameUrls((current) => replaceSampleFrameUrl({
        current,
        replayId: replay.id,
        blob,
        createObjectURL: URL.createObjectURL,
        revokeObjectURL: URL.revokeObjectURL
      }));
    } catch (err) {
      setSampleErrors((current) => ({ ...current, [replay.id]: normalizeUnknownError(err, "Unable to sample replay frame.").message }));
    } finally {
      setSamplingId(null);
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
    <>
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
        deleting={deleting}
        uploading={uploading}
        inspectingId={inspectingId}
        samplingId={samplingId}
        sampleTimestamps={sampleTimestamps}
        sampleErrors={sampleErrors}
        sampleFrameUrls={sampleFrameUrls}
        selectedFile={selectedFile}
        uploadFieldError={uploadFieldError}
        onFormChange={setForm}
        onEditFormChange={setEditForm}
        onFileChange={(file) => {
          setSelectedFile(file);
          setUploadFieldError("");
        }}
        onUpload={handleUpload}
        onCreate={handleCreate}
        onStartEdit={startEditing}
        onCancelEdit={() => setEditingId(null)}
        onUpdate={handleUpdate}
        onRequestDelete={setDeleteReplayId}
        onDownload={handleDownload}
        onInspect={handleInspect}
        onSampleTimestampChange={(replayId, value) => {
          setSampleTimestamps((current) => ({ ...current, [replayId]: value }));
          setSampleErrors((current) => ({ ...current, [replayId]: "" }));
        }}
        onSampleFrame={handleSampleFrame}
      />
      {deleteReplayId !== null && (
        <ConfirmDialog
          title={replayDeleteConfirmation.title}
          message={replayDeleteConfirmation.message}
          confirmLabel={replayDeleteConfirmation.confirmLabel}
          confirming={deleting}
          onCancel={() => setDeleteReplayId(null)}
          onConfirm={() => handleDelete(deleteReplayId)}
        />
      )}
    </>
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
  deleting,
  uploading,
  inspectingId,
  samplingId,
  sampleTimestamps,
  sampleErrors,
  sampleFrameUrls,
  selectedFile,
  uploadFieldError,
  onFormChange,
  onEditFormChange,
  onFileChange,
  onUpload,
  onCreate,
  onStartEdit,
  onCancelEdit,
  onUpdate,
  onRequestDelete,
  onDownload,
  onInspect,
  onSampleTimestampChange,
  onSampleFrame
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
  deleting: boolean;
  uploading: boolean;
  inspectingId: number | null;
  samplingId: number | null;
  sampleTimestamps: Record<number, string>;
  sampleErrors: Record<number, string>;
  sampleFrameUrls: Record<number, string>;
  selectedFile: Pick<File, "name" | "size" | "type"> | null;
  uploadFieldError: string;
  onFormChange: (form: ReplayFormState) => void;
  onEditFormChange: (form: ReplayFormState) => void;
  onFileChange: (file: File | null) => void;
  onUpload: () => void;
  onCreate: () => void;
  onStartEdit: (replay: Replay) => void;
  onCancelEdit: () => void;
  onUpdate: (replayId: number) => void;
  onRequestDelete: (replayId: number) => void;
  onDownload: (replayId: number) => void;
  onInspect: (replayId: number) => void;
  onSampleTimestampChange: (replayId: number, value: string) => void;
  onSampleFrame: (replay: Replay) => void;
}) {
  return (
    <section className="panel replay-panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Replay metadata</span>
          <h2>Replay Sources</h2>
        </div>
        <p className="muted">Attach metadata or upload an MP4 video. Videos are stored privately and are not analyzed yet.</p>
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
                    <p className="muted">{uploadStatusLabel(replay.upload_status)}{replay.size_bytes ? ` · ${formatFileSize(replay.size_bytes)}` : ""}</p>
                    <p className="muted">{processingStatusLabel(replay.processing_status)}</p>
                    {replay.processing_status === "processed" && (
                      <p className="muted">
                        {replay.video_duration_seconds !== null && replay.video_duration_seconds !== undefined ? `Duration: ${formatDuration(replay.video_duration_seconds)} · ` : ""}
                        {replay.video_width && replay.video_height ? `Resolution: ${replay.video_width}×${replay.video_height} · ` : ""}
                        {replay.video_fps ? `FPS: ${replay.video_fps} · ` : ""}
                        {replay.video_codec ? `Codec: ${replay.video_codec}` : ""}
                      </p>
                    )}
                    {replay.processing_status === "failed" && replay.processing_error && <p className="form-error">{replay.processing_error}</p>}
                    {canSampleFrame(replay) && (
                      <div className="frame-sample-box">
                        <label>
                          Timestamp seconds
                          <input
                            inputMode="decimal"
                            placeholder="10"
                            value={sampleTimestamps[replay.id] ?? ""}
                            onChange={(event) => onSampleTimestampChange(replay.id, event.target.value)}
                          />
                        </label>
                        <button className="secondary-button" type="button" disabled={samplingId === replay.id} onClick={() => onSampleFrame(replay)}>
                          {samplingId === replay.id ? "Sampling..." : "Sample frame"}
                        </button>
                        {sampleErrors[replay.id] && <span className="field-error wide">{sampleErrors[replay.id]}</span>}
                        {sampleFrameUrls[replay.id] && <img className="sampled-frame" src={sampleFrameUrls[replay.id]} alt={`Sampled frame from ${replay.original_filename || "replay"}`} />}
                      </div>
                    )}
                  </div>
                  <div className="replay-card-actions">
                    {replay.upload_status === "uploaded" && replay.storage_key && <button className="secondary-button" type="button" onClick={() => onDownload(replay.id)}>Download video</button>}
                    {replay.upload_status === "uploaded" && replay.storage_key && <button className="secondary-button" type="button" disabled={inspectingId === replay.id} onClick={() => onInspect(replay.id)}>{inspectingId === replay.id ? "Inspecting..." : "Inspect metadata"}</button>}
                    <button className="secondary-button" type="button" onClick={() => onStartEdit(replay)}>Edit</button>
                    <button className="danger-button" type="button" disabled={deleting} onClick={() => onRequestDelete(replay.id)}>Delete</button>
                  </div>
                </>
              )}
            </article>
          ))}
        </div>
      )}

      <div className="replay-create-box">
        <h3>Upload MP4 replay video</h3>
        <label className="wide">MP4 file<input type="file" accept="video/mp4,.mp4" onChange={(event) => onFileChange(event.target.files?.[0] ?? null)} /></label>
        {selectedFile && <span className="field-hint wide">Selected: {selectedFile.name} · {formatFileSize(selectedFile.size)}</span>}
        <span className="field-hint wide">The MP4 goes directly to private object storage. Guilty Gear Coach does not analyze video in this phase.</span>
        {uploadFieldError && <span className="field-error wide">{uploadFieldError}</span>}
        <button className="primary-button wide" type="button" disabled={uploading} onClick={onUpload}>{uploading ? "Uploading..." : "Upload MP4"}</button>
      </div>

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

export function formatDuration(seconds: number) {
  const rounded = Math.round(seconds);
  const minutes = Math.floor(rounded / 60);
  const remainingSeconds = rounded % 60;
  return minutes > 0 ? `${minutes}m ${remainingSeconds}s` : `${remainingSeconds}s`;
}

function ReplayFields({ form, onChange }: { form: ReplayFormState; onChange: (form: ReplayFormState) => void }) {
  return (
    <>
      <label>Source type<select value={form.source_type} onChange={(event) => onChange({ ...form, source_type: event.target.value as ReplaySourceType })}>{replaySourceOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
      <label>Original filename or reference<input maxLength={maxFilenameLength} value={form.original_filename} onChange={(event) => onChange({ ...form, original_filename: event.target.value })} placeholder="match-vs-sol-2026-08-09.rep" /></label>
    </>
  );
}

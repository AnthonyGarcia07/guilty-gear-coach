import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import {
  ReplayMetadataContent,
  formatDuration,
  formatFileSize,
  openReplayDownload,
  processingStatusLabel,
  replayDeleteConfirmation,
  replayPayloadFromForm,
  sourceTypeLabel,
  uploadMp4Replay,
  uploadStatusLabel,
  validateMp4File,
  validateReplayForm
} from "./ReplayMetadataSection";
import type { Replay, ReplaySourceType } from "../types";

function makeReplay(overrides: Partial<Replay> = {}): Replay {
  return {
    id: 1,
    match_id: 7,
    source_type: "replay_file",
    original_filename: "match-vs-sol.rep",
    storage_key: null,
    upload_status: "metadata_only",
    content_type: null,
    size_bytes: null,
    uploaded_at: null,
    processing_status: "not_processed",
    processing_error: null,
    metadata_inspected_at: null,
    video_duration_seconds: null,
    video_width: null,
    video_height: null,
    video_fps: null,
    video_codec: null,
    created_at: "2026-08-09T12:00:00Z",
    updated_at: "2026-08-09T12:00:00Z",
    ...overrides
  };
}

function renderContent(overrides: Partial<Parameters<typeof ReplayMetadataContent>[0]> = {}) {
  const props: Parameters<typeof ReplayMetadataContent>[0] = {
    replays: [],
    loading: false,
    error: "",
    success: "",
    form: { source_type: "replay_file", original_filename: "" },
    fieldError: "",
    editForm: { source_type: "replay_file", original_filename: "" },
    editFieldError: "",
    editingId: null,
    saving: false,
    uploading: false,
    selectedFile: null,
    uploadFieldError: "",
    onFormChange: vi.fn(),
    onEditFormChange: vi.fn(),
    onFileChange: vi.fn(),
    onUpload: vi.fn(),
    onCreate: vi.fn(),
    onStartEdit: vi.fn(),
    onCancelEdit: vi.fn(),
    onUpdate: vi.fn(),
    deleting: false,
    inspectingId: null,
    onRequestDelete: vi.fn(),
    onDownload: vi.fn(),
    onInspect: vi.fn(),
    ...overrides
  };

  return renderToStaticMarkup(<ReplayMetadataContent {...props} />);
}

describe("ReplayMetadataSection", () => {
  it("renders the empty state for a match with no replays", () => {
    const html = renderContent();

    expect(html).toContain("Replay Sources");
    expect(html).toContain("No replay metadata attached to this set yet.");
    expect(html).toContain("Attach metadata or upload an MP4 video.");
  });

  it("renders one replay with the correct source label", () => {
    const html = renderContent({ replays: [makeReplay()] });

    expect(html).toContain("Replay file");
    expect(html).toContain("match-vs-sol.rep");
  });

  it("renders multiple replays and source labels", () => {
    const html = renderContent({
      replays: [
        makeReplay({ id: 1, source_type: "replay_file", original_filename: "one.rep" }),
        makeReplay({ id: 2, source_type: "video", original_filename: "two.mp4", upload_status: "uploaded", storage_key: "users/1/matches/7/replays/two.mp4", size_bytes: 2048 }),
        makeReplay({ id: 3, source_type: "external_reference", original_filename: null })
      ]
    });

    expect(html).toContain("Replay file");
    expect(html).toContain("Video");
    expect(html).toContain("External reference");
    expect(html).toContain("No filename or reference saved");
    expect(html).toContain("Uploaded video");
    expect(html).toContain("2.0 KB");
    expect(html).toContain("Download video");
    expect(html).toContain("Inspect metadata");
  });

  it("builds create and update payloads with trimmed optional filenames", () => {
    expect(replayPayloadFromForm({ source_type: "video", original_filename: " set-3.mp4 " })).toEqual({
      source_type: "video",
      original_filename: "set-3.mp4"
    });
    expect(replayPayloadFromForm({ source_type: "external_reference", original_filename: "   " })).toEqual({
      source_type: "external_reference",
      original_filename: null
    });
  });

  it("validates filename length and invalid source type before submitting", () => {
    expect(validateReplayForm({ source_type: "video", original_filename: "x".repeat(256) })).toBe("Original filename must be 255 characters or fewer.");
    expect(validateReplayForm({ source_type: "screenshot" as ReplaySourceType, original_filename: "" })).toBe("Select a supported replay source type.");
    expect(validateReplayForm({ source_type: "replay_file", original_filename: "valid.rep" })).toBe("");
  });

  it("renders editing controls for the selected replay", () => {
    const html = renderContent({
      replays: [makeReplay({ id: 9, source_type: "video", original_filename: "before.mp4" })],
      editingId: 9,
      editForm: { source_type: "external_reference", original_filename: "after-reference" }
    });

    expect(html).toContain("Save metadata");
    expect(html).toContain("Cancel");
    expect(html).toContain("after-reference");
    expect(html).toContain("<option value=\"external_reference\" selected=\"\">External reference</option>");
  });

  it("shows success and error states without raw objects", () => {
    const html = renderContent({ error: "Unable to add replay metadata.", success: "Replay metadata added." });

    expect(html).toContain("Unable to add replay metadata.");
    expect(html).toContain("Replay metadata added.");
    expect(html).not.toContain("[object Object]");
  });

  it("uses destructive replay delete confirmation wording", () => {
    expect(replayDeleteConfirmation).toEqual({
      title: "Delete replay?",
      message: "This will permanently delete this replay and its uploaded video. This action cannot be undone.",
      confirmLabel: "Delete Replay"
    });
  });

  it("renders real MP4 upload UI without claiming gameplay analysis is available", () => {
    const html = renderContent({ replays: [makeReplay()] });

    expect(html).toContain("type=\"file\"");
    expect(html).toContain("accept=\"video/mp4,.mp4\"");
    expect(html).toContain("Upload MP4");
    expect(html).not.toContain("gameplay analysis is available");
    expect(html).not.toContain("Ready for analysis");
  });

  it("maps source type labels exactly", () => {
    expect(sourceTypeLabel("replay_file")).toBe("Replay file");
    expect(sourceTypeLabel("video")).toBe("Video");
    expect(sourceTypeLabel("external_reference")).toBe("External reference");
  });

  it("validates MP4 file selection before upload", () => {
    expect(validateMp4File(null)).toBe("Select an MP4 file.");
    expect(validateMp4File({ name: "set.webm", type: "video/webm", size: 100 })).toBe("Replay video must be an MP4 file.");
    expect(validateMp4File({ name: "empty.mp4", type: "video/mp4", size: 0 })).toBe("Replay video must be larger than 0 bytes.");
    expect(validateMp4File({ name: "huge.mp4", type: "video/mp4", size: 2 * 1024 * 1024 * 1024 + 1 })).toBe("Replay video must be 2.00 GB or smaller.");
    expect(validateMp4File({ name: "set.mp4", type: "video/mp4", size: 1024 })).toBe("");
  });

  it("formats useful file sizes", () => {
    expect(formatFileSize(512)).toBe("512 B");
    expect(formatFileSize(2048)).toBe("2.0 KB");
    expect(formatFileSize(5 * 1024 * 1024)).toBe("5.0 MB");
  });

  it("maps upload status labels exactly", () => {
    expect(uploadStatusLabel("metadata_only")).toBe("Metadata only");
    expect(uploadStatusLabel("pending_upload")).toBe("Upload pending");
    expect(uploadStatusLabel("uploaded")).toBe("Uploaded video");
  });

  it("maps processing status labels exactly", () => {
    expect(processingStatusLabel("not_processed")).toBe("Not inspected");
    expect(processingStatusLabel("processing")).toBe("Inspecting metadata");
    expect(processingStatusLabel("processed")).toBe("Metadata inspected");
    expect(processingStatusLabel("failed")).toBe("Inspection failed");
  });

  it("formats inspected technical video metadata", () => {
    const html = renderContent({
      replays: [
        makeReplay({
          source_type: "video",
          upload_status: "uploaded",
          storage_key: "users/1/matches/7/replays/set.mp4",
          processing_status: "processed",
          video_duration_seconds: 93.25,
          video_width: 1280,
          video_height: 720,
          video_fps: 59.94,
          video_codec: "h264"
        })
      ]
    });

    expect(html).toContain("Metadata inspected");
    expect(html).toContain("Duration: 1m 33s");
    expect(html).toContain("Resolution: 1280×720");
    expect(html).toContain("FPS: 59.94");
    expect(html).toContain("Codec: h264");
  });

  it("shows safe inspection failure messages", () => {
    const html = renderContent({
      replays: [
        makeReplay({
          source_type: "video",
          upload_status: "uploaded",
          storage_key: "users/1/matches/7/replays/set.mp4",
          processing_status: "failed",
          processing_error: "No usable video stream was found."
        })
      ]
    });

    expect(html).toContain("Inspection failed");
    expect(html).toContain("No usable video stream was found.");
    expect(html).not.toContain("[object Object]");
  });

  it("formats durations for replay metadata display", () => {
    expect(formatDuration(42)).toBe("42s");
    expect(formatDuration(93.25)).toBe("1m 33s");
  });

  it("runs successful initialization, direct PUT, and confirmation flow", async () => {
    const file = { name: "set.mp4", type: "video/mp4", size: 4096 } as File;
    const pendingReplay = makeReplay({ id: 8, source_type: "video", original_filename: "set.mp4", upload_status: "pending_upload", storage_key: "storage-key", content_type: "video/mp4", size_bytes: 4096 });
    const uploadedReplay = makeReplay({ ...pendingReplay, upload_status: "uploaded", uploaded_at: "2026-08-24T12:00:00Z" });
    const replayApi = {
      initializeReplayUpload: vi.fn().mockResolvedValue({ replay: pendingReplay, upload_url: "https://storage.example/upload", storage_key: "storage-key", expires_in_seconds: 900 }),
      confirmReplayUpload: vi.fn().mockResolvedValue({ replay: uploadedReplay })
    };
    const putFile = vi.fn().mockResolvedValue(undefined);

    const result = await uploadMp4Replay({ matchId: 7, file, replayApi, putFile });

    expect(replayApi.initializeReplayUpload).toHaveBeenCalledWith(7, {
      original_filename: "set.mp4",
      content_type: "video/mp4",
      size_bytes: 4096
    });
    expect(putFile).toHaveBeenCalledWith("https://storage.example/upload", file);
    expect(replayApi.confirmReplayUpload).toHaveBeenCalledWith(7, 8);
    expect(result.confirmed.replay.upload_status).toBe("uploaded");
  });

  it("does not confirm when the direct storage PUT fails", async () => {
    const file = { name: "set.mp4", type: "video/mp4", size: 4096 } as File;
    const replayApi = {
      initializeReplayUpload: vi.fn().mockResolvedValue({ replay: makeReplay({ id: 8, upload_status: "pending_upload" }), upload_url: "https://storage.example/upload", storage_key: "storage-key", expires_in_seconds: 900 }),
      confirmReplayUpload: vi.fn()
    };
    const putFile = vi.fn().mockRejectedValue(new Error("PUT failed"));

    await expect(uploadMp4Replay({ matchId: 7, file, replayApi, putFile })).rejects.toThrow("PUT failed");
    expect(replayApi.confirmReplayUpload).not.toHaveBeenCalled();
  });

  it("surfaces confirmation failures after direct storage upload", async () => {
    const file = { name: "set.mp4", type: "video/mp4", size: 4096 } as File;
    const replayApi = {
      initializeReplayUpload: vi.fn().mockResolvedValue({ replay: makeReplay({ id: 8, upload_status: "pending_upload" }), upload_url: "https://storage.example/upload", storage_key: "storage-key", expires_in_seconds: 900 }),
      confirmReplayUpload: vi.fn().mockRejectedValue(new Error("Confirm failed"))
    };
    const putFile = vi.fn().mockResolvedValue(undefined);

    await expect(uploadMp4Replay({ matchId: 7, file, replayApi, putFile })).rejects.toThrow("Confirm failed");
    expect(putFile).toHaveBeenCalled();
  });

  it("requests an authorized download URL and opens it", async () => {
    const replayApi = {
      getReplayDownloadUrl: vi.fn().mockResolvedValue({ download_url: "https://storage.example/download", expires_in_seconds: 300 })
    };
    const openUrl = vi.fn();

    const response = await openReplayDownload({ matchId: 7, replayId: 9, replayApi, openUrl });

    expect(replayApi.getReplayDownloadUrl).toHaveBeenCalledWith(7, 9);
    expect(openUrl).toHaveBeenCalledWith("https://storage.example/download");
    expect(response.expires_in_seconds).toBe(300);
  });
});

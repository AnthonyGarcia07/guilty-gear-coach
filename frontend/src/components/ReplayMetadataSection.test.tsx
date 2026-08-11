import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import { ReplayMetadataContent, replayPayloadFromForm, sourceTypeLabel, validateReplayForm } from "./ReplayMetadataSection";
import type { Replay, ReplaySourceType } from "../types";

function makeReplay(overrides: Partial<Replay> = {}): Replay {
  return {
    id: 1,
    match_id: 7,
    source_type: "replay_file",
    original_filename: "match-vs-sol.rep",
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
    onFormChange: vi.fn(),
    onEditFormChange: vi.fn(),
    onCreate: vi.fn(),
    onStartEdit: vi.fn(),
    onCancelEdit: vi.fn(),
    onUpdate: vi.fn(),
    onDelete: vi.fn(),
    ...overrides
  };

  return renderToStaticMarkup(<ReplayMetadataContent {...props} />);
}

describe("ReplayMetadataSection", () => {
  it("renders the empty state for a match with no replays", () => {
    const html = renderContent();

    expect(html).toContain("Replay Sources");
    expect(html).toContain("No replay metadata attached to this set yet.");
    expect(html).toContain("Metadata only — no file is uploaded in this phase.");
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
        makeReplay({ id: 2, source_type: "video", original_filename: "two.mp4" }),
        makeReplay({ id: 3, source_type: "external_reference", original_filename: null })
      ]
    });

    expect(html).toContain("Replay file");
    expect(html).toContain("Video");
    expect(html).toContain("External reference");
    expect(html).toContain("No filename or reference saved");
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

  it("does not render fake upload or analysis UI", () => {
    const html = renderContent({ replays: [makeReplay()] });

    expect(html).not.toContain("type=\"file\"");
    expect(html).not.toContain("Uploaded");
    expect(html).not.toContain("Processing");
    expect(html).not.toContain("Analyzing");
    expect(html).not.toContain("Ready for analysis");
  });

  it("maps source type labels exactly", () => {
    expect(sourceTypeLabel("replay_file")).toBe("Replay file");
    expect(sourceTypeLabel("video")).toBe("Video");
    expect(sourceTypeLabel("external_reference")).toBe("External reference");
  });
});

import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import { ConfirmDialog } from "./ConfirmDialog";

describe("ConfirmDialog", () => {
  it("renders the supplied destructive confirmation content", () => {
    const html = renderToStaticMarkup(
      <ConfirmDialog
        title="Delete match?"
        message="This will permanently delete this match and all associated replay videos. This action cannot be undone."
        confirmLabel="Delete Match"
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />
    );

    expect(html).toContain("role=\"dialog\"");
    expect(html).toContain("Delete match?");
    expect(html).toContain("This will permanently delete this match and all associated replay videos. This action cannot be undone.");
    expect(html).toContain("Cancel");
    expect(html).toContain("Delete Match");
  });

  it("disables actions while deletion is confirming", () => {
    const html = renderToStaticMarkup(
      <ConfirmDialog
        title="Delete replay?"
        message="This will permanently delete this replay and its uploaded video. This action cannot be undone."
        confirmLabel="Delete Replay"
        confirming
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />
    );

    expect(html).toContain("Deleting...");
    expect(html).toContain("disabled=\"\"");
  });
});

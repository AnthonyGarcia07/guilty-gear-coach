export function ConfirmDialog({
  title,
  message,
  confirmLabel,
  confirming = false,
  onCancel,
  onConfirm
}: {
  title: string;
  message: string;
  confirmLabel: string;
  confirming?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="dialog-backdrop" role="presentation">
      <section className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-dialog-title">
        <h2 id="confirm-dialog-title">{title}</h2>
        <p>{message}</p>
        <div className="confirm-dialog-actions">
          <button className="ghost-button" type="button" disabled={confirming} onClick={onCancel}>Cancel</button>
          <button className="danger-button" type="button" disabled={confirming} onClick={onConfirm}>{confirming ? "Deleting..." : confirmLabel}</button>
        </div>
      </section>
    </div>
  );
}

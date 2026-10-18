# UI Registry

This registry is the implementation-facing reference for reusable Guilty Gear Coach interface patterns. Read it with `ui-tokens.md` for values and `ui-rules.md` for behavior, accessibility, and product-language requirements.

The registry records the approved pattern to reuse. A registered pattern may still have implementation gaps; those are listed at the end and do not authorize unrelated UI changes.

---

## Baseline — Established 2026-10-17

This baseline was established through an `/imprint audit` of all production TSX files and `frontend/src/styles.css`, then approved by the developer. It preserves the existing dark-first interface while making the intended hierarchy explicit.

| Property | Approved pattern |
| --- | --- |
| App canvas | `--color-canvas` with the existing red and gold atmospheric glows |
| Major panel background | `--color-surface-panel` |
| Major panel border | `1px solid var(--color-border-default)` |
| Major panel radius | `var(--radius-control)` |
| Major panel shadow | `var(--shadow-panel)` |
| Nested card | Raised surface, subtle border, control radius, no shadow |
| Primary button | `.primary-button`: primary action surface, primary text, action shadow |
| Secondary button | `.secondary-button`: strong neutral control surface, primary text |
| Ghost button | `.ghost-button`: transparent at rest; neutral control surface on interaction |
| Danger button | `.danger-button`: danger surface and text with explicit destructive wording |
| Text — primary | `--color-text-primary` |
| Text — secondary | `--color-text-secondary` |
| Text — muted | `--color-text-muted` |
| Input background | `--color-surface-input` |
| Input border | `1px solid var(--color-border-strong)` |
| Keyboard focus | Visible `:focus-visible` treatment using `--color-focus-ring` |
| Status shapes | Pill radius with a visible text label and semantic status colors |
| Full-screen loading | `.loading-screen`, reserved for application or session initialization |
| Local loading | `.loading-panel`, constrained to the owning content area |

Use the semantic classes below before creating another variant. Token adoption must preserve the approved rendered values unless a separately approved design change says otherwise.

---

### Major Panel

File: `frontend/src/styles.css` (`.scoreboard-panel`, `.auth-card`, `.panel`, `.stat-grid article`, `.detail-grid article`)
Last updated: 2026-10-17

| Property | Approved class or token |
| --- | --- |
| Background | `--color-surface-panel` |
| Border | `--color-border-default` |
| Border radius | `--radius-control` |
| Text — primary | `--color-text-primary` |
| Text — secondary | `--color-text-secondary` |
| Spacing | `--space-panel` for standard panels; role-specific landing/auth spacing may remain |
| Hover state | None unless the entire panel is an interactive control |
| Shadow | `--shadow-panel` |
| Accent usage | Gold eyebrow or red primary action; do not color the whole panel by state |

**Pattern notes:** Major panels establish page-level grouping. Avoid nesting multiple shadowed panels solely for decoration.

### Nested Record Card

File: `frontend/src/styles.css` (`.match-row`, `.replay-card`, `.recommendation-card`)
Last updated: 2026-10-17

| Property | Approved class or token |
| --- | --- |
| Background | `--color-surface-raised` |
| Border | `--color-border-subtle` |
| Border radius | `--radius-control` |
| Text — primary | `--color-text-primary` |
| Text — secondary | `--color-text-secondary` or `--color-text-muted` according to importance |
| Spacing | `--space-grid` to `--space-card` |
| Hover state | Required only when the full card is interactive; must retain visible focus |
| Shadow | None |
| Accent usage | Compact badges, evidence states, or action controls only |

**Pattern notes:** Nested cards represent repeated records inside a major panel. They should remain visually quieter than their container.

### Buttons

File: `frontend/src/styles.css` (`.primary-button`, `.secondary-button`, `.ghost-button`, `.danger-button`)
Last updated: 2026-10-17

| Property | Approved class or token |
| --- | --- |
| Background | Variant-specific semantic surface |
| Border | None by default |
| Border radius | `--radius-control` |
| Text — primary | Primary text for primary, secondary, and ghost; danger text for destructive actions |
| Text size and weight | Inherit body size; weight `800` |
| Spacing | Minimum height `44px`, horizontal padding `18px`, content gap `8px` |
| Hover state | A consistent visible change appropriate to the variant |
| Focus state | `:focus-visible` ring using `--color-focus-ring` |
| Shadow | Primary only: `--shadow-action` |
| Accent usage | One dominant primary action per immediate context |

**Pattern notes:** Secondary is a filled neutral action. Ghost is transparent at rest and gains a neutral control surface on interaction. Danger always uses explicit destructive wording. Busy actions change their label and prevent duplicate submission.

### Form Controls and Feedback

File: `frontend/src/styles.css` and `frontend/src/components/MatchForm.tsx`
Last updated: 2026-10-17

| Property | Approved class or token |
| --- | --- |
| Background | `--color-surface-input` |
| Border | `--color-border-strong` |
| Border radius | `--radius-control` |
| Text — input | `--color-text-primary` |
| Text — label | `--color-text-secondary`, weight `700` |
| Text — hint | Gold for actionable guidance; muted for supporting context |
| Text — error | `--color-error-text` with an error surface where appropriate |
| Spacing | Label gap `8px`; field and group spacing from the documented scale |
| Focus state | Visible `:focus-visible` treatment using `--color-focus-ring` |
| Shadow | None |

**Pattern notes:** Every control requires a visible label. Placeholder text is supplemental. Field errors belong next to their control; form-level failures use `.form-error`. Backend validation remains authoritative.

### Chips and Status Badges

File: `frontend/src/styles.css` (`.chip`, `.priority`, `.win`, `.loss`)
Last updated: 2026-10-17

| Property | Approved class or token |
| --- | --- |
| Background | Neutral control surface or semantic status surface |
| Border | Default border for neutral chips; semantic border for a selected state |
| Border radius | `--radius-pill` |
| Text | Chip or semantic status text token |
| Text size and weight | `11px`–`12px`, weight `900` for compact statuses |
| Spacing | Compact inline padding using existing chip/badge proportions |
| Interactive state | Selected state must be exposed programmatically as well as visually |
| Shadow | None |
| Accent usage | Status color must always be paired with text such as Win, Loss, High, or Selected |

**Pattern notes:** Do not use color as the only state cue. A selected chip should use `aria-pressed` or equivalent native semantics.

### Confirmation Dialog

File: `frontend/src/components/ConfirmDialog.tsx` and `frontend/src/styles.css` (`.dialog-backdrop`, `.confirm-dialog`)
Last updated: 2026-10-17

| Property | Approved class or token |
| --- | --- |
| Background | `--color-surface-solid` over `--color-overlay-dialog` |
| Border | `--color-border-strong` |
| Border radius | `--radius-control` |
| Text — primary | `--color-text-primary` |
| Text — secondary | `--color-text-secondary` |
| Spacing | `--space-section` |
| Interactive state | Safe cancel action receives initial focus; Escape cancels when safe |
| Shadow | `--shadow-dialog` |
| Accent usage | Danger treatment is limited to the destructive confirmation action |

**Pattern notes:** Preserve `role="dialog"`, `aria-modal="true"`, and an accessible name. Focus must enter the dialog, remain inside it, and return to the trigger when the dialog closes.

### Loading Treatment

File: `frontend/src/App.tsx` and route-level pages using `.loading-panel`
Last updated: 2026-10-17

| Property | Approved class or token |
| --- | --- |
| Background | Inherit the owning surface |
| Border | None unless supplied by the owning panel |
| Border radius | Inherit the owning panel |
| Text | `--color-text-secondary` |
| Spacing | Center within the appropriate screen or content region |
| Interactive state | Provide a retry action after retryable failure, not permanent loading |
| Shadow | None |
| Accent usage | None required |

**Pattern notes:** `.loading-screen` may occupy the viewport during application or authentication restoration. `.loading-panel` must remain local to page content. Loading, empty, success, and error are separate states.

---

## Known Deviations Requiring Future Implementation

These items were found during the baseline audit. They are recorded for future focused tasks and are not fixed by this documentation update.

### Styling and token adoption

- `frontend/src/styles.css` still uses literal colors instead of the variables defined in `ui-tokens.md`.
- Primary white appears as `#f5f7fb`, `#fff`, and `white`; all should map to the primary text token.
- `.chip` uses a one-off 11% white border instead of the default or strong border token.
- `.form-success` uses a 14% green surface while the canonical success surface is 16%; confirm the visual result when tokenizing it.
- `.secondary-button` and `.ghost-button` currently render identically. Ghost must become transparent at rest under the approved baseline.
- Hover, pressed, and `:focus-visible` styles are not yet defined consistently.
- `.loading-screen` and `.loading-panel` currently share the same full-viewport treatment.
- Inter is preferred but not bundled, so the system sans-serif fallback is the dependable current behavior.

### Interaction and accessibility

- `frontend/src/components/ConfirmDialog.tsx` needs focus entry, focus trapping, Escape handling, and focus restoration.
- The search input in `frontend/src/pages/MatchHistory.tsx` needs a visible associated label.
- Selectable tag chips need `aria-pressed` or equivalent state semantics.
- Several visible error messages need `role="alert"` or an appropriate field relationship.
- Initial data requests in `Dashboard.tsx`, `Coaching.tsx`, `MatchDetail.tsx`, and `MatchHistory.tsx` need explicit failure states so rejected requests cannot leave permanent loading UI.
- Dashboard collections need explicit empty-state messages instead of blank list or chart regions.

Resolve these through separately approved implementation tasks with focused tests and visual checks. Do not combine the token migration with an unrelated redesign.


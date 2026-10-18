# UI Rules

These rules define how Guilty Gear Coach interfaces should behave and stay visually consistent. They are based on the current React application, `frontend/src/styles.css`, and `context/ui-tokens.md`.

The rules apply to new or materially changed UI. Some accessibility and state-handling rules describe the intended standard even where the current interface has a documented gap. Do not claim a rule is implemented without verifying the component.

---

## Sources of Truth

Use these sources in order:

1. Product meaning and vocabulary: `context/project-overview.md`
2. System and evidence boundaries: `context/architecture.md`
3. Visual values: `context/ui-tokens.md`
4. Interaction and composition rules: this file
5. Reusable component patterns: `context/ui-registry.md`
6. Existing implementation: `frontend/src/`

If an existing component conflicts with a documented rule, report the conflict. Do not silently redesign or broadly refactor it during an unrelated feature.

---

## Product Character

The UI should feel like a focused fighting-game review tool:

- Dark, high-contrast, and information-dense without feeling crowded.
- Direct and practical rather than decorative or playful.
- Evidence-first: important conclusions should show what supports them.
- Honest about loading, missing data, ambiguity, and failure.
- Understandable to a player who does not know the implementation details.

Visual references to fighting games should come from restrained color, terminology, statistics, and replay context. Avoid ornamental effects that compete with match data or evidence.

---

## Application Structure

### Public Pages

The landing, login, and signup pages sit outside the authenticated shell.

- The landing page may use the two-column hero and scoreboard-style preview.
- Authentication uses one focused card with a clear heading, labelled fields, primary submit action, and link to the alternate auth flow.
- Authenticated users who reach a public auth page should be redirected to the dashboard.

### Protected Pages

Authenticated pages use the shared application shell:

```text
Sidebar navigation
  + main content panel
      + page stack
          + page header
          + status messages
          + content sections
```

Primary navigation remains:

```text
Dashboard
Match History
Coaching
Add Match
```

- Use `NavLink` for navigation that needs an active state.
- Use `Link` for ordinary client-side navigation.
- Use a button for an action that changes state or starts work.
- Signing out returns the user to the public landing page.
- Frontend route protection improves the experience; FastAPI remains authoritative for authorization.

---

## Page Anatomy

Standard protected pages should use the existing composition:

```tsx
<section className="page-stack">
  <div className="page-header">
    <div>
      <span className="eyebrow">Section context</span>
      <h1>Page title</h1>
    </div>
    {/* Optional primary page action */}
  </div>

  {/* Messages, panels, lists, or forms */}
</section>
```

Rules:

- Use one descriptive `h1` per route-level page.
- Use the eyebrow for short section context, not a second page title.
- Put the primary page action at the end of the page header.
- Use `h2` for major panels and `h3` only for subdivisions within them.
- Keep related content in one panel; do not wrap every line or statistic in another card.
- Use nested raised cards for repeated records or recommendations inside a panel.
- Do not add breadcrumbs unless the navigation hierarchy becomes deeper than the current match-detail flow.

---

## Layout and Spacing

- Use the spacing, widths, radius, shadow, and breakpoint values from `ui-tokens.md`.
- Desktop protected pages use the 270px sidebar and main content area.
- Page sections use the existing 24px page-stack rhythm.
- Standard panels use 22px padding; repeated nested cards use 14-16px.
- Two- or three-column grids are appropriate for comparable facts, not long prose.
- Long text, evidence explanations, and forms should use the full available column.
- Let action groups wrap rather than overflow.
- Avoid fixed heights for content that may grow through localization, validation messages, or analysis output.
- Preserve a minimum interactive height of 44px for primary buttons and navigation controls when practical.

Do not introduce a second layout system, container library, or utility framework to solve a local spacing problem.

---

## Responsive Behavior

The established breakpoint is 900px.

At and below that breakpoint:

- Multi-column application, dashboard, form, replay, and detail layouts become one column.
- The sidebar returns to normal document flow.
- The page header stacks its title and action.
- Match rows and metric rows stack without dropping content.
- Controls remain reachable without horizontal scrolling.

Responsive rules:

- Do not hide errors, evidence, ownership-sensitive actions, or analysis confidence on narrow screens.
- Preserve the reading order when a grid collapses.
- Images and replay frames must remain within their container.
- Long filenames, character names, metadata, and errors must wrap or truncate with an accessible full value.
- Add another breakpoint only for a demonstrated layout failure and record it in `ui-tokens.md`.
- Verify important workflows at the 320px minimum width as well as desktop width.

---

## Typography and Content Hierarchy

- Use the typography roles from `ui-tokens.md`; do not select arbitrary font sizes or weights.
- Page titles use the established 42px desktop role.
- Section titles should remain visually below the page title.
- Muted text is for supporting information, not essential actions or errors.
- Uppercase is reserved for eyebrows and compact status or priority labels.
- Keep body copy concise and concrete.
- Avoid unexplained implementation language such as “S3 object,” “presigned URL,” or “HTTP 422” in user-facing copy.
- Technical replay metadata such as codec, dimensions, FPS, and duration may use precise terminology because it is the subject of the view.

### Product Vocabulary

Use these terms consistently:

- **Match record**: the stored review record represented by existing `/matches` routes.
- **Set**: the group of games the player reviewed and recorded.
- **Game**: won by taking two gameplay rounds.
- **Round**: one health-bar battle.
- **Replay**: metadata or uploaded footage associated with a match record.
- **Observation**: a measured replay signal.
- **Finding**: an interpretation supported by observations or events.
- **Review moment**: an evidence-linked situation worth inspecting that is not automatically a mistake.
- **Recommendation**: a proposed practice action.
- **AI coaching hypothesis**: an uncertain generated interpretation of gameplay, decisions, opportunities, alternatives, or practice needs; it is not a verified fact.
- **Multimodal gameplay interpretation**: generated analysis based on supplied frames, clips, and structured context; it may contain coaching hypotheses or explanations of deterministic results.

Do not use “rounds won” in UI copy when the stored field represents games won in the set. Existing form hints explicitly clarify this distinction and should be preserved.

---

## Color and Tokens

- Use semantic variables documented in `ui-tokens.md` when the relevant variables exist in `styles.css`.
- Do not add one-off hex, RGB, or RGBA values.
- Do not use Tailwind classes; Tailwind is not part of this project.
- Pair every status color with a text label or other non-color cue.
- Red primary actions and red destructive actions must remain distinguishable through wording and context.
- Gold is the primary label, hint, brand, and focus accent.
- Green communicates positive or selected state; it does not prove correctness.
- Keep panel surfaces neutral. Put state color in badges, messages, borders, or compact indicators.

A broad conversion of existing literals to variables is a separate implementation task and requires visual verification.

---

## Buttons, Links, and Actions

### Primary Actions

Use the primary button for the main forward action in a section or page:

- Add Match
- Save or update a match
- Upload MP4
- Submit authentication

Prefer one visually dominant primary action per immediate context.

### Secondary and Ghost Actions

Use secondary or ghost treatment for actions such as:

- Inspect metadata
- Sample frame
- Download video
- Edit
- Cancel
- Sign out

Do not use a link when the interaction performs a mutation or opens a confirmation flow.

### Destructive Actions

- Use the danger button only for destructive operations.
- Use explicit labels such as “Delete Match” or “Delete Replay,” not a vague “Confirm.”
- Explain cascading consequences, including associated replay-object deletion.
- Require confirmation before deletion.
- Disable repeat submission while deletion is in flight.
- On failure, keep or restore enough context for the user to understand what was not deleted.

### Busy State

- Disable the initiating control while its request is active.
- Change its label to a clear progress phrase such as “Saving...”, “Uploading...”, or “Inspecting...”.
- Do not disable unrelated actions unless they would conflict with the same resource operation.
- Do not show success before the backend confirms the operation.
- Always clear the busy state in success and failure paths.

---

## Forms and Validation

- Every input has a visible associated label; placeholder text is supplemental, not a label.
- Use the correct native input type and constraints where available.
- Keep forms controlled when their values participate in validation or dependent UI.
- Frontend validation provides immediate feedback, but FastAPI validation remains authoritative.
- Normalize API validation errors through `frontend/src/api/errors.ts`.
- Put field-specific errors immediately after the related control.
- Use a form-level message for failures that cannot be assigned to one field.
- Preserve entered values after a rejected submission.
- Clear stale errors when the user starts a new attempt or edits the affected value.
- Disable submission while saving to prevent duplicates.
- Keep optional fields visibly understandable through their label, hint, or surrounding context.
- Do not silently repair a semantically invalid value if the correction could change the user's meaning.

### Match Forms

- Character, result, date, rank, duration, completed-set score, tags, notes, loss reason, and practice focus use the shared `MatchForm` behavior.
- Preserve server-authoritative bounds and cross-field score validation.
- Explain the difference between set score and gameplay rounds.
- Preset chips supplement the editable tag field; they do not replace it.
- Legacy values that are no longer valid should remain visible through a hint until the user chooses a replacement.

### Replay Forms

- Show the selected filename and file size before upload.
- Limit the picker to MP4 as a convenience, while retaining backend validation.
- Explain that the file uploads directly to private object storage.
- Do not describe an uploaded or inspected video as gameplay-analyzed.
- Keep metadata-only replay creation visually distinct from MP4 upload.
- Validate sampling timestamps before requesting a frame and place the error near that control.

---

## Loading, Empty, Success, and Error States

Every asynchronous section must explicitly handle all four states.

### Loading

- Route/session restoration may use the full-screen loading treatment.
- Page or panel requests should use a local loading message within the expected content area.
- Use a specific phrase: “Loading match history...” is better than “Loading...”.
- Do not render stale data under a new route identifier.
- A rejected or abandoned request must not leave a permanent loading state.

### Empty

Empty states should explain what is missing and, when useful, the next action:

- No matches: invite the user to add the first set.
- No mistake tags: explain that they appear after logging matches.
- Insufficient coaching data: state the sample requirement when known.
- No replays: explain that replay metadata or an MP4 can be attached.
- No search results: distinguish an empty account from a filter with no matches.

Never render an empty chart, table, or unlabeled blank panel as the only signal.

### Success

- Show success only after confirmed completion.
- Use `role="status"` for non-urgent success announcements.
- Keep messages concise and dismissible when they remain on the page.
- Navigation may carry a one-time success message, but remove it from navigation state after reading it so refresh does not repeat it.

### Error

- Convert unknown and API errors into safe, human-readable messages.
- Do not show stack traces, storage keys, local paths, raw subprocess output, or private URLs.
- Use `role="alert"` or an equivalent announced error relationship for new error messages.
- Distinguish load failure from an empty dataset.
- Keep retryable controls available when retry is safe.
- Do not erase successfully loaded unrelated content because one local action failed.

---

## Replay and Analysis States

Replay UI must reflect the actual lifecycle rather than a generic “ready” state.

### Upload State

Display meaningful labels for:

- Metadata only
- Pending upload
- Uploaded

Do not trust or display a client-claimed successful upload before backend confirmation.

### Processing State

Display meaningful labels for:

- Not processed
- Processing
- Processed
- Failed

When a future worker is introduced, queued and stage progress should be shown separately from upload status.

### Analysis Run State

Analysis runs have their own durable lifecycle and must not reuse upload or individual evidence labels:

- `queued`: accepted and waiting for a worker;
- `running`: claimed by a worker, with the current stage shown when available;
- `completed`: the run finished, even if some individual evidence is `unknown`;
- `failed`: the run stopped because of a technical failure, with a safe retry path when retry is valid.

Do not describe a queued run as processing, a completed run as conclusive, or an unknown observation as a failed run. Clear stale progress after refresh and recover from rejected status requests without leaving the interface permanently busy.

### Evidence State

The UI must preserve these distinctions:

- `ok`: processing succeeded and produced evidence.
- `unknown`: processing succeeded, but visual evidence was inconclusive.
- `failed`: extraction or detection failed technically.

Do not render `unknown` as “no gameplay,” “false,” or an error. Do not render `failed` as ambiguous evidence.

### Precision and Confidence

- Display sampled boundary ranges as ranges, not exact timestamps.
- Label measured observations separately from inferred events.
- Label findings, review moments, and recommendations separately from source evidence.
- Label multimodal interpretations and AI coaching hypotheses as generated, identify their source media and supplied evidence, and state when they lack independent validation.
- Confidence must describe uncertainty; it must not be styled as a guarantee.
- Whenever practical, make a finding's timestamp or evidence reference open the relevant replay moment.

### Review Moments and Generated Interpretations

- Use non-accusatory wording for a review moment. The first targeted example is: “The round appears to have ended while Burst was visually available.”
- When generated interpretation accompanies a deterministic result, show the observation, supporting timestamp or range, and caveat before or alongside it.
- When the LLM proposes a hypothesis that has no deterministic finding, show the source clip or frames, label it as not independently validated, and keep its uncertainty visible.
- Do not let fluent generated text visually outrank the evidence-linked review moment.
- If generation is unavailable, refused, timed out, or not consented to, keep the deterministic result usable and explain only that the generated layer is unavailable.
- Provide separate correctness and usefulness feedback controls. Correctness feedback concerns the evidence-linked result; usefulness feedback concerns whether the coaching helped.
- Do not silently treat user feedback as a replacement for measured evidence.

### Third-Party Media Disclosure

Before a private frame or clip is sent to a third-party model, the UI must clearly state what media leaves project-controlled infrastructure, why it is sent, and the relevant retention or training policy. Require the consent behavior approved for that feature and offer a path that keeps deterministic analysis usable without generation.

### Claims

UI copy must not imply capabilities that do not exist. For example:

- “Metadata inspected” is accurate after `ffprobe` succeeds.
- “Frame sampled” is accurate after FFmpeg returns an image.
- “Ready for gameplay analysis” is not accurate until that workflow exists.
- “The player missed an anti-air” is not accurate as a verified fact without supporting analysis. “AI hypothesis: this may have been a missed anti-air” may be appropriate when linked to the inspected media and clearly marked as unvalidated.

---

## Lists, Statistics, and Data Displays

- Repeated records use semantic lists, articles, or links rather than anonymous clickable containers.
- A match row should keep result, matchup, date/rank, and review context legible.
- The entire row may be a link when it has one clear destination.
- Use `aria-current="page"` for active pagination.
- Disable previous and next controls at their real boundaries.
- Keep filters distinct from server-side pagination; current match-history text filtering applies to the loaded page only and its copy must say so.
- Percentages include the percent sign and should use consistent rounding from the backend contract.
- Progress bars need a nearby text value; the visual fill is not the only representation.
- Use “Not logged,” “Unranked,” or an equally explicit fallback instead of blank output.
- Do not infer meaning from small sample sizes; show the count or insufficiency message.

---

## Dialogs

Confirmation dialogs must:

- Use `role="dialog"` and `aria-modal="true"`.
- Have an accessible name through `aria-labelledby` or `aria-label`.
- Describe the consequence in visible text.
- Move focus into the dialog when opened.
- Keep keyboard focus inside while open.
- Support Escape to cancel when no irreversible request is in progress.
- Restore focus to the triggering control when closed.
- Keep cancel and confirm actions keyboard reachable.
- Prefer initial focus on the safe cancel action for destructive confirmations.
- Prevent duplicate confirmation while the operation is running.

The current shared `ConfirmDialog` already provides dialog roles and labelled destructive actions, but focus management, focus trapping, Escape handling, and focus restoration still require a dedicated improvement task.

---

## Accessibility

### Semantics

- Use landmarks such as `main`, `nav`, and `aside` according to their real role.
- Preserve a logical heading hierarchy.
- Use native buttons, links, inputs, selects, and textareas before custom controls.
- Icon-only controls require an accessible name; prefer an icon paired with visible text for important actions.
- Decorative icons should not become duplicate screen-reader content.

### Keyboard and Focus

- Every interactive element must work without a mouse.
- Provide a visible `:focus-visible` treatment using the documented focus token.
- Focus order must follow the visual and reading order.
- Do not remove outlines without an equally visible replacement.
- Avoid positive `tabIndex` values.

### Forms and Messages

- Associate errors and hints with their fields using native structure or ARIA relationships when needed.
- Announce urgent errors; announce non-urgent completion with status semantics.
- Required state must be conveyed programmatically, not only with an asterisk or color.
- Disabled controls must still leave enough visible context to explain why work is in progress.

### Images and Media

- Replay frames require descriptive alt text that identifies their replay context without claiming what the analyzer found.
- Decorative images use empty alt text.
- Do not autoplay video or audio.
- Future video controls must be keyboard accessible and expose the current timestamp.

### Color and Contrast

- Never use color as the only status indicator.
- Essential text must use primary or secondary text colors rather than muted text.
- Verify contrast when combining translucent status colors with raised surfaces.
- A new token or state color requires contrast review in its real component context.

---

## Icons

- Use the installed `lucide-react` library for interface icons.
- Existing navigation and action icons use 18px as the default size.
- Use one icon style within an action group.
- Pair icons with text for primary, destructive, upload, inspection, and navigation actions.
- Do not use an icon as evidence of success, failure, or confidence without a text label.
- Do not add a second icon library for a small gap; first verify that Lucide lacks an appropriate symbol.

---

## Motion and Feedback

- The current interface has no animation system; do not add decorative motion incidentally.
- Use immediate text and disabled-state feedback for asynchronous actions.
- If motion is introduced for a specific usability purpose, keep it short and respect `prefers-reduced-motion`.
- Do not animate analytical values in a way that suggests false precision or delays access to the actual number.

---

## Component Placement

- Route-level composition belongs in `frontend/src/pages/`.
- Reusable interface elements belong in `frontend/src/components/`.
- API transport and error normalization belong in `frontend/src/api/`.
- Shared domain types belong in `frontend/src/types.ts`.
- Extract a shared component when it has repeated use or owns meaningful interaction behavior.
- Do not extract a component solely to reduce a short page file.
- Components do not call PostgreSQL or R2 directly.
- Large replay bytes follow the approved presigned storage flow rather than passing through an invented frontend abstraction.

Once `ui-registry.md` exists, reuse its registered patterns before creating another component variant.

---

## UI Testing Rules

New or changed behavior should have focused Vitest coverage for the relevant risks:

- Loading, empty, success, and failure rendering.
- Client validation and normalized backend field errors.
- Busy controls and duplicate-submission prevention.
- Navigation and return-path behavior.
- Pagination boundaries and `aria-current`.
- Confirmation-dialog labels and destructive workflow behavior.
- Replay upload, inspection, sampling, object-URL cleanup, and failure messages.
- Evidence-state wording, especially `unknown` versus `failed`.
- Generated provenance, AI-hypothesis labels, source-media links, uncertainty, and lack of independent validation.
- Accessibility attributes introduced by the feature.

Prefer testing observable behavior and output over internal state or implementation details.

Visual changes should also be checked at desktop width, the 900px collapse boundary, and the 320px minimum width. A screenshot alone does not replace interaction or accessibility testing.

---

## Current Baseline Gaps

These observations identify future work; they do not authorize changes during unrelated tasks:

- The stylesheet lacks an explicit `:focus-visible` treatment.
- The shared confirmation dialog lacks focus trapping, Escape handling, and focus restoration.
- Some load-only effects do not currently expose an error state and can remain visually stuck after rejection.
- Several errors are visible text without explicit alert semantics or field relationships.
- The sidebar does not yet have a dedicated compact-navigation pattern below 900px.
- Secondary and ghost buttons currently render the same way.
- Loading-screen and loading-panel styling currently share a full-viewport treatment even though their semantic scope differs.

The first `ui-registry.md` baseline was established on 2026-10-17. Use `/imprint` only when a reusable visual pattern is introduced or materially changed, and use `/imprint audit` when the baseline needs a deliberate reassessment. Neither command authorizes automatic fixes to these gaps.

---

## Do Not

- Do not redesign existing pages while implementing an unrelated feature.
- Do not add hardcoded colors or duplicate token values.
- Do not introduce Tailwind, a component framework, or another icon library without an approved need.
- Do not place API calls in purely presentational components.
- Do not rely on frontend checks for authorization or replay ownership.
- Do not leave asynchronous UI in a permanent loading or disabled state after failure.
- Do not show a blank panel when a loading, empty, or error explanation is available.
- Do not use color as the only indication of win, loss, priority, selection, confidence, or failure.
- Do not claim replay analysis beyond the evidence the backend actually produced.
- Do not present multimodal model wording as a measured gameplay fact.
- Do not hide uncertainty ranges to make results appear more precise.
- Do not expose storage keys, private URLs, credentials, stack traces, or subprocess output.
- Do not make destructive actions immediate or ambiguous.
- Do not add motion, overlays, or card nesting only for decoration.

---

## Invariants

- The UI remains dark-first and uses the tokens in `ui-tokens.md`.
- Existing semantic classes and registered patterns are reused before new variants are created.
- Every asynchronous workflow has loading, empty where applicable, success, and failure behavior.
- Every mutation prevents accidental duplicate submission.
- Server validation and authorization remain authoritative.
- Replay state, processing state, and evidence state are displayed as separate concepts.
- `unknown` and `failed` never mean the same thing.
- Evidence, findings, review moments, recommendations, and multimodal interpretations—including AI coaching hypotheses and explanations—remain visually and linguistically distinct.
- Important actions are labelled, keyboard reachable, and visibly focusable.
- Responsive layouts preserve information and action availability.
- Destructive actions explain their consequences and require confirmation.
- UI tests protect meaningful interaction and state behavior.

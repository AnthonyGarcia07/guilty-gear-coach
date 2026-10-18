# UI Tokens

This document records the visual tokens already present in Guilty Gear Coach and gives them stable semantic names for future UI work. The values were extracted from `frontend/src/styles.css` and verified against the current dashboard and replay-processing screenshots.

The application currently uses literal CSS values rather than custom properties. The token names below are the approved target contract, not a claim that `styles.css` has already been migrated. Do not change the visual appearance merely to adopt the names.

---

## How to Use

Guilty Gear Coach uses semantic CSS classes in `frontend/src/styles.css`. It does not use Tailwind CSS or CSS-in-JS.

For future UI implementation:

- Reuse an existing semantic class or component pattern first.
- Use the tokens in this file instead of adding a new one-off color, radius, or shadow.
- If the needed CSS variable is not yet defined in `styles.css`, add the smallest required token definition as part of the approved UI task and preserve the rendered value.
- Keep dynamic values, such as a calculated progress-bar width, inline only when they genuinely come from runtime data.
- Update this document before introducing a new reusable visual value.

Example target usage after the relevant variables exist:

```css
.panel {
  color: var(--color-text-primary);
  background: var(--color-surface-panel);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-control);
  box-shadow: var(--shadow-panel);
}
```

Do not add new component styles like this:

```css
/* Avoid: duplicates project values without semantic meaning. */
.new-card {
  color: #f5f7fb;
  background: rgba(17, 20, 27, 0.86);
  border-radius: 8px;
}
```

---

## Canonical Token Definitions

The following block is the target variable set for a future focused migration of `frontend/src/styles.css`. Values match the current interface unless explicitly described as a shared semantic alias.

```css
:root {
  /* Typography */
  --font-sans: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;

  /* Base backgrounds */
  --color-canvas: #0b0d10;
  --color-surface-input: #0e1118;
  --color-surface-solid: #11141b;
  --color-surface-panel: rgba(17, 20, 27, 0.86);
  --color-surface-sidebar: rgba(9, 11, 15, 0.92);
  --color-surface-raised: rgba(255, 255, 255, 0.04);
  --color-surface-control: rgba(255, 255, 255, 0.06);
  --color-surface-control-strong: rgba(255, 255, 255, 0.08);
  --color-meter-track: #262a34;

  /* Text */
  --color-text-primary: #f5f7fb;
  --color-text-secondary: #c7cedc;
  --color-text-muted: #9aa5b8;
  --color-text-chip: #dbe2ee;
  --color-text-inverse: #13151b;

  /* Brand and emphasis */
  --color-action-primary: #f23f54;
  --color-action-primary-soft: rgba(242, 63, 84, 0.16);
  --color-action-primary-active: rgba(242, 63, 84, 0.20);
  --color-action-primary-border: rgba(242, 63, 84, 0.50);
  --color-accent-gold: #ffcc5c;
  --color-accent-green: #38d39f;
  --color-focus-ring: #ffcc5c;

  /* Status */
  --color-success-text: #7af0c4;
  --color-win-text: #66f2c0;
  --color-warning-text: #ffdc87;
  --color-error-text: #ff9b9b;
  --color-loss-text: #ff8795;
  --color-danger-text: #ff8080;
  --color-success-soft: rgba(56, 211, 159, 0.16);
  --color-success-selected: rgba(56, 211, 159, 0.18);
  --color-success-border: rgba(56, 211, 159, 0.45);
  --color-warning-soft: rgba(255, 204, 92, 0.16);
  --color-error-soft: rgba(255, 73, 73, 0.12);
  --color-danger-soft: rgba(255, 73, 73, 0.15);

  /* Borders and overlays */
  --color-border-subtle: rgba(255, 255, 255, 0.08);
  --color-border-default: rgba(255, 255, 255, 0.10);
  --color-border-strong: rgba(255, 255, 255, 0.12);
  --color-overlay-dialog: rgba(0, 0, 0, 0.68);

  /* Background atmosphere */
  --color-glow-red: rgba(217, 38, 69, 0.18);
  --color-glow-gold: rgba(245, 190, 64, 0.14);

  /* Radius */
  --radius-control: 8px;
  --radius-pill: 999px;

  /* Shadows */
  --shadow-action: 0 14px 36px rgba(242, 63, 84, 0.32);
  --shadow-panel: 0 22px 60px rgba(0, 0, 0, 0.30);
  --shadow-dialog: 0 22px 70px rgba(0, 0, 0, 0.48);

  /* Common spacing */
  --space-tight: 4px;
  --space-control: 8px;
  --space-inline: 10px;
  --space-group: 12px;
  --space-grid: 14px;
  --space-card: 16px;
  --space-field: 18px;
  --space-panel: 22px;
  --space-section: 24px;
  --space-page-edge: 28px;
  --space-page: 34px;
  --space-hero: 42px;

  /* Type sizes */
  --text-micro: 11px;
  --text-caption: 12px;
  --text-small: 13px;
  --text-body: 16px;
  --text-lead: 20px;
  --text-stat: 28px;
  --text-page-title: 42px;
  --text-hero: clamp(48px, 8vw, 104px);
}
```

`rgba(255, 255, 255, 0.11)` appears once on existing tag borders. It is not a separate semantic token; when that area is next touched, use either the default or strong border token after confirming the visual result.

---

## Color Usage

### Foundations

| Role | Token | Current value | Usage |
| --- | --- | --- | --- |
| App canvas | `--color-canvas` | `#0b0d10` | Root and body background |
| Form input | `--color-surface-input` | `#0e1118` | Inputs, selects, and textareas |
| Solid surface | `--color-surface-solid` | `#11141b` | Confirmation dialog |
| Main panel | `--color-surface-panel` | `rgba(17, 20, 27, 0.86)` | Panels, cards, and stats |
| Sidebar | `--color-surface-sidebar` | `rgba(9, 11, 15, 0.92)` | Persistent application navigation |
| Nested surface | `--color-surface-raised` | White at 4% | Match rows, replay cards, recommendations |
| Control surface | `--color-surface-control` | White at 6% | Pagination and chips |
| Strong control | `--color-surface-control-strong` | White at 8% | Secondary buttons and interactive ghost-button states |
| Meter track | `--color-meter-track` | `#262a34` | Win-rate and landing-page bars |

### Text

| Role | Token | Current value | Usage |
| --- | --- | --- | --- |
| Primary | `--color-text-primary` | `#f5f7fb` | Headings, important values, controls |
| Secondary | `--color-text-secondary` | `#c7cedc` | Body copy, labels, dialog text |
| Muted | `--color-text-muted` | `#9aa5b8` | Supporting metadata and empty states |
| Chip | `--color-text-chip` | `#dbe2ee` | Tags and compact labels |
| Inverse | `--color-text-inverse` | `#13151b` | Text on the gold brand mark |

Use white only through the primary text token. Existing `white` and `#fff` declarations are legacy aliases of the same visual role.

### Brand and Emphasis

| Role | Token | Current value | Usage |
| --- | --- | --- | --- |
| Primary action | `--color-action-primary` | `#f23f54` | Main calls to action |
| Primary soft | `--color-action-primary-soft` | Red at 16% | Active navigation and loss backgrounds |
| Gold accent | `--color-accent-gold` | `#ffcc5c` | Eyebrows, logo, hints, gradient endpoint |
| Green accent | `--color-accent-green` | `#38d39f` | Positive values and gradient start |
| Focus ring | `--color-focus-ring` | Gold accent | Intended visible keyboard focus color |

Primary red is both a brand/action color and part of the loss/error family. Keep action labels and destructive labels explicit so color is never the only distinction.

### Status Colors

| State | Background token | Text token |
| --- | --- | --- |
| Success message | Green at 14-16% | `--color-success-text` |
| Win badge | `--color-success-soft` | `--color-win-text` |
| Selected chip | `--color-success-selected` | Inherited chip text |
| Medium priority | `--color-warning-soft` | `--color-warning-text` |
| Field/form error | `--color-error-soft` | `--color-error-text` |
| Loss badge | `--color-action-primary-soft` | `--color-loss-text` |
| Destructive action | `--color-danger-soft` | `--color-danger-text` |

Color must be paired with text such as “win,” “loss,” “high,” or an error message.

The current palette does not define colors for observation provenance, evidence confidence, review moments, AI coaching hypotheses, or other generated interpretations. Do not assign new semantic colors to those concepts until an approved UI task defines and visually verifies the pattern. Until then, distinguish them with explicit labels, headings, and existing neutral/status treatments; color must never imply that generated output is measured evidence or independently validated.

### Gradients

The body uses two restrained atmospheric gradients over the canvas:

```css
background:
  linear-gradient(135deg, var(--color-glow-red), transparent 36%),
  linear-gradient(225deg, var(--color-glow-gold), transparent 38%),
  var(--color-canvas);
```

Progress and win-rate bars use:

```css
background: linear-gradient(90deg, var(--color-accent-green), var(--color-accent-gold));
```

Do not introduce additional decorative gradients without updating this file and confirming they fit the existing visual language.

---

## Typography

The current font stack prefers Inter but does not load a web font. If Inter is unavailable on the device, the UI uses the system sans-serif fallback.

| Element | Size | Weight | Line height | Color |
| --- | --- | --- | --- | --- |
| Hero title | `clamp(48px, 8vw, 104px)` | Browser heading default/bold | `1` | Primary |
| Page title | `42px` | Browser heading default/bold | `1` | Primary |
| Landing lead | `20px` | Normal | Browser default | Secondary |
| Stat value | `28px` | `700` through `<strong>` | Browser default | Primary |
| Body text | Browser default `16px` | Normal | Browser default | Primary or secondary |
| Field label | Browser default `16px` | `700` | Browser default | Secondary |
| Helper/error text | `13px` | `700` | Browser default | Gold or error |
| Eyebrow | `12px` | `800` | Browser default | Gold |
| Win/loss badge | `12px` | `900` | Browser default | Status color |
| Priority badge | `11px` | `900` | Browser default | Status color |

Current emphasis weights include `700`, `800`, `900`, and `950`. New components should reuse an existing semantic role rather than choosing a new weight arbitrarily.

Text transformations currently used:

- Eyebrows and status badges are uppercase.
- Eyebrows currently use zero additional letter spacing.
- Headings and ordinary body content retain natural casing.

---

## Spacing

The existing stylesheet uses a compact scale derived from recurring layout needs rather than a strict four-pixel utility system.

| Token | Value | Current usage |
| --- | --- | --- |
| `--space-tight` | `4px` | Dense metadata and nested text |
| `--space-control` | `8px` | Button icon gaps, field-label gaps, navigation gaps |
| `--space-inline` | `10px` | Small action groups and chip spacing |
| `--space-group` | `12px` | Button groups, lists, and message internals |
| `--space-grid` | `14px` | Stat grids, replay forms, and compact cards |
| `--space-card` | `16px` | Nested card padding |
| `--space-field` | `18px` | Form-grid gaps and section headers |
| `--space-panel` | `22px` | Standard panel padding |
| `--space-section` | `24px` | Page-stack gaps and large grid separation |
| `--space-page-edge` | `28px` | Landing edge padding and scoreboard padding |
| `--space-page` | `34px` | Desktop application content padding |
| `--space-hero` | `42px` | Landing hero column gap |

Existing one-off values such as `5px`, `9px`, `13px`, and `30px` belong to specific badge, input, or auth-card geometry. Do not promote them to global tokens unless they repeat in a new reusable pattern.

---

## Shape and Elevation

### Radius

| Token | Value | Usage |
| --- | --- | --- |
| `--radius-control` | `8px` | Panels, buttons, inputs, dialogs, cards, images |
| `--radius-pill` | `999px` | Chips, priorities, win/loss badges, meter tracks |

The visual language is intentionally compact and slightly sharp. Do not add large rounded-card radii unless the design direction is intentionally changed.

### Shadows

| Token | Value | Usage |
| --- | --- | --- |
| `--shadow-action` | `0 14px 36px rgba(242, 63, 84, 0.32)` | Primary call-to-action glow |
| `--shadow-panel` | `0 22px 60px rgba(0, 0, 0, 0.30)` | Main surfaces |
| `--shadow-dialog` | `0 22px 70px rgba(0, 0, 0, 0.48)` | Modal confirmation |

Nested cards do not receive additional shadows; they rely on borders and subtle surface contrast.

---

## Layout Tokens

| Role | Value | Current usage |
| --- | --- | --- |
| Minimum viewport width | `320px` | Body minimum width |
| Landing content maximum | `1120px` | Two-column landing hero |
| Landing minimum height | `620px` | Desktop hero composition |
| Sidebar width | `270px` | Desktop application shell |
| Auth/dialog maximum width | `430px` | Login, signup, confirmation dialog |
| Search maximum width | `520px` | Match-history filter |
| Sampled-frame maximum width | `640px` | Displayed replay frame |
| Frame-sample container maximum | `680px` | Timestamp controls and image |
| Desktop content padding | `34px` | Main application panel |
| Compact content padding | `22px` | Main panel below breakpoint |
| Primary breakpoint | `900px` | Collapse multi-column layouts |

The interface currently has one responsive breakpoint. New breakpoints require evidence from a real layout problem and should be documented here.

---

## Component Tokens

### Panels

```text
background: surface-panel
border: 1px solid border-default
radius: 8px
padding: 22px for standard panels
shadow: panel shadow on major surfaces
```

Nested recommendation, replay, and match cards use the raised surface, subtle border, 8px radius, and 14-16px padding.

### Buttons

All primary button families share:

```text
minimum height: 44px
horizontal padding: 18px
radius: 8px
font weight: 800
icon/content gap: 8px
disabled opacity: 0.6
```

| Variant | Background | Text | Additional treatment |
| --- | --- | --- | --- |
| Primary | Primary action | White/primary | Action shadow |
| Secondary | Strong control surface | Primary | No border |
| Ghost | Transparent at rest | Primary | Strong control surface on interaction |
| Danger | Danger soft | Danger text | Destructive wording required |

The approved registry baseline distinguishes these roles: secondary buttons are filled neutral actions, while ghost buttons are transparent at rest. The current stylesheet still renders both variants identically and requires a future implementation task.

### Form Controls

```text
background: surface-input
border: 1px solid border-strong
radius: 8px
padding: 12px 13px
text: primary
label: secondary, weight 700
textarea minimum height: 104px
```

The current stylesheet does not define explicit placeholder, hover, or `:focus-visible` styling. Those accessibility states belong in `ui-rules.md` and should reuse the tokens here rather than inventing new colors.

### Chips and Badges

```text
radius: pill
border: subtle/default
padding: 9px 12px for chips
padding: 4-5px 9-10px for status badges
uppercase: status and priority badges only
```

Selected chips add the success-selected background and success border. Selection must remain understandable without color alone.

### Progress Bars

```text
height: 10px
track: meter-track
fill: green-to-gold gradient
radius: pill
overflow: hidden
```

The fill width may be set inline because it represents runtime data.

### Dialog

```text
backdrop: dialog overlay
content width: min(430px, 100%)
content background: solid surface
border: strong
radius: 8px
padding: 22px
shadow: dialog shadow
```

### Navigation

- Desktop sidebar width is 270px and remains sticky at the top.
- Navigation items have a 44px minimum height and 8px radius.
- Active navigation uses the soft primary-action background and primary text.
- The brand mark is 44px square, gold, and uses inverse text.

---

## Responsive Behavior

At `900px` and below:

- The application shell, landing hero, and dashboard become single-column.
- The sidebar becomes normal document flow rather than sticky full-height navigation.
- The main panel padding changes from 34px to 22px.
- Stat, detail, coaching, history-toolbar, replay, and form grids become single-column.
- Match rows, bar rows, and the landing round header become single-column.
- Page headers stack vertically and align to the start.

Responsive changes should preserve all information and actions. Do not hide evidence, error messages, replay status, or ownership-sensitive actions merely to simplify a narrow layout.

---

## Motion

The current UI defines no animations or transition tokens. Preserve that restrained behavior until motion is introduced for a specific usability purpose. Any future motion must respect `prefers-reduced-motion` and be documented here.

---

## Current Baseline Gaps

These are documentation findings, not authorization to modify the UI:

- `styles.css` repeats literal colors instead of defining the variables documented here.
- Inter is preferred but not loaded, so its appearance depends on local availability.
- Focus-visible styles are not explicitly defined.
- Button hover and pressed states are not explicitly defined.
- Secondary and ghost buttons are still visually identical in the stylesheet even though the approved registry baseline distinguishes them.
- Several nearly identical border-alpha values exist.
- Success backgrounds use both 14% and 16% green opacity.

Resolve these only through an approved UI task. A migration should include visual regression checks and must not combine unrelated redesign work.

---

## Invariants

- The product remains dark-first unless a separate theme project is approved.
- Do not add new hardcoded hex, RGB, or RGBA values to components or component-specific CSS.
- Use semantic token names; do not name tokens after a single page or component.
- Do not use raw Tailwind color classes; Tailwind is not part of this project.
- Primary red is for primary actions and established loss emphasis, not arbitrary decoration.
- Gold is the main label, brand, hint, and focus accent.
- Green communicates positive outcomes, selected states, and the start of performance gradients.
- Error, warning, win, loss, and priority states must include text, not color alone.
- Use 8px for standard controls and surfaces and pill radius for compact statuses.
- Reuse the existing spacing and type roles before adding another value.
- Runtime measurements may set numeric inline styles; static visual values belong in CSS.
- Preserve readable contrast against the dark canvas and translucent surfaces.
- Update this document when a reusable token is intentionally added or changed.
- Creating these tokens does not authorize a broad stylesheet refactor or visual redesign.

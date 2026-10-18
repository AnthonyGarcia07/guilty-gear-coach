---
name: imprint
description: Audit Guilty Gear Coach UI consistency or record a reusable visual or interaction pattern in context/ui-registry.md after that pattern is introduced or materially changed.
---

# Imprint

Use this skill to keep the established Guilty Gear Coach UI baseline accurate. The project uses semantic CSS classes in `frontend/src/styles.css`, documented tokens in `context/ui-tokens.md`, rules in `context/ui-rules.md`, and reusable patterns in `context/ui-registry.md`.

Do not run normal imprinting after every component or every UI edit. Use it only when a reusable visual or interaction pattern is introduced or materially changed. Use `/imprint audit` for a deliberate consistency reassessment. A page-specific composition or an accidental deviation is not automatically a reusable pattern.

## Shared Preparation

Before either mode:

1. read `AGENTS.md`;
2. read `context/ui-tokens.md`, `context/ui-rules.md`, and `context/ui-registry.md`;
3. inspect the relevant React/TypeScript files and the CSS selectors they use;
4. distinguish an intentional reusable pattern from a one-off implementation or existing inconsistency.

The registry baseline already exists. Do not recreate or replace it unless the developer explicitly approves a new baseline.

## Normal Mode

Invocation:

```text
/imprint
/imprint [filepath]
```

If a path is provided, inspect that implementation and its associated CSS. Otherwise, use the UI files changed by the current approved task. If the target is genuinely unclear, ask which UI change should be evaluated.

Compare the implementation with the existing registry:

- If it follows an existing pattern without materially changing it, report that no registry update is needed.
- If it intentionally changes a registered reusable pattern, update that entry and explain the compatibility impact.
- If it introduces a genuinely reusable pattern, add one concise entry.
- If it conflicts with the approved tokens or rules, report the deviation; do not legitimize it by recording it as the baseline.

Capture only information future UI work needs:

- semantic component and CSS class names;
- relevant token usage;
- typography, surfaces, borders, spacing, and reusable responsive behavior;
- hover, focus, disabled, selected, loading, empty, success, and error states where applicable;
- labels, keyboard behavior, dialog semantics, focus behavior, and other accessibility requirements;
- evidence, confidence, and provenance presentation when the UI shows replay analysis.

Use actual selectors and tokens from `frontend/src/styles.css`. Do not translate them into Tailwind-style utility classes. Include file references only when they help locate the canonical implementation.

Update `context/ui-registry.md` in place. Avoid duplicate entries, exhaustive per-component inventories, and records of context-dependent width, positioning, or layout details unless they form a deliberate reusable rule.

Afterward, summarize what was added or changed and flag any implementation drift that remains. This skill does not authorize application-code fixes.

## Audit Mode

Invocation:

```text
/imprint audit
```

Audit mode evaluates the current UI against the established tokens, rules, and registry. Inspect the relevant breadth of `frontend/src/pages/`, `frontend/src/components/`, and `frontend/src/styles.css` needed to support the requested audit.

Report:

- consistent use of registered patterns;
- conflicting selectors, tokens, spacing, typography, responsive behavior, or interaction states;
- hardcoded or one-off values that bypass documented tokens;
- accessibility gaps;
- missing states such as loading, empty, success, or failure;
- unclear presentation of deterministic evidence versus AI-generated hypotheses.

For each finding, give the file and line when available, the expected documented pattern, and the observed difference. Separate confirmed inconsistencies from optional improvements.

Audit mode is report-only. Do not fix UI code or change `context/ui-registry.md` unless the developer separately approves a specific baseline or registry change. Majority usage alone does not define the correct pattern; the context documents and confirmed product intent do.

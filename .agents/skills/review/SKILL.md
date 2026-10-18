---
name: review
description: Review a completed Guilty Gear Coach feature against its approved scope, project boundaries, evidence model, UI rules, tests, and intended environment without fixing findings automatically.
---

# Review

Use this skill after a meaningful implementation feature or risky refactor, or when the developer explicitly requests a review. It is not required after every trivial or documentation-only change.

A review reports evidence and limitations. It does not modify files, fix findings, update progress, or declare unverified paths production-ready.

## Establish the Benchmark

Read:

1. `AGENTS.md`;
2. the approved implementation plan, if one exists;
3. the developer's task and acceptance criteria;
4. relevant context files in the order defined by `AGENTS.md`;
5. `context/progress-tracker.md`;
6. the actual diff, affected code, and relevant tests.

A separate `/architect` plan is not mandatory when the requested behavior and context already define a clear benchmark. Ask for clarification only when missing intent prevents a meaningful review.

Distinguish implemented behavior from planned roadmap language.

## Review Layer 1: Scope and Behavior

Check whether:

- every approved requirement is implemented;
- unrequested behavior or dependencies expanded the scope;
- existing behavior changed intentionally;
- API and UI contracts agree;
- data enters, transforms, persists, and returns as intended;
- loading, empty, success, and failure behavior is complete.

## Review Layer 2: System Integrity

Apply the relevant project checks:

- frontend, API route, schema, model, service, and authentication responsibilities remain in the correct layer;
- account ownership is enforced through `Replay -> Match -> User` without trusting client owner identifiers or revealing inaccessible records;
- PostgreSQL rows and R2 objects have explicit partial-failure and recovery handling;
- replay readiness and timestamps are validated before expensive processing;
- temporary media is cleaned up and FFmpeg/`ffprobe` timeouts and safe errors are preserved;
- `unknown` visual evidence remains distinct from `failed` processing;
- measured observations, inferred ranges, deterministic findings, review moments, and AI coaching hypotheses retain distinct provenance;
- multimodal processing is authorized, consent-aware, bounded, backend-only, and unable to overwrite deterministic results;
- semantic CSS, tokens, registered UI patterns, responsive behavior, and accessibility rules are respected;
- new abstractions or dependencies have a demonstrated need.

## Review Layer 3: Verification and Readiness

Inspect and, when safe and in scope, run focused verification before broader relevant checks.

Confirm:

- regression or characterization coverage protects risky behavior;
- backend services can be tested without real R2, FFmpeg, `ffprobe`, or model providers where practical;
- any database-mutating integration test uses a verified isolated disposable database;
- migrations have upgrade verification and rollback analysis where practical;
- environment-sensitive behavior uses the installed versions and intended configuration;
- browser, real-media, storage, worker, and provider paths that were not exercised are reported as unverified;
- commands, results, warnings, and skipped checks are accurately recorded.

Do not run destructive infrastructure actions or tests against development or production data.

## Findings

For each issue, report:

- severity;
- classification: confirmed defect, future concern, or optional improvement;
- file and line when available;
- evidence;
- user or maintenance impact;
- the requirement or project rule affected.

Use these severities:

- **Critical:** security, privacy, ownership, destructive-data, or core correctness failure that blocks release.
- **High:** approved behavior is missing or a likely user path fails.
- **Medium:** maintainability, evidence, recovery, accessibility, or edge-case gap that should be addressed soon.
- **Low:** bounded inconsistency or optional improvement with limited impact.

Do not inflate speculative concerns. State uncertainty and the verification needed to confirm them.

## Report

```markdown
## Review — [Feature]

### Scope and behavior
[Pass, findings, and evidence.]

### System integrity
[Pass, findings, and evidence.]

### Verification and readiness
[Commands run, results, unverified paths, and findings.]

### Findings summary
[Counts by severity and classification.]

### Readiness
[Ready within the verified scope | Not ready]
[Blocking findings and explicit limitations.]
```

If no issues are found, say only that the feature is ready within the verified scope and list any untested environment paths. Do not claim universal production readiness.

Stop after the report. The developer decides which findings to address. A later fix request is a separate implementation task and must preserve its own authorization boundary.

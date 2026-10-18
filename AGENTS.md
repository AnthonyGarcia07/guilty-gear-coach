# Guilty Gear Coach Agent Instructions

These instructions apply to the entire repository.

Guilty Gear Coach is a React/TypeScript and FastAPI application for manual match tracking and evidence-grounded Guilty Gear Strive replay coaching. Its approved direction combines deterministic computer vision with multimodal LLM gameplay interpretation while keeping measured facts separate from AI-generated hypotheses. Prefer the simplest design that preserves correctness, ownership boundaries, evidence provenance, honest uncertainty, privacy, and the developer's ability to understand the code.

## Read Before Implementation

Read `README.md` and the relevant project context before making project changes. The repository and `README.md` describe the implemented application and local setup. The context files describe the approved product direction, architecture, standards, roadmap, and recorded status. If they disagree, inspect the code, report the discrepancy, and do not silently treat planned behavior as implemented.

For a complex or cross-cutting feature, read the context files in this order:

1. `context/project-overview.md`
2. `context/architecture.md`
3. `context/ui-tokens.md` when UI is involved
4. `context/ui-rules.md` when UI is involved
5. `context/ui-registry.md` when UI is involved
6. `context/code-standards.md`
7. `context/library-docs.md` when a third-party library is involved
8. `context/build-plan.md` for roadmap scope, dependencies, and acceptance criteria
9. `context/progress-tracker.md`

For focused work, read only the entries relevant to the task, but always use `context/progress-tracker.md` to distinguish implemented, active, next, and planned work. If a referenced file is missing, state that and use the repository, `README.md`, and remaining context as evidence rather than inventing its contents.

## Rules That Never Change

- Do not modify files during an analysis, audit, explanation, or guided-learning task unless the developer explicitly authorizes a specific change.
- Preserve existing behavior unless the approved task explicitly changes it.
- Prefer focused functions and direct control flow over speculative abstractions or additional architectural layers.
- Never commit secrets, credentials, tokens, connection strings, private object URLs, or real user replay data.
- Never expose storage credentials or administrative operations to browser code.
- Do not run migrations, destructive database commands, object-storage deletion, or other state-changing infrastructure operations unless they are explicitly required by the approved task.
- Before running backend integration tests, verify that they use a disposable database that is separate from development and production data. If isolation cannot be verified, do not run database-mutating tests.
- If the same problem remains after one evidence-based corrective attempt, stop making speculative changes and use `/recover`.
- Preserve unrelated user changes. Never reset, discard, or overwrite them without explicit approval.

## Project Architecture

### Frontend

- The frontend is React with TypeScript and Vite.
- Route-level screens live in `frontend/src/pages/`.
- Reusable interface elements live in `frontend/src/components/`.
- HTTP transport and response normalization live in `frontend/src/api/`.
- Authentication state lives in `frontend/src/auth/`.
- Shared frontend domain types live in `frontend/src/types.ts`.
- Keep server-authoritative validation in FastAPI even when the frontend duplicates rules for immediate feedback.
- Handle loading, empty, success, and failure states explicitly. A rejected request must not leave the UI in a permanent loading state.

### Backend

- The backend is FastAPI with SQLAlchemy, Alembic, Pydantic, and PostgreSQL.
- API route modules in `backend/app/api/routes/` own HTTP concerns: dependencies, status codes, request/response mapping, and authorization entry points.
- Pydantic schemas in `backend/app/schemas/` define and validate API contracts.
- SQLAlchemy models in `backend/app/models/` define persistence.
- Services in `backend/app/services/` own reusable business logic, storage operations, subprocess integration, and deterministic analysis.
- Route modules must not import implementation helpers from other route modules. Move shared behavior to a focused service or dependency module.
- Do not introduce a repository layer merely to wrap straightforward SQLAlchemy calls. Add a boundary only when it owns meaningful policy or coordination.
- Schema changes require an Alembic migration. Do not rewrite an applied migration to represent a new change.

### Ownership and Authorization

- User-owned replay access follows `Replay -> Match -> User`.
- Every match, replay, upload, download, inspection, sampling, and deletion path must enforce account ownership on the backend.
- Do not trust a frontend ownership check or a client-supplied owner identifier.
- Avoid revealing whether another user's resource exists; preserve the established not-found behavior for inaccessible resources.

### Replay Storage and Processing

- Cloudflare R2 is accessed through the S3-compatible storage service. The bucket remains private.
- FastAPI is the authorization and control plane; large MP4 bytes should travel directly between the browser and object storage when the existing presigned-URL flow supports it.
- Treat PostgreSQL rows and R2 objects as separate resources. For upload, confirmation, and deletion changes, reason explicitly about partial failure and recovery.
- Use temporary local workspaces for downloaded replay processing and ensure temporary artifacts are cleaned up.
- Preserve subprocess timeouts and safe public error messages for FFmpeg and `ffprobe` failures.
- Validate replay readiness and timestamps before downloading or processing video when possible.

### Deterministic Analysis

- Replay facts must come from deterministic processing. Do not present guesses or language-model output as measured gameplay evidence.
- Preserve the distinction between visual ambiguity and technical failure:
  - `unknown` means processing succeeded but evidence was inconclusive.
  - `failed` means extraction or detection failed technically.
- Preserve uncertainty ranges for sampled boundaries. Do not replace coarse evidence with false frame-level precision.
- Keep video inspection, frame extraction, HUD detection, timeline scanning, and gameplay-window inference independently testable.
- Threshold or calibration changes require evidence and regression tests; do not tune constants solely to satisfy one fixture.

### Multimodal Gameplay Analysis

- Multimodal LLM gameplay understanding is a core planned capability, not merely a prose layer over deterministic findings.
- A multimodal model may directly inspect authorized, bounded clips or sampled frames and propose descriptions, decision assessments, missed opportunities, possible punishes, alternative actions, outcome explanations, and practice priorities.
- Unless independently validated, generated interpretations are **AI coaching hypotheses**, not observations, measured facts, or deterministic findings. They may be uncertain or wrong and must communicate that uncertainty visibly.
- Preserve the provenance of supplied media, structured evidence, model and prompt versions, and any independent validation status.
- Keep deterministic results usable when multimodal processing is declined, unavailable, too costly, or fails. A provider failure must not overwrite or invalidate deterministic evidence.
- Send replay media to an external provider only through an approved backend flow with explicit privacy, consent, retention, and authorization rules. Never expose provider credentials or private object URLs to browser code.

## UI and Styling

- The project uses semantic CSS classes and `frontend/src/styles.css`.
- Reuse established component classes and visual patterns before adding new ones.
- Do not add one-off hardcoded color values to components. Use the CSS variables and documented tokens in `context/ui-tokens.md`.
- Treat `context/ui-registry.md` as the established reusable-pattern baseline. Do not turn a one-off implementation or an accidental inconsistency into a new standard.
- Maintain accessible labels, keyboard interaction, visible focus behavior, dialog semantics, and status/error messaging.
- Use `/imprint audit` for a deliberate consistency reassessment. Use `/imprint` only when a reusable visual or interaction pattern is introduced or materially changed.

## Third-Party Libraries

- Check the installed version before relying on remembered APIs.
- When an applicable installed skill exists, read and follow it before changing integration code.
- When `context/library-docs.md` exists, read its project-specific guidance for the library being changed.
- Prefer official documentation for version-sensitive behavior.
- Do not add, replace, or upgrade a dependency without explaining the need and receiving approval when the change expands project scope.

## Testing and Verification

- Add characterization or regression tests before risky refactoring.
- Prefer focused verification first, followed by the broader relevant suite.
- Frontend behavior should be protected with Vitest tests for validation, error handling, loading states, navigation, and important interactions.
- Backend pure services should be tested without network or object-storage access where practical.
- Mock R2/S3, FFmpeg, and `ffprobe` at appropriate boundaries unless an explicitly approved integration test needs the real dependency.
- Database integration tests must use an isolated disposable database and must not leave committed test records behind.
- Migration changes require upgrade verification and, when practical, downgrade or rollback analysis.
- Report commands run, results, and anything that could not be verified.

## Documentation and Progress

- Keep documentation concise and avoid duplicating the same source of truth across multiple files.
- Update `context/progress-tracker.md` after completing an implementation feature or changing recorded roadmap status. Do not mark planned work complete without implementation evidence and verification.
- Update `context/ui-registry.md` only when a reusable UI pattern is introduced or materially changed, not after every code change.
- Update `context/architecture.md` only when system boundaries or data flow actually change.
- Use `/remember save` for incomplete or multi-session work, meaningful unresolved decisions, or hard-won diagnostic context. It is not required after trivial tasks.

## Available Project Skills

- `/architect` — use before complex, cross-cutting, or architecturally meaningful implementation. Produce a plan and wait for approval before coding.
- `/imprint audit` — reassess the established UI consistency baseline without fixing issues automatically.
- `/imprint` — record a newly introduced or materially changed reusable UI pattern.
- `/review` — verify an implemented feature against its approved plan, project boundaries, tests, and intended environment. Report findings before fixing them.
- `/recover` — diagnose an unsuccessful implementation or repeated failure before attempting more changes. Never discard work automatically.
- `/remember save` — preserve non-sensitive handoff context for work that spans sessions.
- `/remember restore` — restore saved project context, summarize it, and wait for confirmation before continuing.

## Working With the Developer

- Explain important decisions in language a junior developer can follow without sacrificing technical accuracy.
- For guided learning, teach one logical section at a time and ask the developer to reason about it before providing the complete explanation.
- When diagnosing, identify the root cause before proposing a fix.
- When reviewing, separate confirmed defects from future concerns or optional improvements.
- Do not make an unrelated cleanup part of a focused task merely because you noticed it.

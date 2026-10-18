# Code Standards

Implementation standards for Guilty Gear Coach. These rules apply to new code and to existing code when it is changed. They are intended to improve the codebase gradually without turning focused work into unrelated refactoring.

The central standard is explainability: a developer should be able to identify where data enters, how it changes, what side effects occur, and what can fail without reverse-engineering hidden framework behavior or unnecessary abstractions.

---

## Engineering Mindset

- Understand the requested behavior and the existing execution path before editing code.
- Prefer direct, readable control flow over cleverness, indirection, or compressed syntax.
- Give each module and function a clear responsibility.
- Preserve established architecture and behavior unless the approved task changes them.
- Keep the change as small as correctness allows. Do not attach unrelated cleanup to a feature or bug fix.
- Make invalid states difficult to create, but do not add an abstraction merely to make the design appear sophisticated.
- Treat ownership, private replay data, deterministic evidence, and safe failure handling as correctness requirements.
- Add or update tests for meaningful behavior changes.
- If a developer cannot explain the implementation in plain language, simplify it before considering the work complete.

### AI-Generated Code Standard

AI-generated code must be understandable and explainable by a human maintainer. Before accepting generated code, verify that it can answer all of these questions:

1. What is the entry point?
2. What data enters, and what validates it?
3. How is the data transformed?
4. What does the code return or persist?
5. Which external systems or files does it touch?
6. What failures are expected, and where are they translated?
7. Which tests demonstrate the important behavior?

Generated code must not introduce generic factories, registries, base classes, decorators, dependency containers, event systems, or configuration layers unless the feature has a concrete need for them. “This may be useful later” is not sufficient justification.

---

## Before Implementation

- Read `README.md` and the context documents required by `AGENTS.md`.
- Trace the existing path through the frontend, API contract, route, service, and persistence layers as applicable.
- Check installed library versions before relying on remembered APIs.
- Search for an existing helper, semantic class, schema, or test pattern before creating another one.
- Identify authorization, database, R2, subprocess, and temporary-file side effects before changing the flow.
- For risky refactoring, first add characterization tests that preserve current behavior.
- Use `/architect` and wait for approval before complex, cross-cutting, or architecturally meaningful implementation.

---

## Change Scope and Existing Code

- Apply these standards to new and modified code; do not rewrite untouched areas only to make them conform.
- A focused change may improve nearby code when the improvement is necessary for correctness, testing, or clear ownership.
- Preserve public API contracts unless a contract change is explicitly approved.
- Preserve unrelated developer changes and existing migrations.
- Do not perform speculative cleanup, mass renaming, or broad formatting in a feature change.
- Record a larger issue for later when resolving it would expand the approved scope.

---

## Responsibilities and Boundaries

### Frontend

- `frontend/src/pages/` owns route-level composition and page state.
- `frontend/src/components/` owns reusable interface behavior and presentation.
- `frontend/src/api/` owns HTTP transport, authentication headers, response parsing, and API-error normalization.
- `frontend/src/auth/` owns authentication state and session restoration.
- `frontend/src/types.ts` owns domain types shared across frontend features.
- `frontend/src/constants/` owns stable frontend constants shared by multiple modules.
- `frontend/src/utils/` owns pure, reusable transformations and validation helpers.

Components must not build ad hoc fetch requests when the operation belongs in the shared API client. UI components must not know database, R2, or server filesystem details.

### Backend

- `backend/app/api/routes/` owns HTTP dependencies, authorization entry points, status codes, and request/response mapping.
- `backend/app/schemas/` owns Pydantic API contracts and contract validation.
- `backend/app/models/` owns SQLAlchemy persistence definitions and database constraints.
- `backend/app/services/` owns reusable business rules, deterministic analysis, storage integration, subprocess work, and other non-HTTP behavior.
- `backend/app/core/` owns configuration, database setup, and security primitives.

Route modules must not import implementation helpers from other route modules. When behavior is genuinely shared, move it to a focused service or dependency module. Do not add a repository layer that only forwards ordinary SQLAlchemy calls.

### Dependency Direction

Preferred dependencies flow inward toward domain behavior:

```text
frontend page -> component / api client -> FastAPI route -> schema / service -> model or external adapter
```

Pure analysis services should not import FastAPI, SQLAlchemy sessions, React concepts, or browser APIs. Framework-specific translation belongs at the boundary.

---

## Naming and File Organization

### TypeScript and React

- React component files use `PascalCase.tsx`.
- Utility, API, and test-helper files use descriptive `camelCase.ts` names.
- React components use `PascalCase`; hooks start with `use`; other functions and variables use `camelCase`.
- Constants use descriptive `camelCase` unless they are true module-level configuration constants, which may use `UPPER_SNAKE_CASE` when that improves visibility.
- Boolean names should read as conditions: `isLoading`, `hasReplay`, `canSubmit`.
- Event handlers should describe the event or action: `handleSubmit`, `handleDeleteReplay`.
- Prefer one primary exported component per file. Small private rendering helpers may stay beside it when extraction would make navigation harder.

The project does not currently define a TypeScript import alias. Use clear relative imports and do not introduce an alias as part of an unrelated task.

### Python

- Python modules, functions, and variables use `snake_case`.
- Classes and exceptions use `PascalCase`.
- Module constants use `UPPER_SNAKE_CASE`.
- Test functions use `test_<behavior>_<expected_result>` or another sentence-like name that clearly states the scenario.
- File names describe the owned capability, such as `video_inspection.py` or `replay_gameplay_windows.py`.

Choose domain names that match the product vocabulary in `ui-rules.md` and `architecture.md`. In particular, do not introduce additional ambiguity between matches, sets, games, and gameplay rounds.

---

## Readable Function Design

- A function should perform one coherent job at one level of abstraction.
- Prefer guard clauses for invalid input and unavailable state.
- Name intermediate values when they carry domain meaning or make a condition easier to read.
- Avoid deeply nested conditionals. Extract a named helper when a branch represents a distinct rule.
- Do not split a short, readable sequence into many pass-through helpers.
- Do not combine validation, persistence, external I/O, and response formatting in one helper merely to reduce line count.
- Prefer explicit parameters and return values over mutable module globals or implicit context.
- Mutate state only where ownership is clear. Pure transformations should return new values.
- Keep constants near the rule they configure. Shared calibration thresholds belong in an explicit threshold or configuration module.
- Do not hide important work in property accessors, decorators, import-time side effects, or constructors.

There is no arbitrary maximum function length. Length is a signal to examine responsibilities, not a rule to split code mechanically.

---

## TypeScript Standards

The frontend uses strict TypeScript. Preserve `strict: true` in `frontend/tsconfig.json`.

- Do not use `any`. Use a precise type or `unknown`, then narrow it.
- Exported functions should declare return types when the contract is not immediately obvious or is shared across modules.
- Component props should have a named type when there are multiple props or the type is reused.
- Use `type` for unions and ordinary object contracts. Use `interface` only when extension or declaration merging is intentional.
- Use `const` by default and `let` only for deliberate reassignment.
- Prefer discriminated unions for state or result variants that require different data.
- Avoid non-null assertions. Validate or guard the value instead.
- Use type assertions only at a trusted boundary or after a runtime check. If the reason is non-obvious, explain why the assertion is safe.
- Do not duplicate backend response shapes in local component types. Put shared frontend API/domain types in `types.ts`.
- Keep browser-only types and APIs out of code intended to be pure and testable.
- Do not leave promises unhandled. Await them or explicitly handle rejection.

### Formatting

- Use two-space indentation, double quotes, and semicolons, matching the current frontend.
- Break long JSX elements, function calls, and object literals across lines so their structure is visible.
- Avoid dense one-line handlers when validation, state changes, or failure behavior needs explanation through structure.
- Do not reformat unrelated files as part of a focused change.

The repository does not currently configure ESLint or a formatter. Adding one is a separate tooling decision, not a reason to invent commands or silently reformat the project.

---

## React Standards

- Keep render functions declarative. Move substantial transformations and reusable validation into named helpers.
- Store the minimum required state. Derive values during rendering when they are inexpensive and deterministic.
- Do not use an effect for a calculation that can be performed from props or state.
- Effects that start asynchronous work must handle rejection and prevent stale or abandoned work from updating the wrong screen.
- Every asynchronous view must represent loading, success, empty where applicable, and failure states.
- Use controlled form inputs when their values participate in validation or dependent UI.
- Prevent duplicate submissions and always clear busy state in both success and failure paths.
- Preserve user input after a rejected request unless clearing it is part of the successful workflow.
- Keep server validation authoritative even when the client provides immediate feedback.
- Use semantic HTML before ARIA. Add ARIA when native semantics do not express the required behavior.
- Use semantic CSS classes and the approved patterns in `ui-registry.md`; keep static styling out of JSX.
- Inline styles are acceptable only for genuinely runtime-derived values, such as a measured progress width.
- Revoke object URLs and clean up browser resources when a component no longer needs them.

### Component Order

A component file should generally read in this order:

1. External imports.
2. Internal imports.
3. Module constants and local types.
4. Small pure helpers.
5. The primary component.

Inside a component, group state, derived values, handlers, effects, and returned JSX in an order that makes the data flow easy to follow. This is guidance, not a reason to force every simple component into boilerplate.

---

## Frontend API Standards

- Add backend operations to `frontend/src/api/client.ts` or a focused API module if that file becomes meaningfully too broad.
- Keep token attachment, base-URL handling, response parsing, and normalized error creation inside the transport layer.
- UI code should receive typed data or a normalized error, not inspect arbitrary HTTP response shapes.
- Treat unexpected caught values as `unknown` and normalize them before showing a message.
- Never display raw server traces, storage keys, private object URLs, or subprocess output.
- For `204 No Content`, return an explicit `void` contract.
- Direct browser-to-R2 upload is the approved exception to ordinary API transport. The browser may receive a short-lived presigned URL, never storage credentials.
- Do not log bearer tokens, presigned URLs, replay contents, or personal account data.

---

## Python Standards

The backend targets Python 3.12.

- Use four-space indentation and standard Python naming.
- Add type annotations to public functions, service boundaries, dataclass fields, and non-obvious return values.
- Prefer built-in generics such as `list[str]` and union syntax such as `str | None`.
- Use `Literal` or enums when a closed set of values forms a meaningful contract.
- Use dataclasses for small structured service results when Pydantic or SQLAlchemy behavior is not required.
- Prefer frozen dataclasses for immutable analysis results.
- Do not use mutable default arguments.
- Use timezone-aware timestamps for stored or compared application times.
- Prefer `pathlib.Path` for filesystem paths.
- Do not use bare `except`. Catch the narrowest exception that can be handled meaningfully.
- If an exception is translated, preserve its cause with `raise ... from error`.
- Do not catch an exception only to return a misleading success value.

The repository does not currently configure Ruff, Black, mypy, or another Python static-analysis tool. Do not claim those checks ran. Adding tooling requires an approved change and should start with settings that do not force unrelated rewrites.

---

## FastAPI Route Standards

- Declare a Pydantic request schema for structured request bodies.
- Declare `response_model` for JSON responses when a schema exists.
- Use FastAPI dependencies for authentication, database sessions, settings, and replaceable external services.
- Enforce ownership before exposing or mutating a resource.
- Use the established not-found response for resources the current user cannot access.
- Validate inexpensive prerequisites before downloading replay data or starting subprocess work.
- Map domain or integration failures to intentional HTTP statuses and safe public messages.
- Keep reusable business rules and external integration details out of route functions.
- A route may coordinate a short transaction, but complex multi-resource workflows deserve a focused service boundary.
- Do not add a blanket `try/except` to every route. Catch only errors that the route can translate into an intentional API response.
- Do not return a generic `{ success, data }` wrapper unless the entire API contract is deliberately migrated. Preserve the current typed REST responses.

---

## Pydantic Schema Standards

- Schemas define the public API contract; SQLAlchemy models do not substitute for request validation.
- Put field bounds, lengths, and closed-value validation in schemas when they are part of the contract.
- Put cross-field validation near the schema or in a focused pure function shared by create and update flows.
- Separate create, update, read, and specialized-operation schemas when their allowed fields differ.
- Update schemas must distinguish an omitted field from an explicitly supplied null value.
- Read schemas may use `from_attributes` for ORM conversion.
- Never accept `owner_id`, trusted storage metadata, processing success, or other server-owned fields from the browser.
- When a contract changes, update frontend types and tests in the same feature.

---

## SQLAlchemy and Database Standards

- Scope every user-owned query to the authenticated owner on the backend.
- Replay ownership follows `Replay -> Match -> User`; do not authorize a replay by replay ID alone.
- Add database constraints for invariants that must remain true regardless of the caller.
- Use explicit ordering whenever response order affects behavior or tests.
- Avoid accidental N+1 queries when returning related collections, but do not add complex loading strategies without evidence.
- Keep transaction boundaries visible. Commit only after all required database changes for that unit of work are ready.
- If caught database work leaves a session in a failed transaction, roll it back before reuse.
- Refresh ORM objects only when server-generated or database-updated values are needed.
- Do not pass request-scoped sessions or ORM instances into future background workers; pass stable identifiers and open fresh resources.

### Migrations

- Every schema change requires a new Alembic migration.
- Never rewrite an applied migration to represent a later change.
- Give migrations descriptive revision names and preserve a single understandable upgrade path.
- Review existing data before adding non-null constraints or new validation constraints.
- Verify upgrades and analyze downgrade or rollback behavior when practical.
- Do not run a migration against development or production data without explicit authorization.

---

## Replay Storage and External I/O

- Keep the R2 bucket private and credentials on the backend.
- Use presigned URLs only for narrowly scoped, short-lived operations.
- Treat PostgreSQL records and R2 objects as separate resources with possible partial failure.
- Define the order of cross-resource operations deliberately and leave recoverable state when one side fails.
- Validate upload readiness, object metadata, file size, content type, replay ownership, and timestamps before expensive processing.
- Use a unique temporary workspace per processing operation and clean it up on success and failure.
- Use argument lists for subprocesses; do not construct shell command strings from user input.
- Preserve subprocess timeouts and bounded output handling.
- Convert FFmpeg, `ffprobe`, storage, and filesystem failures into safe public errors at the boundary.
- Never return local paths, raw subprocess output, credentials, or permanent object locations to the client.
- Mock R2, FFmpeg, and `ffprobe` at their service boundaries in ordinary tests.

---

## Deterministic Analysis Standards

- Replay facts come from deterministic processing, not from an LLM.
- Keep observation, gameplay event, finding, review moment, recommendation, and multimodal interpretation—including AI coaching hypotheses and explanations—as separate concepts.
- Preserve `unknown` for inconclusive processed evidence and `failed` for technical failure.
- Preserve sampled uncertainty ranges; do not manufacture exact timestamps.
- Return structured results with units and descriptive field names.
- Keep detection, extraction, timeline construction, and inference independently testable.
- Treat thresholds and calibration values as named configuration, not unexplained numbers embedded in branches.
- A threshold change requires evidence, regression coverage, and evaluation beyond one fixture.
- Do not mutate input timelines or evidence collections unless the function explicitly owns them.
- Retain enough provenance to reproduce a result when persistence for that stage exists.

### Multimodal LLM and Coaching Code

- Multimodal calls belong on the backend or in a worker; provider credentials never enter browser code.
- The model may directly inspect authorized gameplay clips or sampled frames and propose descriptions, decision assessments, missed opportunities or punishes, alternative actions, outcome explanations, and practice priorities.
- A generated interpretation does not need deterministic confirmation to be stored or shown as an AI coaching hypothesis, but it must never be promoted to an observation or deterministic finding without independent validation.
- Authorize every replay, frame, clip, and evidence identifier through `Replay -> Match -> User` before building a request.
- Send only the bounded derived media and structured context required for the approved coaching task.
- Treat private derived frames and clips as user-owned replay data. Clean up temporary artifacts and follow the approved provider disclosure, consent, retention, training, and deletion policy.
- Supply structured, evidence-linked inputs through an explicit allowlist and validate structured outputs before persistence or display.
- Reject or flag output that cites evidence identifiers not supplied to the model or states unavailable move, timing, frame-data, or resource claims as facts.
- Persist the provider, model, prompt version, supplied evidence identifiers, validated output, caveats, latency, cost metadata when available, and failure state.
- Enforce configured request timeout, retry, media-size, clip-duration, frame-count, and cost limits.
- Label generated output as interpretation, record whether it has independent validation, and never persist it as an observation or deterministic finding.
- A provider failure, refusal, malformed response, or lack of user consent must not invalidate completed deterministic processing.
- Introduce one focused adapter for the approved provider. Do not build a multi-provider framework before a second implementation or demonstrated test boundary requires it.

---

## Error Handling and Logging

- Handle an error where the code can recover, add meaningful context, clean up, or translate it for another boundary.
- Allow unexpected programming errors to fail visibly in development and tests.
- Never use empty catch or exception blocks.
- User-facing messages must be actionable and must not reveal sensitive implementation details.
- Domain and integration exceptions may expose a deliberately safe `public_message`; internal details belong in server logs.
- Use Python's `logging` module for backend diagnostics rather than `print` statements.
- Include operation and resource identifiers that help debugging, but exclude secrets, tokens, presigned URLs, and private replay content.
- Frontend console logging should be intentional and must not be the only user-visible failure handling.
- Cleanup belongs in `finally`, a context manager, or an ownership-specific cleanup function.
- Do not collapse partial success, ambiguity, or unavailable optional services into a generic failure state.

---

## Environment Variables and Secrets

Configuration is loaded through `backend/app/core/config.py` and the frontend's Vite environment.

| Variable | Exposure | Purpose |
| --- | --- | --- |
| `ENVIRONMENT` | Backend only | Runtime environment name |
| `DATABASE_URL` | Backend only | PostgreSQL connection |
| `SECRET_KEY` | Backend secret | JWT signing |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Backend only | Token lifetime |
| `S3_ENDPOINT_URL` | Backend only | R2 S3-compatible endpoint |
| `S3_BUCKET_NAME` | Backend only | Private replay bucket |
| `S3_REGION` | Backend only | S3-compatible region |
| `S3_ACCESS_KEY_ID` | Backend secret | R2 access key |
| `S3_SECRET_ACCESS_KEY` | Backend secret | R2 secret key |
| `S3_PRESIGNED_UPLOAD_EXPIRATION_SECONDS` | Backend only | Upload URL lifetime |
| `S3_PRESIGNED_DOWNLOAD_EXPIRATION_SECONDS` | Backend only | Download URL lifetime |
| `MAX_MP4_UPLOAD_SIZE_BYTES` | Backend only | Upload size limit |
| `VITE_API_URL` | Browser-visible | Public API base URL |

- Never hardcode production credentials, tokens, private URLs, or connection strings.
- Keep `.env.example` limited to safe placeholders and documented defaults.
- Any `VITE_` variable is browser-visible and must never contain a secret.
- Validate required production configuration at startup or before the capability is used.
- Do not print complete settings objects or environment contents.

---

## Comments and Documentation

- Prefer names and structure that explain what the code does.
- Comments should explain why a non-obvious decision, workaround, threshold, or ordering requirement exists.
- A short docstring is appropriate for a public service contract, a subtle algorithm, or behavior that callers must preserve.
- Do not narrate obvious syntax line by line.
- Do not leave vague TODO comments. Record actionable future work in the appropriate context or progress document.
- Keep comments current when behavior changes; stale explanations are defects.
- Include units in names or documentation, such as `duration_seconds` and `size_bytes`.
- Document whether a value is measured, inferred, user-entered, or generated when that distinction matters.

---

## Dependency Standards

- Do not add, replace, or upgrade a dependency without an approved need.
- First check whether the standard library, browser platform, React, FastAPI, SQLAlchemy, Pydantic, Pillow, or an existing dependency already provides the capability.
- Check the installed version and official documentation before using a version-sensitive API.
- Explain the dependency's responsibility, maintenance cost, security implications, and simpler alternatives.
- Pin backend dependencies consistently with `backend/requirements.txt`.
- Preserve the frontend lockfile when dependency work is approved.
- Do not add a framework, queue, cache, component library, state manager, or model runtime in anticipation of possible future scale.
- Remove a dependency only after confirming that source code, tests, build scripts, and runtime configuration no longer use it.

---

## Testing Standards

### General

- Test observable behavior and contracts rather than private implementation details.
- A bug fix should include a regression test that fails for the original defect when practical.
- Use descriptive test names and arrange tests so the scenario, action, and expected result are easy to see.
- Keep fixtures small and explicit. Avoid large shared fixtures that hide the important setup.
- Test expected failures and boundary values, not only the happy path.
- Run the narrowest relevant test first, then the broader affected suite.
- Report commands run, results, and anything not verified.

### Backend

- Use pytest for backend tests.
- Test pure services without a database, network, object storage, or real subprocess when practical.
- Mock storage and subprocesses at the adapter boundary, not deep inside the algorithm being tested.
- Route tests should cover authentication, ownership, validation, response status, and safe error mapping.
- Analysis tests must cover `ok`, `unknown`, and `failed` separately, including uncertainty boundaries.
- Before database-mutating tests, verify the database is disposable and separate from development and production data.
- Do not weaken a threshold or assertion solely to make one fixture pass.

### Frontend

- Use Vitest for frontend tests.
- Cover validation, loading, empty, success, failure, navigation, busy controls, and important accessibility behavior.
- Prefer rendering public output or calling exported pure helpers over inspecting component internals.
- Keep API transport tests focused on request construction, typed responses, and normalized failures.
- Run `npm run build` after TypeScript or production-bundle changes when practical; passing unit tests does not replace type checking.

### Typical Verification Commands

Run commands from the relevant project directory:

```text
backend:  pytest tests/<focused_test_file>.py
backend:  pytest
frontend: npm test -- <focused_test_file>
frontend: npm test
frontend: npm run build
```

Do not claim database, R2, FFmpeg, browser, or production-environment verification unless those dependencies were actually exercised in an approved environment.

---

## Definition of Done

A code change is complete when:

- The implementation matches the approved scope and architecture.
- Responsibilities and data flow are understandable without hidden behavior.
- Ownership and authorization are enforced on the backend.
- Loading, empty, success, and failure states are handled where applicable.
- Errors are translated safely without losing important distinctions.
- Temporary resources and busy states are cleaned up.
- Relevant tests pass, and production build or migration checks run when applicable.
- New dependencies, environment variables, migrations, and public contracts are documented.
- UI changes follow `ui-tokens.md`, `ui-rules.md`, and `ui-registry.md`.
- Deterministic analysis preserves repeatability, provenance, and uncertainty; multimodal analysis preserves source media, generated provenance, hypothesis labels, and caveats.
- Unrelated files and developer changes remain untouched.
- A junior developer can explain the entry point, transformations, side effects, failure paths, and tests.

---

## Do Not

- Do not optimize for fewer lines at the expense of readability.
- Do not introduce abstraction for hypothetical reuse.
- Do not hide network, database, storage, or subprocess work behind innocent-looking helpers.
- Do not trust client-supplied ownership or processing state.
- Do not expose credentials, storage keys, private URLs, local paths, or raw internal errors.
- Do not mix HTTP concerns into pure analysis services.
- Do not import reusable implementation behavior from another route module.
- Do not rewrite applied migrations.
- Do not run destructive or data-mutating infrastructure operations without explicit authorization.
- Do not treat `unknown` as `failed`, absent, false, or confirmed negative evidence.
- Do not present a multimodal model statement as an observed gameplay fact.
- Do not add a dependency or architecture layer merely because generated code commonly uses it.
- Do not leave rejected promises, permanent loading states, temporary files, or failed database sessions unhandled.

---

## Invariants

- FastAPI remains the authorization and control plane.
- User-owned access is enforced on the backend.
- Replay ownership follows `Replay -> Match -> User`.
- PostgreSQL stores structured state; R2 stores large private binary artifacts.
- Browser code never receives storage credentials or backend secrets.
- Route modules own HTTP behavior; services own reusable processing and integration behavior.
- Deterministic evidence remains separate from inference and generated interpretations, including AI coaching hypotheses and explanations.
- Technical failure remains distinct from visual ambiguity.
- Sampled analysis preserves uncertainty instead of claiming false precision.
- New code remains straightforward enough to test, debug, modify, and explain.

# Progress Tracker

Use this file to record implementation progress against `context/build-plan.md`. An agent or developer reading it should be able to identify the current roadmap position, the active implementation work, the next milestone, and the latest verification state without treating planned documentation as completed code.

The build plan owns milestone scope, dependencies, and acceptance criteria. This tracker owns status and concise implementation history.

---

## Current Status

| Status field | Current value |
| --- | --- |
| Roadmap position | Stage 1 — Current Implemented Baseline |
| Last completed stage | Stage 1 — Current Implemented Baseline |
| Active implementation | None recorded |
| Next recommended milestone | Stage 2 — Boundary Refinement and Evaluation Harness |
| First targeted replay-derived coaching finding | “The round appears to have ended while Burst was visually available.” |
| Status reviewed | 2026-10-17 |

Stage 1 is marked complete from repository inspection and existing project documentation. The automated suites were not rerun during this documentation pass, so this tracker does not claim a new green test run.

---

## Roadmap Progress

| Stage | Milestone | Status | Notes |
| ---: | --- | --- | --- |
| 1 | Current implemented baseline | Complete | Match tracking, manual coaching, private replay storage, media inspection, HUD detection, timeline scanning, and coarse gameplay windows exist |
| 2 | Boundary refinement and evaluation harness | Next | No implementation recorded; this is the next recommended engineering milestone |
| 3 | Durable analysis-run vertical slice | Not started | Requires Stage 2 contract and verified disposable database testing |
| 4 | Game and round segmentation | Not started | Depends on durable analysis runs and evaluated boundary evidence |
| 5 | Early multimodal gameplay-understanding prototype | Not started | May overlap Stage 4 only after Stage 3 privacy, persistence, and derived-media gates |
| 6 | First replay-derived coaching slice | Not started | Targets the round-end Burst review moment with evidence, optional AI hypotheses, and user feedback |
| 7 | Expand visual observations | Not started | Adds evaluated CV signals one at a time |
| 8 | Gameplay events and deterministic findings | Not started | Combines versioned observations through explicit rules |
| 9 | Move recognition, punish analysis, and alternatives | Not started | Requires stronger visual, timing, spatial, and patch-aware evidence |
| 10 | Cross-replay personalization and production hardening | Not started | Long-term aggregation, privacy, operations, and cost controls |

Statuses mean:

- **Complete:** implementation and its required verification are recorded as complete.
- **In progress:** an approved implementation task is actively underway.
- **Next:** recommended next work, not implementation already in progress.
- **Not started:** planned roadmap scope with no completed implementation recorded here.
- **Blocked:** progress cannot continue without a named decision, dependency, or external change.

---

## Implemented Baseline

### Application and Match Tracking

- [x] React, TypeScript, and Vite frontend
- [x] FastAPI, SQLAlchemy, Alembic, and PostgreSQL backend
- [x] Email/password authentication with JWT bearer tokens
- [x] Account-scoped match CRUD
- [x] Paginated and sortable match history
- [x] Dashboard statistics
- [x] Deterministic coaching from manually entered match history

### Replay Storage and Lifecycle

- [x] Multiple replay records per match
- [x] Private Cloudflare R2 storage through the S3-compatible API
- [x] Direct browser-to-R2 presigned MP4 upload
- [x] Backend upload confirmation using trusted object metadata
- [x] Authorized short-lived replay download URLs
- [x] Object cleanup when replay records or parent matches are deleted

### Replay Processing and Deterministic CV Foundation

- [x] `ffprobe` technical video inspection
- [x] FFmpeg frame extraction at explicit timestamps
- [x] Pillow-based combat-HUD measurements
- [x] `likely_gameplay_hud`, `not_gameplay_hud`, and `unknown` classification
- [x] Single- and multi-timestamp HUD detection
- [x] Internal HUD timeline scanning
- [x] Internal coarse gameplay-window inference with uncertainty ranges

### Not Yet Implemented

- [ ] Gameplay-window boundary refinement
- [ ] Durable analysis runs, background worker, or analysis persistence tables
- [ ] User-visible gameplay-window analysis results
- [ ] Game or round segmentation
- [ ] Health, Burst, Tension, timer, character, position, movement, animation, or candidate-move extraction
- [ ] Replay-derived gameplay events, deterministic findings, or coaching
- [ ] Multimodal provider integration or AI gameplay hypotheses
- [ ] Cross-replay personalization

---

## Next Milestone

### Stage 2 — Boundary Refinement and Evaluation Harness

**Goal:** refine existing coarse gameplay-window boundaries by sampling only within their uncertainty brackets, while preserving ambiguity and bounded processing.

Before marking Stage 2 in progress, record the approved implementation scope and confirm access to legally usable, manually reviewed transition clips or frames. Before marking it complete, satisfy the deliverables and acceptance criteria in `context/build-plan.md`, including:

- a versioned evaluation dataset and documented sampling configuration;
- a pure boundary-refinement service;
- explicit structured result types with units;
- bounded sampling and preserved subprocess timeouts;
- normal, ambiguous, failed, and resource-limited regression coverage; and
- evaluation output for boundary error, `unknown` rate, failure rate, and sampling cost.

The first implementation work is expected to center on:

- `backend/app/services/replay_gameplay_windows.py`
- `backend/app/services/replay_hud_timeline.py`
- `backend/app/services/frame_extraction.py`
- `backend/app/services/ggst_hud_detection.py`
- focused tests under `backend/tests/`

---

## Decisions Affecting Progress

- **2026-10-17 — Status-aware roadmap:** work follows the approved ten-stage roadmap, and `README.md` uses the same stage vocabulary.
- **2026-10-17 — First coaching slice:** the first targeted replay-derived finding is the uncertainty-aware round-end Burst review moment.
- **2026-10-17 — Complementary analysis paths:** deterministic CV and multimodal LLM gameplay understanding are both core product capabilities. CV produces measurable observations; the LLM may directly inspect authorized clips or frames and produce clearly labelled AI coaching hypotheses.
- **2026-10-17 — Per-run degradation:** multimodal analysis may be unavailable for consent, privacy, provider, latency, or cost reasons without invalidating deterministic results.
- **2026-10-17 — Initial worker direction:** the first durable analysis worker will use PostgreSQL coordination unless measured requirements justify a separate queue.

Record only decisions that change execution order, milestone status, or an unresolved implementation constraint. Architectural details remain in `context/architecture.md`.

---

## Prerequisites and Follow-Ups

- Obtain or define access to legally usable, labelled replay media for Stage 2 evaluation.
- Verify and document a disposable PostgreSQL test database before Stage 3 migrations or database-mutating worker tests.
- Resolve the route-to-route shared-helper boundary before adding Stage 3 analysis routes.
- Address permanent-loading and dialog-focus gaps before relying on new analysis UI flows.
- Decide provider, private-media consent, retention, training-use, deletion, latency, and cost policy before Stage 5 uses real user footage.
- Keep `README.md` synchronized with the approved roadmap and clearly distinguish implemented capabilities from planned work.

---

## Verification Log

| Date | Scope | Result | Notes |
| --- | --- | --- | --- |
| 2026-10-17 | Context-system documentation | Passed document checks | Markdown fences balanced, UTF-8 text preserved, final newlines present, and no trailing whitespace in audited context files |
| 2026-10-17 | Application tests | Not run | Documentation work only; existing coverage is described in `README.md` and Stage 1 of the build plan |

For implementation entries, record the exact commands run, their results, and anything that could not be verified. Do not write “tests pass” without a corresponding command or trusted CI result.

---

## Update Rules

Update this tracker after a completed implementation feature or whenever roadmap status materially changes:

1. Update **Current Status**.
2. Change only the affected row in **Roadmap Progress**.
3. Add or revise checklist items when implemented capability changes.
4. Record decisions only when they affect future execution.
5. Add verification commands and results to **Verification Log**.
6. Keep detailed requirements in `build-plan.md`; link to them instead of duplicating them here.
7. Never mark planned documentation, an experiment proposal, or an unverified assumption as completed implementation.


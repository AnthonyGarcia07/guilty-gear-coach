# Build Plan

Status-aware development roadmap for Guilty Gear Coach. This plan begins with the repository as it exists today and progresses toward a video-understanding AI coach through small, independently verifiable milestones.

This is not a deadline schedule. A later stage may begin experimental work early when its safety and data dependencies are satisfied, but no experimental result may bypass the evidence model or be presented as a verified gameplay fact.

The ten-stage roadmap and its first targeted replay-derived finding are approved product direction. That approval does not mean every stage is implemented or authorize an entire stage at once; each implementation task still needs a focused scope, its prerequisites, and proportionate verification.

---

## Core Principle

Guilty Gear Coach uses an evidence-first vertical-slice approach:

```text
deterministic service
  -> regression and evaluation tests
  -> persistence and API
  -> understandable UI
  -> user feedback
```

The roadmap is not completely sequential. Computer-vision development and multimodal LLM experimentation may proceed in parallel after the required privacy, extraction, persistence, and evaluation foundations exist. Both are core gameplay-understanding capabilities.

Multimodal gameplay understanding is an approved roadmap capability, not an uncommitted afterthought or a prose formatter for deterministic findings. It remains optional and degradable for an individual analysis run: deterministic evidence and review moments must still work when a user does not consent, a provider is unavailable, or cost and resource limits prevent generation. Optional per run does not make it secondary in the product vision.

The two paths complement each other:

```text
                         -> CV observations -> deterministic events and findings
gameplay clips/frames ---|
                         -> multimodal LLM -> AI coaching hypotheses

both paths -> evidence-linked review and practice recommendations
```

Computer vision independently measures HUD states, health, resources, positioning, movement, animations, and eventually candidate moves. The multimodal LLM directly examines actual bounded gameplay clips or sampled frames and attempts to interpret decision-making and tactical context.

The LLM is allowed to describe what appears to be happening, identify possible good or bad decisions, suggest missed opportunities or punishes, recommend alternatives, explain why a choice may have worked or failed, and propose practice priorities. These outputs may be uncertain or incorrect. That is acceptable for experimental AI coaching when the uncertainty and source are clear. An unvalidated interpretation is stored and displayed as an **AI coaching hypothesis**, not as a visual observation, deterministic finding, or verified fact.

These are planned roles. The current baseline has early deterministic HUD and gameplay-window processing but no multimodal provider integration, decision interpretation, or replay-derived coaching. Every future user-facing result must identify whether it came from CV measurement, deterministic rules, or multimodal generation.

---

## Product Target

The long-term goal is an AI-powered Guilty Gear Strive coach that can:

- inspect uploaded gameplay video;
- divide it into games, rounds, and important moments;
- identify supported gameplay observations and events;
- detect mistakes or missed opportunities when evidence is sufficient;
- compare a decision with supported alternatives;
- explain positioning, timing, character interaction, and gameplay context;
- use a multimodal LLM to inspect gameplay media and propose contextual decision, opportunity, alternative-action, and practice hypotheses;
- identify recurring strengths and weaknesses across replays; and
- connect feedback to timestamps, frames, or short clips.

The “Stockfish for Guilty Gear” description expresses the desired analytical usefulness, not a promise of chess-engine certainty. Fighting-game video is visually ambiguous, patch-dependent, and only partially observable. The product must communicate that uncertainty.

---

## Agreed Vocabulary

- **Build plan:** a status-aware roadmap beginning from the current repository, not a retrospective feature list or a calendar schedule.
- **Current baseline:** the implemented match tracker, manual coaching, private replay storage, media inspection, deterministic HUD detection, timeline scanning, and coarse gameplay-window inference.
- **Gameplay-boundary refinement:** denser sampling within existing uncertainty ranges. It does not mean detecting individual games or rounds.
- **Visual observation:** a direct measurement from video, including an explicit `unknown` result when the image is inconclusive.
- **Gameplay event:** a time-bounded change inferred from one or more observations.
- **Deterministic finding:** an explicit, versioned rule result supported by observations or events.
- **Review moment:** an evidence-linked situation worth inspecting that is not automatically labelled a mistake.
- **First replay-derived coaching slice:** round ranges, a deterministic Burst observation, an evidence-linked review moment, optional multimodal interpretation or coaching hypotheses, and user feedback.
- **AI coaching hypothesis:** an uncertain multimodal interpretation of gameplay, decisions, opportunities, alternatives, or practice needs. It is generated analysis, not a verified fact.
- **Multimodal gameplay interpretation:** generated analysis of supplied frames or clips plus structured context. It may contribute new coaching hypotheses as well as explain deterministic results.

### Result Status Semantics

- `ok`: processing succeeded and produced usable evidence.
- `unknown`: processing succeeded, but the visual evidence was inconclusive.
- `failed`: extraction, detection, or another technical operation failed.

These meanings remain distinct through persistence, APIs, tests, and UI copy.

---

## Roadmap Shape

The ten stages are:

| Stage | Name | Status or role |
| ---: | --- | --- |
| 1 | Current implemented baseline | Completed foundation |
| 2 | Boundary refinement and evaluation harness | First recommended engineering milestone |
| 3 | Durable analysis-run vertical slice | First persisted and user-visible analysis flow |
| 4 | Game and round segmentation | Structured gameplay hierarchy |
| 5 | Early multimodal gameplay-understanding prototype | Parallel experimental track after Stage 3 gates |
| 6 | First replay-derived coaching slice | First evidence-linked coaching experience |
| 7 | Expand visual observations | Broader deterministic CV signals |
| 8 | Gameplay events and deterministic findings | Rule-driven interpretation |
| 9 | Move recognition, punish analysis, and alternatives | Advanced, evidence-intensive analysis |
| 10 | Cross-replay personalization and production hardening | Long-term coaching usefulness and reliability |

### Dependency and Parallelism Map

```text
Stage 1: implemented baseline
  -> Stage 2: boundary refinement + evaluation
    -> Stage 3: durable analysis run + worker + user-visible windows
      -> Stage 4: game and round segmentation
      -> Stage 5: multimodal gameplay-understanding prototype
        Stage 4 + Stage 5
          -> Stage 6: first replay-derived coaching slice
            -> Stage 7: broader observations
              -> Stage 8: events and findings
                -> Stage 9: moves, punishes, alternatives
                  -> Stage 10: personalization and hardening
```

Stage 5 may overlap Stage 4 after Stage 3 establishes bounded derived media, privacy controls, persistent runs, and a backend-only provider boundary. Stage 5 does not need advanced move recognition, but it cannot publish unsupported gameplay facts.

---

## Evaluation Dimensions

Each milestone must say which kind of success it demonstrates. A passing unit test does not prove CV accuracy, and a useful coaching response does not prove factual correctness.

### Engineering Correctness

Measures whether the software behaves reliably:

- unit, route, integration, and UI tests;
- ownership and authorization coverage;
- transaction and partial-failure behavior;
- cleanup, retry, timeout, and cancellation behavior;
- deterministic serialization and API contracts; and
- absence of leaked secrets, private URLs, paths, or subprocess details.

### CV Detection Accuracy

Measures the visual analyzer against labeled evidence:

- precision and recall where positive/negative labels are meaningful;
- timestamp or boundary error ranges;
- `unknown` rate;
- technical failure rate;
- performance across resolution, compression, side, stage, effects, and characters; and
- regression results by analyzer and configuration version.

### Deterministic Analysis Reliability

Measures whether structured rules remain faithful to evidence:

- repeatability with the same replay and configuration;
- rule precision on reviewed fixtures;
- provenance completeness;
- unsupported-finding rate;
- correct handling of missing and ambiguous inputs; and
- stability across game-patch and rule versions.

### Multimodal Interpretation Quality

Measures the experimental model output against its source media and human review:

- whether descriptions correspond to the supplied clip or frames;
- whether decision assessments and proposed opportunities are plausible;
- whether alternatives respect supplied character, resource, position, and patch context;
- whether uncertainty and missing context are communicated;
- unsupported verified-fact rate;
- evidence-reference accuracy; and
- agreement and disagreement with knowledgeable human reviewers.

### Coaching Usefulness

Measures whether the output helps a player improve:

- user correctness feedback;
- usefulness ratings;
- expert review where available;
- evidence-reference accuracy;
- unsupported-claim rate;
- clarity of uncertainty; and
- whether suggested practice actions are specific and actionable.

Keep these scorecards separate. Do not average them into one number that hides the source of a failure.

---

## Stage 1 — Current Implemented Baseline

**Status:** Implemented. Preserve this behavior while future stages are built.

### What Exists

#### Application and match tracking

- React/TypeScript/Vite single-page frontend.
- FastAPI backend with PostgreSQL, SQLAlchemy, Alembic, and Pydantic.
- Email/password signup and login using JWT bearer tokens.
- Account-scoped match creation, reading, editing, and deletion.
- Paginated and sortable match history.
- Dashboard statistics and deterministic coaching from manual match data.
- Explicit loading, form validation, and destructive confirmation patterns, with known accessibility and failure-state gaps recorded elsewhere.

#### Replay storage and lifecycle

- Multiple replay records per match.
- Private Cloudflare R2 storage through an S3-compatible backend service.
- Direct browser-to-R2 MP4 upload with short-lived presigned PUT URLs.
- Backend confirmation using trusted object metadata.
- Authorized short-lived download URLs.
- Object cleanup when replay records or parent matches are deleted.

#### Replay processing and deterministic CV foundation

- `ffprobe` video metadata inspection.
- FFmpeg frame extraction at explicit timestamps.
- Pillow-based deterministic combat-HUD measurements.
- `likely_gameplay_hud`, `not_gameplay_hud`, and `unknown` classification.
- Single- and multi-timestamp HUD detection.
- Internal timestamp generation and replay HUD timeline scanning.
- Internal coarse gameplay-window inference with uncertainty ranges.

#### Automated verification

- Backend pytest coverage for match, coaching, replay, storage, media, HUD, timeline, and gameplay-window behavior.
- Frontend Vitest coverage for validation, error normalization, navigation helpers, pages, forms, dialogs, and replay UI output.

### Current Boundaries

- Gameplay-window refinement is not implemented.
- Internal timeline and gameplay-window results are not a durable user-facing analysis run.
- Individual games and rounds are not segmented.
- The system does not yet read health, Burst, Tension, timer, character identity, moves, or player inputs.
- Replay-derived gameplay events, findings, and coaching are not implemented.
- No LLM provider or multimodal model integration is installed.
- No background worker or analysis persistence tables exist.

### Important Concepts to Understand

- React page/component/API separation.
- FastAPI dependency injection and ownership enforcement.
- `Replay -> Match -> User` authorization.
- PostgreSQL record and R2 object lifecycle coordination.
- subprocess timeouts and safe public errors.
- deterministic measurements versus classifications.
- `unknown` versus `failed`.
- sampled boundary ranges rather than exact timestamps.

### Key Code Paths

- `frontend/src/api/client.ts`
- `frontend/src/components/ReplayMetadataSection.tsx`
- `backend/app/api/routes/replays.py`
- `backend/app/services/storage.py`
- `backend/app/services/video_inspection.py`
- `backend/app/services/frame_extraction.py`
- `backend/app/services/ggst_hud_detection.py`
- `backend/app/services/replay_hud_timeline.py`
- `backend/app/services/replay_gameplay_windows.py`

### Completion Condition

Stage 1 remains complete while its tests and ownership behavior continue to pass. Regression in the existing application blocks later feature release.

---

## Stage 2 — Boundary Refinement and Evaluation Harness

**Status:** Next recommended engineering milestone.

### Why This Comes First

The current pipeline already produces coarse gameplay-window ranges. Refining those ranges is the smallest reliable extension of implemented work, creates measurable improvement, and supplies stronger segment evidence for every later stage. It avoids prematurely introducing round detection, move recognition, or LLM claims.

### Dependencies

- Existing HUD detector, timeline scanner, and coarse gameplay-window inference.
- Legally usable replay clips or frames with manually reviewed gameplay transitions.
- A documented sampling configuration and acceptable resource bounds.

### Deliverables

1. A small versioned evaluation dataset containing:
   - replay or clip identifier;
   - source resolution, frame rate, and relevant game patch when known;
   - manually reviewed gameplay start and end ranges;
   - deliberately ambiguous transitions; and
   - expected technical failures where useful.
2. A pure boundary-refinement service that:
   - accepts an existing uncertainty bracket;
   - samples more densely only inside that bracket;
   - reuses the existing extraction and HUD-detection boundaries;
   - stops at a configured tolerance or sample limit; and
   - returns a refined range, not an unsupported exact timestamp.
3. Explicit configuration and result types with units in their field names.
4. Regression tests for normal, ambiguous, failed, and resource-limited refinement.
5. Evaluation output reporting boundary error, `unknown` rate, failure rate, and sampling cost.

### Acceptance Criteria

- The same replay and configuration produce the same refined range.
- Refined ranges never extend outside their validated coarse brackets.
- An inconclusive transition remains a wider or `unknown` range rather than becoming an exact boundary.
- Technical extraction failure remains distinguishable from visual ambiguity.
- Sampling has a hard upper bound and preserves subprocess timeouts.
- Representative fixtures improve or preserve boundary accuracy without tuning solely to one replay.

### Testing and Evaluation

- Unit tests for timestamp selection and stopping behavior.
- Service tests with mocked extraction and detector boundaries.
- Golden-clip evaluation in an approved media environment.
- Regression comparisons between coarse and refined ranges.
- Performance notes for samples, processing time, and worst-case bounds.

### Developer Learning Goals

- Trace data through timeline samples, window inference, and refinement.
- Explain why binary or adaptive sampling still returns uncertainty ranges.
- Understand dependency injection around FFmpeg and HUD detection.
- Distinguish algorithm tests from real-media evaluation.

### Primary Code Paths

- `backend/app/services/replay_gameplay_windows.py`
- `backend/app/services/replay_hud_timeline.py`
- `backend/app/services/frame_extraction.py`
- `backend/app/services/ggst_hud_detection.py`
- focused tests under `backend/tests/`
- future versioned evaluation fixtures outside committed private user data

### Completion Condition

Boundary refinement has a stable structured contract, bounded execution, regression tests, and evidence from representative labeled clips. It does not need persistence or UI to prove the algorithm, but its contract must be ready for Stage 3.

---

## Stage 3 — Durable Analysis-Run Vertical Slice

### Goal

Turn refined gameplay-window analysis into a durable, authorized workflow a user can request, monitor, and inspect without keeping a long HTTP request open.

### Dependencies

- Stage 2 structured refinement contract and evaluation baseline.
- Verified disposable database testing for new migrations and job-state behavior.
- Replay upload and metadata inspection must already be complete.

### Deliverables

1. Minimal persistence introduced through forward Alembic migrations:
   - `analysis_runs` for replay ownership, queued/running/completed/failed status, stage progress, versions, heartbeat, retry data, and safe failure details;
   - the smallest segment/result persistence needed for refined gameplay windows.
2. A PostgreSQL-backed worker that:
   - claims one queued run transactionally;
   - opens its own database session;
   - downloads the replay once to a unique temporary workspace;
   - runs metadata validation, coarse detection, and boundary refinement;
   - writes versioned results idempotently;
   - records progress and heartbeat; and
   - cleans temporary data on success and failure.
3. Authorized API operations to create a run and read its status/results.
4. Frontend controls and states for:
   - requesting analysis;
   - queued and processing progress;
   - completed refined gameplay windows;
   - empty or inconclusive results;
   - safe failure and retry.
5. Evidence links that let the UI request an authorized frame or bounded replay moment near a result.

### Acceptance Criteria

- Every operation enforces `AnalysisRun -> Replay -> Match -> User` ownership.
- Two workers cannot process the same run concurrently.
- A restart does not falsely mark a run complete or permanently strand it without recovery information.
- Retrying a run does not duplicate the run's own stage outputs.
- Results retain replay identity, analyzer version, configuration, and uncertainty ranges.
- A failed run exposes a safe public message while internal diagnostics remain server-side.
- The UI never remains permanently loading after a rejected request.

### Testing and Evaluation

- Pure worker-stage tests with mocked R2 and media adapters.
- Disposable PostgreSQL tests for job claiming, state transitions, heartbeat, retry, and ownership.
- Route tests for create/read/retry authorization and safe failure mapping.
- Frontend tests for queued, running, completed, inconclusive, failed, and retry states.
- One approved end-to-end run using a non-sensitive evaluation replay.

### Developer Learning Goals

- Understand request work versus background work.
- Explain session-per-worker and identifier-based job handoff.
- Trace job state from React to FastAPI, PostgreSQL, worker, result, and UI.
- Explain idempotency, heartbeat, retry, and cleanup.

### Primary Code Paths

- future `backend/app/models/analysis.py`
- future `backend/app/schemas/analysis.py`
- future `backend/app/api/routes/analysis.py`
- future `backend/app/services/analysis_runs.py`
- future worker entry point under `backend/app/` or `backend/scripts/`
- `backend/alembic/versions/`
- replay detail UI and frontend API/types

### Completion Condition

A user can request analysis of an owned uploaded replay, leave the request, return to its durable status, and inspect refined gameplay-window ranges after background completion.

---

## Stage 4 — Game and Round Segmentation

### Goal

Build a deterministic hierarchy from gameplay windows into games and rounds while preserving range uncertainty and source evidence.

### Dependencies

- Durable analysis runs and refined gameplay windows from Stage 3.
- Representative clips annotated with game and round boundaries.
- A clear GGST set/game/round vocabulary and patch context.

### Deliverables

- Independent game-boundary and round-boundary analyzers.
- Versioned `analysis_segments` persistence for gameplay, game, and round ranges.
- Segment relationships that express containment without assuming perfect boundaries.
- Visual observations for round transitions or round markers sufficient to support segmentation.
- UI hierarchy for games, rounds, ranges, confidence, and evidence access.
- Manual correction or feedback capture for obviously wrong or ambiguous segments.

### Acceptance Criteria

- Gameplay-boundary, game-boundary, and round-boundary results remain separate.
- Every segment records its source run, analyzer/configuration version, range, status, confidence where meaningful, and supporting evidence references.
- A segment may be `unknown` without failing the entire run.
- Missing round evidence does not cause invented segments.
- Parent and child ranges remain internally consistent.
- UI wording does not imply exact frame precision when the evidence is sampled.

### Testing and Evaluation

- Pure segmentation tests for standard, incomplete, ambiguous, and interrupted footage.
- Golden clips covering multiple games, skipped intros, rematches, transitions, and compression levels.
- Boundary error and segment-count evaluation.
- Persistence and API tests for hierarchy, ownership, and versioning.
- UI tests for nested segments and ambiguous states.

### Developer Learning Goals

- Model hierarchical time ranges without false precision.
- Separate visual observation from temporal inference.
- Understand database representation of versioned, evidence-linked segments.
- Explain how a user correction differs from changing measured evidence.

### Completion Condition

Supported replays display evidence-linked game and round ranges with measured accuracy and honest ambiguity. No coaching judgment is required yet.

---

## Stage 5 — Early Multimodal Gameplay-Understanding Prototype

**Parallelism:** May begin after Stage 3 privacy and derived-media gates while Stage 4 segmentation continues.

### Goal

Evaluate whether a multimodal LLM can directly inspect bounded gameplay clips or sampled frames and produce useful, evidence-aware interpretations of player decisions and coaching opportunities. The prototype is allowed to go beyond restating deterministic findings, provided its independent interpretations remain labelled as hypotheses.

### Required Decisions Before Implementation

- Provider and model capability.
- Whether the provider retains inputs or uses them for training.
- User disclosure and consent for sending private derived media to a third party.
- Maximum clip length, frame count, request size, latency, and cost.
- Data deletion and audit expectations.
- Whether experiments run only on approved evaluation clips before user replays.

### Dependencies

- Backend-only provider adapter boundary.
- Durable analysis-run identity and evidence references.
- Authorized generation of short clips or selected frames.
- Privacy review and explicit user-facing disclosure.
- A labeled evaluation set with human-reviewed source moments.

### Deliverables

- A provider-neutral request and response contract owned by the application.
- A single backend adapter for the approved initial provider.
- Structured inputs containing:
  - selected frames or a short authorized clip;
  - replay/segment timestamps;
  - verified observations;
  - explicit unknowns and unavailable facts; and
  - allowed evidence identifiers.
- A validated structured response separating:
  - what appears to be happening in the supplied media;
  - possible good or bad decisions;
  - potential missed opportunities or punishes;
  - possible alternative actions;
  - why a decision may have worked or failed;
  - suggested practice priorities;
  - caveats; and
  - cited evidence identifiers.
- Persistence of provider, model, prompt version, supplied evidence IDs, validated output, latency, cost metadata where available, and failure state.
- An internal or clearly experimental UI that labels output as generated interpretation.

### Acceptance Criteria

- Provider credentials never enter browser code.
- Only authorized bounded media is sent.
- The model cannot cite an evidence identifier that was not supplied.
- The model may contribute a coaching hypothesis that no deterministic rule produced, and the product preserves its generated provenance.
- An interpretation does not require deterministic confirmation to appear as a hypothesis, but it cannot appear as a verified observation or finding without independent validation.
- Unsupported move identity, frame data, or punish claims are rejected, flagged, or clearly labelled as hypotheses.
- Provider failure leaves deterministic results intact.
- The prototype reports latency, cost, evidence-faithfulness, and unsupported-claim rate.
- Generated output is never stored as an observation or deterministic finding.

### Testing and Evaluation

- Adapter contract tests with recorded or mocked provider responses.
- Schema-validation and invalid-citation tests.
- Privacy and authorization tests for derived-media access.
- Human review against the source clips.
- Separate review of description accuracy, decision plausibility, alternative validity, uncertainty communication, and coaching usefulness.
- Prompt-version comparisons using the same evaluation inputs.
- Failure tests for timeout, malformed output, refusal, unavailable provider, and partial response.

### Developer Learning Goals

- Explain adapter boundaries without creating unnecessary provider abstractions.
- Understand structured-output validation and evidence allowlists.
- Trace private media from R2 to temporary artifact to provider and cleanup.
- Distinguish model usefulness from factual accuracy.

### Completion Condition

The team has evidence about whether the selected model can usefully interpret gameplay decisions and coaching opportunities while remaining honest about uncertainty, faithful to supplied media, affordable, and acceptable for private video. The prototype does not need to be enabled for ordinary users and does not block deterministic analysis progress.

---

## Stage 6 — First Replay-Derived Coaching Slice

### Target Finding

> The round appears to have ended while Burst was visually available.

This is a **review moment**, not automatically a confirmed mistake. The player may have had valid reasons not to Burst, the visual detector may be uncertain, and relevant tactical context may be missing.

### Why This Slice

- Burst is a visible resource with meaningful coaching value.
- The finding builds on round segmentation without requiring comprehensive move recognition.
- The claim can remain narrow and evidence-linked.
- It creates a complete path from video to feedback while preserving uncertainty.

### Dependencies

- Durable analysis runs and evidence references.
- Supported round-end ranges from Stage 4.
- A deterministic Burst-availability observation with measured accuracy.
- Optional Stage 5 gameplay-understanding capability that has passed privacy and faithfulness gates.

### Deliverables

1. A versioned Burst observation service that records visible availability, `unknown`, or technical failure near a round-end range.
2. A deterministic rule that creates a review moment only when its required evidence is present.
3. Persistence linking the review moment to:
   - the analysis run;
   - round segment;
   - supporting observations;
   - timestamps or ranges;
   - analyzer and rule versions; and
   - confidence and caveats.
4. A user-facing review card with:
   - precise non-accusatory wording;
   - an authorized frame or clip link;
   - measured evidence separated from interpretation;
   - optional multimodal interpretation or coaching hypothesis; and
   - correctness and usefulness feedback controls.
5. A drill or review suggestion that does not depend on invented move facts.

### Acceptance Criteria

- The deterministic rule never fires from an `unknown` or failed Burst observation.
- The UI says “appears” or equivalent uncertainty-aware language unless evidence supports stronger wording.
- The user can open the supporting moment.
- Optional multimodal interpretation cites only supplied media or evidence and is visually distinct from the deterministic review moment.
- The LLM may add contextual possibilities, decision reasoning, alternatives, or practice suggestions without changing the deterministic Burst result.
- LLM failure does not hide or invalidate the deterministic result.
- User feedback is stored separately from the analyzer output.
- False-positive rate and usefulness are reported separately.

### Testing and Evaluation

- Labeled Burst-visible, Burst-unavailable, obscured, transition, and failed-frame fixtures.
- Detector precision/recall and `unknown` rate.
- Rule tests covering every status combination.
- Persistence and ownership tests.
- UI tests for evidence, caveats, generated labels, feedback, and provider failure.
- Human review of whether the moment is correctly stated and useful.

### Developer Learning Goals

- Trace one complete feature from pixels to observation, rule, API, UI, and feedback.
- Explain why a review moment is not identical to a mistake.
- Separate detector accuracy, rule correctness, and coaching usefulness.
- Understand how optional generated language depends on—but does not overwrite—deterministic evidence.

### Completion Condition

At least one supported replay can produce a trustworthy, timestamped round-end Burst review moment with inspectable evidence, optional bounded multimodal interpretation, and user feedback.

---

## Stage 7 — Expand Visual Observations

### Goal

Add independently testable observations that increase coaching coverage without coupling all CV work into one opaque analyzer.

### Candidate Order

Implement one signal at a time based on visibility, labeled-data availability, expected coaching value, and evaluation cost:

1. Round result and round markers.
2. Health estimates and major health changes.
3. Burst state across a round.
4. Tension/resource estimates.
5. Timer region and coarse timer state.
6. Character identity and player side.
7. Coarse screen position, corner state, and movement.
8. Animation or candidate action descriptors.

The exact order may change after evaluation. Do not bundle these into one milestone merely because they share frames.

### Deliverables Per Observation

- A versioned input/output contract.
- Named regions, units, thresholds, and configuration.
- `ok`, `unknown`, and `failed` behavior.
- Representative labeled fixtures.
- Precision/recall or error metrics appropriate to the signal.
- Structured persistence with timestamps and evidence references.
- UI display only when the value helps users or debugging.

### Acceptance Criteria

- Each observation can be evaluated and rerun independently.
- One detector's failure does not erase unrelated completed observations.
- Calibration changes retain version identity and regression history.
- Character, stage, side, effects, resolution, and compression coverage expands with the supported claim set.
- The product does not imply support outside evaluated conditions.

### Developer Learning Goals

- Build and test one CV responsibility at a time.
- Select metrics that fit continuous, categorical, and ambiguous outputs.
- Understand calibration datasets and versioned configuration.
- Explain why a reusable frame pipeline does not require one monolithic detector.

### Completion Condition

The system has a documented set of supported, evaluated observations sufficient to infer a small collection of reliable gameplay events.

---

## Stage 8 — Gameplay Events and Deterministic Findings

### Goal

Combine observations over time into explicit events, then apply versioned Guilty Gear rules to produce evidence-backed findings and recommendations.

### Candidate Events

- damage or major health swing;
- resource gain or expenditure;
- round start and round end;
- entering or leaving the corner;
- knockdown or advantage-state candidate;
- Burst use or retained Burst;
- major position change; and
- candidate hit, block, or whiff when evidence supports it.

### Candidate Findings

- repeated resource retention at round end;
- recurring damage taken near the corner;
- repeated health losses after a supported situation type;
- possible missed defensive-resource review moments; and
- repeated patterns that merit manual replay review.

### Dependencies

- Versioned observations from Stage 7.
- Patch-aware domain rules where game mechanics affect interpretation.
- Labeled sequences, not only individual frames.

### Deliverables

- Event contracts with start/end ranges, actor where known, confidence, and observation references.
- Versioned deterministic rule definitions.
- Finding and recommendation persistence separated from observations and events.
- Evidence-linked UI timelines and coaching summaries.
- User confirmation, rejection, correction, and usefulness feedback.
- Evaluation reports for event accuracy and rule precision.

### Acceptance Criteria

- Events cannot cite nonexistent or inaccessible observations.
- Findings state the rule and evidence version that produced them.
- A low-confidence event cannot silently become a high-confidence finding.
- Findings remain reproducible for the same run, configuration, patch data, and rule version.
- Recommendations describe practice actions without claiming unavailable tactical certainty.

### Testing and Evaluation

- Sequence-based golden fixtures.
- Rule-table tests for required, optional, contradictory, unknown, and failed evidence.
- Provenance integrity tests.
- Patch-version regression tests where applicable.
- UI tests for event/finding/evidence separation.
- Expert or knowledgeable-player review of finding precision.

### Developer Learning Goals

- Distinguish temporal inference from direct measurement.
- Design explainable rule engines without overgeneralized frameworks.
- Trace a recommendation back to its evidence.
- Understand patch-aware domain data and reproducibility.

### Completion Condition

The application can generate multiple independently testable replay-derived findings whose supporting events and observations are inspectable by a developer and player.

---

## Stage 9 — Move Recognition, Punish Analysis, and Alternatives

### Goal

Progress from coarse action evidence toward candidate move identities, possible punish opportunities, and supported alternatives without claiming certainty the video cannot provide.

### Prerequisites

- Reliable character identity, player side, round timing, and spatial context.
- Frame- or sequence-level action descriptors with labeled data.
- Versioned GGST patch and frame-data sources with verified licensing and reliability.
- Known timing error bounds from video frame rate, sampling, and detector latency.
- A large enough evaluation set to measure false punish claims.

### Milestone Progression

1. **Candidate action classes** — movement, attack, block, hit, knockdown, wake-up, or resource action.
2. **Character-specific candidate moves** — ranked candidates with confidence and supporting visual sequence.
3. **Situation reconstruction** — spacing, side, timing range, hit/block/whiff candidate, and available resources.
4. **Possible punish windows** — only when move identity, outcome, timing, and distance evidence satisfy a versioned rule.
5. **Supported alternatives** — options compatible with the known character, resources, position, and timing range.
6. **Generated gameplay interpretation** — the multimodal LLM independently examines the supplied sequence and may assess the decision, identify a possible punish or missed opportunity, propose alternatives, explain the outcome, and suggest practice without upgrading hypotheses to facts.

### Deliverables

- Model or deterministic recognizer evaluation artifacts and versioning.
- Candidate outputs rather than forced single-label certainty.
- Patch-aware move and frame-data store with sources and review status.
- Punish-opportunity rules with timing tolerances and evidence requirements.
- Alternative-action ranking that exposes assumptions.
- UI that distinguishes observed, candidate, inferred, deterministic, and generated content.

### Acceptance Criteria

- Unsupported exact move names are not displayed as confirmed.
- A punish finding requires explicit evidence for the opponent action, outcome, timing window, player capability, and relevant position/resource assumptions.
- Frame-data versions are traceable to game patches and sources.
- False-positive punish claims remain within an agreed reviewed threshold before user release.
- Recommended alternatives include their evidence and limitations.
- The LLM may propose uncertain punish or alternative hypotheses from the video, but it cannot present invented frame advantage, exact timing, or legal options outside supplied domain data as verified facts.

### Testing and Evaluation

- Character-, side-, stage-, compression-, and patch-diverse labeled clips.
- Top-k move candidate accuracy and calibration.
- Timing-error analysis.
- Punish-rule precision and false-positive review.
- Alternative validity review by knowledgeable players.
- Adversarial LLM tests for unsupported move names, frame data, and certainty.

### Developer Learning Goals

- Understand supervised visual evaluation and calibration.
- Model candidate identity rather than forcing certainty.
- Combine domain data, timing ranges, and visual evidence.
- Explain why missed-punish detection is a multi-signal problem.

### Completion Condition

The system can identify a deliberately limited set of supported character situations and produce reviewed, evidence-linked punish or alternative suggestions with clearly bounded uncertainty.

---

## Stage 10 — Cross-Replay Personalization and Production Hardening

### Goal

Turn isolated findings into reliable personalized coaching while making the system safe, observable, recoverable, and economically sustainable.

### Personalized Coaching Deliverables

- Aggregate findings by player character, opponent character, patch, situation, and time period.
- Detect recurring patterns only after a documented minimum evidence threshold.
- Separate strengths, weaknesses, habits, and uncertain hypotheses.
- Rank practice priorities using frequency, severity, confidence, recency, and user feedback.
- Generate drills, coaching hypotheses, and explanations grounded in authorized source media and persisted evidence.
- Let users correct findings and indicate usefulness.
- Show when the sample is too small for a strong conclusion.

### Production Reliability Deliverables

- Bounded worker concurrency, retries, and resource quotas.
- Stale-job recovery and operational visibility.
- Cost, latency, and provider-failure monitoring.
- Storage lifecycle policies for source replays and derived artifacts.
- Privacy controls, retention policy, deletion propagation, and provider disclosures.
- Analyzer, rule, model, prompt, and game-data version auditability.
- Secure deployment configuration and secret rotation.
- Performance testing using realistic replay sizes.
- Backup, restoration, and migration procedures appropriate to deployment scope.

### Acceptance Criteria

- Personalized claims cite the runs and findings supporting them.
- Low sample sizes and contradictory evidence remain visible.
- User deletion removes or invalidates owned derived artifacts according to policy.
- Provider outages degrade generated interpretations without losing deterministic results.
- Resource limits prevent one replay from exhausting worker capacity.
- Operational metrics distinguish technical failure, unknown evidence, low-confidence findings, and provider failure.
- Costs and latency remain within agreed product budgets.

### Testing and Evaluation

- Aggregation and minimum-sample tests.
- Ownership and deletion tests across database, R2, derived media, and provider records where applicable.
- Load and resource-limit tests.
- Recovery drills for worker termination and stale jobs.
- Security review of replay access and provider integration.
- Longitudinal usefulness evaluation with user feedback.

### Developer Learning Goals

- Explain aggregation without overstating trends.
- Understand operational limits, privacy lifecycle, and graceful degradation.
- Trace a personalized recommendation back through findings, events, observations, and source replay moments.
- Discuss engineering tradeoffs between reliability, accuracy, usefulness, cost, and complexity.

### Completion Condition

The product provides evidence-grounded personalized coaching across replays and operates within documented privacy, reliability, performance, and cost constraints.

---

## Technical-Debt Gates

These items should be addressed when they become prerequisites for a milestone. They do not authorize a general refactoring phase.

| Issue | Required before | Reason |
| --- | --- | --- |
| Verify and document a disposable PostgreSQL test database | Stage 3 migrations and worker tests | Prevent tests from mutating development or production data |
| Move shared route behavior out of route-to-route imports | Stage 3 analysis routes | Preserve backend ownership boundaries |
| Add failure states to load-only frontend effects | Stage 3 analysis UI | New analysis views must not repeat permanent-loading behavior |
| Complete dialog focus management and visible focus styles | User-facing Stage 3/6 workflows | Analysis and destructive actions must be keyboard accessible |
| Recover interrupted or abandoned replay uploads | Before large-scale analysis requests | Avoid analyzing incomplete or orphaned storage state |
| Decide explicit frontend version policy instead of relying on `latest` | Before major frontend dependency work | Improve reproducibility and upgrade safety |
| Pin directly imported Pydantic behavior | Before version-sensitive schema expansion | Make API validation behavior reproducible |
| Record FFmpeg/`ffprobe` versions in evaluation output | Stage 2 real-media evaluation | Media behavior may vary by executable version |
| Add browser-capable interaction testing when required | Before claiming focus/clip-control behavior is covered | Static rendering cannot prove browser interactions |
| Adopt documented UI tokens during touched UI work | Stages 3, 4, and 6 UI | Prevent visual drift without unrelated redesign |

---

## Cross-Cutting Security and Privacy Rules

- Every match, replay, analysis run, segment, observation, finding, clip, frame, generated interpretation, feedback record, and deletion path enforces backend ownership.
- R2 remains private. Derived clips and frames inherit the source replay's ownership.
- Presigned URLs remain short-lived capabilities and are not logged or persisted unnecessarily.
- Provider credentials stay on the backend or worker.
- User replay media is not sent to a third-party model without an explicit product decision, disclosure, and retention review.
- Logs exclude tokens, credentials, presigned URLs, local paths, raw subprocess output, and private replay contents.
- File size, duration, frame count, sample count, clip length, concurrency, and provider request limits are enforced before expensive work.
- Deletion design covers PostgreSQL, R2, derived artifacts, and external provider retention where applicable.

---

## Evaluation Dataset Rules

- Use legally usable clips with permission appropriate to development and evaluation.
- Do not commit real private user replays to the repository.
- Store only the smallest fixtures practical in version control; keep larger private evaluation media in access-controlled storage.
- Record game patch, resolution, frame rate, compression, character, side, stage, and relevant visual effects when known.
- Include clear positive, clear negative, ambiguous, and technical-failure examples.
- Preserve human labels, reviewer identity or role, review date, and tolerance ranges.
- Version datasets and analyzer configuration together in evaluation reports.
- Do not tune a threshold solely to improve one fixture.
- Add new failure cases to regression coverage when legally and technically practical.

---

## Major Decision Gates

These decisions remain intentionally unresolved until their stage needs them:

### Multimodal provider and model

Choose based on video/frame support, structured output, privacy terms, retention controls, latency, cost, reliability, and evaluation performance. Do not select a provider solely because it is familiar.

### User media consent and retention

Decide whether multimodal processing is opt-in, what derived media leaves project infrastructure, how long providers retain it, and how deletion is communicated and enforced.

### Evaluation data acquisition

Define how labeled clips are obtained, licensed, stored, reviewed, and shared among developers without exposing private user data.

### Worker deployment

The first worker uses PostgreSQL coordination. Process layout, host separation, concurrency, and compute/GPU requirements should follow measured workload rather than anticipation.

### CV model runtime

Pillow remains suitable for current deterministic measurements. Add OpenCV, ONNX Runtime, PyTorch, or another runtime only when a specific evaluated detector requires it.

### GGST domain data

Before punish analysis, choose reliable and legally usable patch-specific character/move/frame data, including versioning and review policy.

### Supported replay conditions

Define and publish which resolutions, frame rates, layouts, patches, capture styles, and video qualities are considered supported as evidence accumulates.

---

## Milestone Completion Checklist

Before marking a future milestone complete:

- The approved deliverables exist without unrelated scope expansion.
- Data flow, side effects, and failure paths are explainable.
- Ownership and private-media rules are enforced on the backend.
- `ok`, `unknown`, and `failed` remain distinct.
- Observations, events, findings, recommendations, and generated interpretations—including AI coaching hypotheses and explanations—remain separate.
- Relevant unit, integration, route, UI, and evaluation checks pass.
- Real-media claims are supported by representative labeled clips.
- Analyzer, configuration, rule, model, prompt, and game-data versions are retained where applicable.
- Latency, resource use, and cost are measured when the milestone adds expensive processing.
- The UI exposes evidence and uncertainty instead of false precision.
- Documentation and the progress tracker are updated.
- A junior developer can explain the important code paths and verify the result independently.

---

## What Not to Build Prematurely

- A generic microservice architecture.
- A message broker before PostgreSQL-backed work proves insufficient.
- Live gameplay capture, WebRTC, or real-time overlays.
- Broad move recognition before character, timing, spatial, and evaluation foundations exist.
- LLM-generated punish interpretations presented as verified facts without independent validation.
- Public replay hosting or permanent public URLs.
- A large future schema before the next vertical slice needs each table.
- A provider abstraction with multiple unused implementations.
- GPU infrastructure before a measured model workload requires it.
- A social platform, subscription system, or native mobile client.

These may become valid later, but they must not distort the post-match evidence pipeline being built now.

---

## Interview-Level System Explanation Target

As the roadmap progresses, the developer should be able to explain the system in this form:

> Guilty Gear Coach keeps uploaded replays private in R2 and uses FastAPI as the authorization and control plane. A background worker downloads an owned replay into a temporary workspace. Computer vision extracts versioned measurements with uncertainty, while a multimodal language model directly examines authorized clips or frames and proposes contextual gameplay and coaching hypotheses. Deterministic rules produce reproducible findings from supported observations. The frontend shows the source timestamp, frame, or clip and distinguishes measured evidence, deterministic findings, and AI-generated hypotheses. Tests and labelled replay clips evaluate software correctness, CV accuracy, deterministic rule reliability, multimodal interpretation quality, and coaching usefulness as separate concerns.

That explanation should remain true as capabilities grow.

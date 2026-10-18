# Project Overview

## About the Project

Guilty Gear Coach is a full-stack match tracking and evidence-grounded replay-coaching application for **Guilty Gear Strive** players.

The project began as a way to help my brother review his matches more efficiently. Its long-term direction combines deterministic computer vision, versioned gameplay rules, and multimodal LLM gameplay understanding to turn uploaded footage into useful practice recommendations without confusing generated interpretation with measured facts.

The intended analysis model has two complementary paths:

```text
                             -> CV measurements and observations
uploaded gameplay video ----> deterministic events, findings, and review moments
                         |
                         +---> multimodal LLM video interpretation
                               -> AI-generated gameplay hypotheses and coaching ideas

both paths -> evidence-linked player review and practice recommendations
```

The application currently combines a usable manual match tracker with the early technical foundations of replay analysis. It is not yet a complete gameplay-understanding system.

---

## The Problem It Solves

Improving at a fighting game requires more than remembering whether a set was won or lost. Players need to notice repeated mistakes, weak matchups, resource habits, missed defensive options, and practice priorities across many matches.

Manual review is valuable but time-consuming. Video alone also does not provide structured evidence that can be searched, compared, or summarized.

Guilty Gear Coach addresses this in two broad phases:

1. **Today:** help players record match context and derive deterministic coaching patterns from their own notes and results.
2. **Long term:** analyze uploaded gameplay footage through three coordinated product tracks:
   - deterministic computer vision produces observations and uncertainty-aware segments;
   - versioned rules turn supported observations into events, findings, review moments, and recommendations; and
   - a multimodal LLM directly examines bounded gameplay clips or sampled frames, interprets player decisions, and proposes contextual coaching hypotheses without becoming the source of measured facts.

Computer vision and multimodal LLM gameplay understanding are both core product capabilities. The LLM is not restricted to rewriting deterministic findings: it may identify possible good or bad decisions, missed opportunities or punishes, alternative actions, reasons a choice may have worked or failed, and practice priorities directly from authorized video evidence. Those interpretations may be useful even when uncertain or incorrect, but they must remain labelled as AI-generated hypotheses unless independently validated.

Multimodal processing remains optional and degradable for an individual analysis run because user consent, provider availability, privacy, cost, or latency requirements may prevent it. Optional per run does not mean optional to the product vision; deterministic results must simply remain usable when the generated path is unavailable.

---

## Target User

The primary user is a Guilty Gear Strive player who:

- wants to improve through deliberate match review;
- records completed sets and practice notes;
- wants to identify repeated mistakes and matchup trends;
- may upload MP4 gameplay footage for complementary CV and multimodal analysis;
- values evidence and uncertainty over confident but unsupported conclusions.


---

## Product Principles

### Evidence and hypotheses remain distinct

Gameplay facts must come from deterministic processing or explicit player-entered data. A multimodal model may independently describe supplied frames or clips, assess decisions, identify candidate opportunities, propose alternatives, explain possible outcomes, and suggest practice. When those interpretations have not been independently validated, the product presents them as AI-generated hypotheses rather than verified facts.

### Honest uncertainty

Sampled video observations do not prove exact frame boundaries. The system represents coarse boundary ranges and distinguishes ambiguous visual evidence from technical failures.

### Private by default

Replay videos are user-owned and stored in a private object-storage bucket. Access is authorized through the backend using short-lived presigned URLs.

### Simple before sophisticated

The project should use the simplest implementation that correctly supports its requirements. New layers and abstractions need a demonstrated maintenance or correctness benefit.

### Preserve understandable code

The codebase is a learning project as well as a product. Clear names, focused responsibilities, direct data flow, and meaningful tests are preferred over code that merely appears enterprise-like.

---

## Core Replay-Understanding Capabilities

The roles below describe the approved product direction, not the current implementation. Today the repository has early deterministic CV primitives, described under **Current Replay-Analysis Capabilities**, and no multimodal provider integration.

### Computer Vision

Computer vision independently measures information that can be evaluated against labelled video evidence. The current implementation detects broad combat-HUD presence and infers coarse gameplay windows. Planned signals include refined gameplay and round boundaries, detailed HUD states, health, Burst and Tension resources, player side, screen position, movement, animations, and eventually candidate moves.

CV outputs retain timestamps or ranges, analyzer and configuration versions, confidence or ambiguity, and `ok`, `unknown`, or `failed` status. These outputs can support deterministic gameplay events and rules without relying on an LLM.

### Multimodal LLM Gameplay Understanding

Multimodal gameplay understanding is planned and not implemented yet. The multimodal LLM will directly examine selected gameplay clips or sampled frames together with bounded structured context. It is expected to attempt contextual interpretation, including:

- describing what appears to be happening;
- identifying possible good or bad decisions;
- suggesting potential missed opportunities or punishes;
- recommending possible alternative actions;
- explaining why a decision may have worked or failed; and
- suggesting what the player should practice.

The model may contribute a useful coaching hypothesis even when CV cannot verify the full situation. Its output records the source media and supplied evidence, model and prompt version, uncertainty and caveats, and whether any part was independently validated. It must not silently promote an interpretation into an observation or deterministic finding.

### Complementary Roles

CV supplies measurable, repeatable signals. The multimodal LLM supplies broader contextual interpretation that may be less certain. Each path is evaluated on its own terms, and the interface makes their provenance visible so a player can compare deterministic evidence with AI-generated hypotheses. Neither path is a substitute for the other.

---

## Product Vocabulary

- **Round:** one health-bar battle within a game.
- **Game:** won by taking two rounds.
- **Set:** a group of games played against one opponent, often first-to-two.
- **Match record:** the application's stored record of a reviewed set. Some existing code and API paths use `match` for this concept.
- **Replay:** metadata or an uploaded video associated with a match record.
- **HUD detection:** deterministic classification of whether a sampled frame contains the expected Guilty Gear Strive combat HUD.
- **Unknown sample:** a frame was processed successfully, but its visual evidence was inconclusive.
- **Failed sample:** frame extraction or detection failed technically.
- **Gameplay window:** a coarse time range inferred from consecutive HUD samples that likely represents active gameplay.
- **Coaching insight:** a deterministic summary or recommendation based on recorded match data or, in the future, extracted replay facts.
- **Review moment:** an evidence-linked situation worth inspecting that is not automatically labelled a mistake.
- **AI coaching hypothesis:** a multimodal model's uncertain interpretation of gameplay, decisions, opportunities, alternatives, or practice needs. It is generated analysis, not a verified fact.
- **Multimodal gameplay interpretation:** generated analysis based on bounded frames, clips, and structured context; it may include coaching hypotheses as well as explanations of deterministic results.

---

## Pages and Routes

```text
/                  -> Public landing page
/login             -> Log in
/signup            -> Create an account
/dashboard         -> Match statistics and recent match history
/matches           -> Paginated and sortable match history
/matches/new       -> Create a match record
/matches/:id       -> Review/edit a match and manage its replays
/coaching          -> Deterministic coaching insights
```

Protected application pages send unauthenticated users to `/login`. An authenticated user who visits the landing page is sent to `/dashboard`.

---

## Navigation

Authenticated pages use the shared application shell with these primary destinations:

```text
Dashboard    Match History    Coaching    Add Match
```

The landing, login, and signup pages sit outside the authenticated application shell.

---

## Core User Flows

### Authentication

- A user creates an account with email, username, and password.
- The backend returns a JWT access token and user information.
- The frontend stores the token locally and uses it for protected API requests.
- On a later visit, the frontend requests the current user to restore the session.

### Recording a Match

- The user opens Add Match.
- They enter characters, result, date, rank, duration, optional completed-set score, notes, mistakes, strengths, loss reason, and next practice focus.
- The frontend provides immediate validation and sanitizes form values.
- FastAPI performs authoritative validation and associates the record with the authenticated user.
- The saved match appears in match history, dashboard statistics, and coaching calculations.

### Reviewing Match History

- The user views their account-scoped match records.
- Results are paginated and can be sorted by recently played, last updated, or oldest played.
- A text filter narrows the matches displayed on the current page.
- Opening a record allows the user to review, edit, or delete it.

### Viewing Deterministic Coaching

- The backend analyzes the user's recorded match history.
- It calculates win rates, streaks, character usage, matchup records, trends, repeated mistakes, and recurring practice priorities.
- Recommendations include their evidence and sample size.
- The UI reports when there is not enough data instead of presenting an unsupported conclusion.
- Current coaching uses manually entered match data; replay-derived coaching is not implemented yet.

### Attaching Replay Metadata

- A user can attach one or more replay records to a match.
- A replay can describe a replay file, video, or external reference without uploading bytes.
- Replay ownership is inherited through its parent match.

### Uploading an MP4 Replay

- The frontend requests an authorized upload from FastAPI.
- FastAPI creates a pending replay record and returns a short-lived presigned upload URL.
- The browser uploads the MP4 directly to private R2 object storage.
- The frontend asks FastAPI to confirm the upload.
- FastAPI reads trusted storage metadata before marking the replay uploaded.
- Authorized download requests receive a short-lived presigned download URL.

### Inspecting and Sampling a Replay

- An uploaded replay is temporarily downloaded to the backend for processing.
- `ffprobe` extracts technical metadata such as duration, resolution, frame rate, and codec.
- After successful inspection, the user can request a frame at an explicit timestamp.
- FFmpeg extracts a resized JPEG frame and returns it without permanently storing the image.
- Internal services can classify sampled frames, build a HUD timeline, and infer coarse gameplay windows.

---

## Current Replay-Analysis Capabilities

The existing deterministic pipeline is:

```text
private replay object
  -> temporary local MP4
  -> ffprobe metadata inspection
  -> FFmpeg frame extraction
  -> Pillow-based HUD measurements
  -> HUD classification
  -> timestamp-sampled HUD timeline
  -> coarse gameplay-window inference
```

The current HUD detector can classify the visible structure of sampled frames as:

- `likely_gameplay_hud`;
- `not_gameplay_hud`;
- `unknown`.

It does not currently identify characters, read the timer, measure health, recognize moves, detect game decisions, or provide replay-derived coaching.

---

## Main Stored Data

### Users

- Account identity and password hash.
- Own all match records in their account.

### Matches

- Player and opponent characters.
- Win/loss result and date.
- Rank, duration, and optional completed-set score.
- Notes, mistake tags, strength tags, loss reason, and practice focus.
- Belong to exactly one user.

### Replays

- Belong to exactly one match.
- Describe the replay source and original filename/reference.
- May track a private object-storage key and upload state.
- May store inspected technical video metadata and processing state.

Detailed table definitions and module dependencies belong in `context/architecture.md`, not this overview.

---

## Features Implemented

- Email/password signup and login with JWT authentication.
- Account-scoped match creation, reading, editing, and deletion.
- Paginated and sortable match history.
- Dashboard match statistics.
- Deterministic coaching from manual match data.
- Multiple replay records per match.
- Private MP4 upload and authorized download through presigned URLs.
- Upload confirmation using trusted object metadata.
- Storage cleanup when uploaded replays or parent matches are deleted.
- Video metadata inspection with `ffprobe`.
- Single-frame extraction with FFmpeg.
- Single- and multi-timestamp deterministic HUD detection.
- Internal timestamp generation and HUD timeline scanning.
- Internal coarse gameplay-window inference with uncertainty ranges.

---

## Near-Term Direction

- Refine coarse gameplay boundary ranges and establish a versioned evaluation harness.
- Persist analysis runs and process full replay work through a recoverable PostgreSQL-backed worker.
- Expose authorized analysis status, uncertainty-aware gameplay windows, and supporting replay moments in the UI.
- Segment games and rounds as deterministic evidence permits.
- After the analysis-run privacy and derived-media gates exist, evaluate a backend-only multimodal gameplay-understanding prototype in parallel with segmentation work.
- Continue replay lifecycle recovery, isolated database testing, accessible failure states, and evaluation-data discipline as milestone prerequisites.

---

## Longer-Term Direction

The deterministic evidence hierarchy is:

```text
Replay
  -> Set
  -> Game
  -> Round
  -> Visual Observation
  -> Gameplay Event
  -> Deterministic Finding or Review Moment
  -> Coaching Recommendation
```

Alongside that hierarchy, the multimodal LLM directly examines bounded clips or frames and produces AI-generated gameplay hypotheses. Those hypotheses may reinforce a deterministic result, disagree with it, or identify a candidate coaching opportunity that CV cannot yet verify. The UI and persistence model must retain that distinction.

The first targeted replay-derived coaching finding is:

> The round appears to have ended while Burst was visually available.

This is a review moment, not automatically a mistake. The first slice requires supported round ranges, a deterministic Burst observation, an evidence-linked moment, optional multimodal interpretation or coaching hypotheses, and correctness/usefulness feedback.

Later deterministic findings or AI-generated coaching hypotheses may include:

- missed anti-airs;
- punish opportunities;
- unsafe attacks;
- Burst and Tension usage;
- defensive habits;
- wall-break decisions;
- repeated neutral losses;
- game- and round-level turning points.

These are product goals, not claims about current functionality.

---

## Features Out of Scope for the Current Project Phase

- Native Guilty Gear Strive replay parsing.
- General-purpose video understanding.
- Machine-learning model training.
- OCR or timer/health extraction before the deterministic foundations are ready.
- LLM-generated gameplay facts.
- Automatic gameplay decisions without supporting evidence.
- Public replay hosting.
- Social feeds, teams, or shared organization accounts.
- Native mobile applications.
- Payments or subscriptions.
- Large-scale production deployment architecture.

An out-of-scope feature can be reconsidered later, but it should not be introduced incidentally during unrelated work.

---

## Success Criteria

### Current application

- A user can create an account and manage only their own matches and replays.
- Match records reliably produce useful dashboard and coaching summaries.
- Insufficient data is represented honestly.
- Uploaded replays remain private and require authorization to access.
- Replay inspection and frame extraction fail safely without leaking internal details.
- Visual ambiguity remains distinct from technical failure.
- Automated tests protect important domain and ownership behavior.

### Replay-analysis foundation

- The same replay and sampling configuration produce deterministic results.
- Measurements and classifications retain enough evidence to be debugged and calibrated.
- Gameplay boundaries communicate their uncertainty rather than claiming false precision.
- Each analysis stage remains independently testable.
- The first coaching slice can link a round-end Burst review moment to its deterministic observation and supporting media without calling it a confirmed mistake.
- Multimodal analysis can inspect actual gameplay media and produce useful decision, opportunity, alternative-action, and practice hypotheses without presenting them as verified facts.
- Generated interpretations cite only supplied media or evidence, remain visibly separate from deterministic results, communicate uncertainty, and can fail or be declined without hiding deterministic results.

### Maintainability and learning

- A developer can trace a request from React through FastAPI to PostgreSQL or R2.
- Important responsibilities have clear file locations.
- New features preserve established ownership and evidence boundaries.
- The developer can explain major workflows and architectural choices in an interview.
- Documentation remains accurate without duplicating the same details across several files.

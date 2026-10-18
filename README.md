# Guilty Gear Coach

Guilty Gear Coach is a full-stack match tracker and evidence-grounded replay-coaching project for **Guilty Gear Strive** players.

It began as a way to help my brother review matches more efficiently. Today, the application records completed sets, turns manual notes into deterministic coaching summaries, stores private replay videos, and provides the first computer-vision building blocks for analyzing those videos.

The long-term goal is a **Stockfish-like post-match review experience**: help a player find important moments, understand possible decisions, and choose what to practice next. The comparison describes the review experience—not a claim that fighting games have a single computable best move.

## Product Vision

Replay understanding will use two complementary analysis paths:

```text
                             -> CV measurements and observations
uploaded gameplay video ----> deterministic events, findings, and review moments
                         |
                         +---> multimodal LLM video interpretation
                               -> AI-generated gameplay hypotheses and coaching ideas

both paths -> evidence-linked player review and practice recommendations
```

Computer vision provides measurable, repeatable evidence. A multimodal LLM may directly inspect authorized clips or sampled frames and suggest possible decisions, missed opportunities, alternatives, explanations, or practice priorities.

Generated interpretations may be useful even when uncertain, but they must remain visibly labelled as **AI coaching hypotheses** unless independently validated. They never become measured gameplay facts merely because a model stated them confidently.

> **Current status:** The match tracker and early deterministic replay-analysis foundation are implemented. Replay-derived coaching and multimodal LLM integration are planned, not currently available.

## Screenshots

### Dashboard

Match statistics, opponent performance, mistake tags, and recent match history.

![Guilty Gear Coach dashboard](docs/images/dashboard.png)

### Coaching Insights

Deterministic coaching recommendations generated from logged match history.

![Guilty Gear Coach coaching insights](docs/images/coaching.png)

### Replay Processing

A private uploaded replay with inspected metadata, explicit timestamp sampling, and an extracted gameplay frame.

![Guilty Gear Coach replay processing](docs/images/replay-processing.png)

## Implemented Today

### Match tracking and coaching

- Email/password signup and login with JWT authentication.
- Account-scoped match creation, editing, deletion, pagination, and sorting.
- Characters, result, rank, date, duration, completed-set score, notes, mistakes, strengths, loss reason, and practice focus.
- Dashboard statistics and deterministic coaching summaries from manually entered match history.
- Evidence and sample sizes for coaching conclusions, including honest insufficient-data states.

### Private replay lifecycle

- Multiple replay records per match.
- Metadata-only replay references or real MP4 uploads.
- Direct browser-to-Cloudflare-R2 uploads through short-lived presigned URLs.
- Backend confirmation using trusted object metadata.
- Authorized short-lived download URLs.
- R2 object cleanup when uploaded replays or parent matches are deleted.
- Ownership enforced through `Replay -> Match -> User`.

### Replay-analysis foundation

- `ffprobe` metadata inspection for duration, resolution, frame rate, and codec.
- FFmpeg frame extraction at explicit timestamps.
- Pillow-based deterministic combat-HUD measurements.
- Single- and multi-timestamp HUD detection.
- Internal timestamp generation and HUD timeline scanning.
- Internal coarse gameplay-window inference with uncertainty ranges.

## Not Yet Implemented

- Refined gameplay-window boundaries or durable analysis runs.
- User-visible gameplay-window results.
- Game or round segmentation.
- Health, Burst, Tension, timer, character, position, movement, animation, or move recognition.
- Replay-derived gameplay events, findings, or coaching.
- A background analysis worker.
- A multimodal provider or AI gameplay hypotheses.
- Cross-replay personalization.

The first targeted replay-derived coaching finding is:

> **The round appears to have ended while Burst was visually available.**

This will be presented as an evidence-linked review moment, not automatically as a mistake. The player may have had a valid reason not to Burst, and either the visual evidence or tactical context may be incomplete.

## Current Replay Pipeline

The implemented video path is deterministic and evidence-first:

```text
private replay object
  -> temporary local processing workspace
  -> ffprobe technical metadata inspection
  -> FFmpeg frame extraction
  -> Pillow-based HUD measurements
  -> HUD classification
  -> timestamp-sampled HUD timeline
  -> coarse gameplay-window inference
```

The current detector classifies sampled frames as:

- `likely_gameplay_hud`;
- `not_gameplay_hud`; or
- `unknown`.

`unknown` means processing succeeded but the visual evidence was inconclusive. It is different from `failed`, which means extraction or detection failed technically.

Sampled transitions are stored as ranges rather than false frame-level precision. A boundary may look like `[12s, 14s]`, meaning the transition was observed somewhere inside that interval.

## Architecture

```mermaid
flowchart TD
    Player[Player] --> Frontend[React + TypeScript]
    Frontend --> API[FastAPI REST API]
    API --> Postgres[(PostgreSQL)]
    API --> StorageAuth[Presigned upload/download authorization]
    StorageAuth --> R2[(Private Cloudflare R2 bucket)]

    R2 --> Processing[Temporary local replay processing]
    Processing --> FFprobe[ffprobe inspection]
    Processing --> FFmpeg[FFmpeg frame extraction]
    FFmpeg --> HUD[Pillow HUD detection]
    HUD --> Timeline[Sampled HUD timeline]
    Timeline --> Windows[Coarse gameplay windows]

    Postgres --> ManualCoaching[Manual-data coaching]
    ManualCoaching --> Frontend

    Windows -. planned .-> Rules[Versioned events and deterministic findings]
    Processing -. planned bounded media .-> LLM[Multimodal gameplay interpretation]
    Rules -. planned .-> Review[Evidence-linked review]
    LLM -. planned AI hypotheses .-> Review
```

FastAPI is the authorization and control plane. The browser never receives storage credentials, permanent public object URLs, raw server paths, or model-provider credentials.

PostgreSQL rows and R2 objects are separate resources, so upload, confirmation, and deletion flows account for partial failure. Replay processing uses temporary local workspaces, subprocess timeouts, cleanup, and safe public error messages.

## Technology

| Area | Technologies |
| --- | --- |
| Frontend | React, TypeScript, Vite, React Router, Vitest |
| Backend | Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic, pytest |
| Data | PostgreSQL |
| Replay storage | Private Cloudflare R2 through the S3-compatible API and `boto3` |
| Media processing | FFmpeg, `ffprobe`, Pillow |
| Authentication | JWT bearer tokens, `python-jose`, Passlib/bcrypt |
| Containers | Docker Compose, PostgreSQL, FastAPI, Nginx |

## Quick Start with Docker

### Requirements

- Docker with Docker Compose
- Git
- Cloudflare R2 credentials only if you want to exercise real replay upload, download, or processing

Clone the repository, then create the environment file.

Bash:

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

Replace the placeholder `SECRET_KEY`. Configure the R2 values when real replay storage is needed, then start the application:

```bash
docker compose up --build
```

Open:

```text
Frontend: http://localhost:8080
API docs: http://localhost:8000/docs
Health:   http://localhost:8000/health
```

The backend container waits for PostgreSQL, runs `alembic upgrade head`, and then starts FastAPI. The containers use production-style images, so source changes usually require rebuilding the affected service.

## Cloudflare R2

Basic match tracking does not require working R2 credentials. Real MP4 upload, download, inspection, and frame extraction do.

Use a private bucket and configure the `S3_*` values documented in [`.env.example`](.env.example). The credentials need object read, write, head, and delete access for that bucket.

For browser uploads, configure bucket CORS for the exact frontend origin:

- allow `PUT` and `GET`;
- allow the `Content-Type` request header;
- expose `ETag`; and
- do not make the bucket public.

Keep real credentials only in an uncommitted `.env` file or deployment secret manager.

## Local Development

Docker Compose is the simplest way to run the complete stack. For separate development servers, start PostgreSQL first:

```bash
docker compose up -d db
```

### Backend

Create and activate a virtual environment, then install the pinned dependencies.

For Bash:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For PowerShell:

```powershell
cd backend
python -m venv .venv
. ./.venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

When running the backend outside Docker, point `DATABASE_URL` at `localhost` rather than the Compose hostname `db`. Also set a development `SECRET_KEY`.

Bash:

```bash
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/guilty_gear_coach
export SECRET_KEY=replace-with-a-long-random-value
alembic upgrade head
uvicorn app.main:app --reload
```

PowerShell:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/guilty_gear_coach"
$env:SECRET_KEY = "replace-with-a-long-random-value"
alembic upgrade head
uvicorn app.main:app --reload
```

Local replay inspection and frame extraction also require FFmpeg and `ffprobe` on the backend `PATH`. The Docker backend image already installs them.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Set `VITE_API_URL=http://localhost:8000/api` when the Vite development server is not using the Docker/Nginx `/api` proxy.

## Testing

Backend:

```bash
cd backend
pytest
```

Backend through the running Docker container:

```bash
docker compose exec backend sh -lc "PYTHONPATH=/app pytest"
```

Frontend:

```bash
cd frontend
npm test
npm run build
```

The suites cover authentication, account isolation, match workflows, coaching calculations, replay metadata, mocked private-storage behavior, upload confirmation, deletion cleanup, video inspection, frame extraction, HUD detection, timeline scanning, gameplay-window inference, and frontend match/replay interactions.

The current automated tests do not require real R2 access or large replay fixtures. Any future database-mutating integration suite must use an isolated disposable database rather than development or production data.

## Roadmap

The repository follows a ten-stage roadmap. The current position is:

| Stage | Status | Outcome |
| ---: | --- | --- |
| 1 | Implemented baseline | Match tracking, private replay storage, media inspection, HUD detection, timelines, and coarse gameplay windows |
| 2 | Next | Boundary refinement and a versioned evaluation harness |
| 3 | Planned | Durable analysis runs, a recoverable worker, and user-visible evidence |
| 4 | Planned | Game and round segmentation |
| 5 | Planned | An early privacy-gated multimodal gameplay-understanding prototype |
| 6 | Planned | The first round-end Burst review moment |
| 7–10 | Planned | Broader observations, gameplay events, move/punish analysis, personalization, and production hardening |

Stage 1 is complete and no active implementation is recorded. **Stage 2 — Boundary Refinement and Evaluation Harness** is next. Stage 5 may overlap Stage 4 only after Stage 3 establishes durable runs, bounded derived media, privacy controls, and a backend-only provider boundary.

See [`context/build-plan.md`](context/build-plan.md) for milestone dependencies and acceptance criteria, and [`context/progress-tracker.md`](context/progress-tracker.md) for current status.

## Project Principles

- **Evidence and hypotheses remain distinct.** Measured observations and deterministic findings are not interchangeable with generated interpretations.
- **Uncertainty is explicit.** Ambiguous visual evidence stays `unknown`; technical failure stays `failed`.
- **Private by default.** Replays remain account-scoped in private object storage.
- **Simple before sophisticated.** New layers and dependencies need a demonstrated benefit.
- **Understandable code matters.** This is both a product and a learning project, so direct data flow and clear responsibilities are preferred over unnecessary abstraction.

## More Documentation

- [Project overview](context/project-overview.md)
- [Architecture](context/architecture.md)
- [Code standards](context/code-standards.md)
- [Library guidance](context/library-docs.md)
- [Build plan](context/build-plan.md)
- [Progress tracker](context/progress-tracker.md)

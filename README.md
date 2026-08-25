# Guilty Gear Coach

Guilty Gear Coach is a full-stack match tracker and deterministic coaching foundation for Guilty Gear players. It focuses on useful manual set review before replay parsing, video analysis, or natural-language AI explanations are introduced.

## What The Current App Includes

- React + TypeScript frontend with a responsive dark esports dashboard
- FastAPI backend with JWT signup/login
- PostgreSQL-backed users and matches
- Alembic database migrations
- Match CRUD API routes scoped to the authenticated user
- Dashboard stats for total matches, win rate, matchup win rate, mistake tags, loss reasons, and recent matches
- Manual match form with player character, opponent character, win/loss, set score context, date, rank, duration, notes, mistake tags, strength tags, reason for loss, practice focus, and replay/video filename placeholder
- Advanced deterministic coaching insights from existing match history only
- Focused backend and frontend tests

## Project Structure

```text
guilty-gear-coach/
  backend/
    app/
      api/routes/       FastAPI route modules
      core/             settings, database, auth helpers
      models/           SQLAlchemy models
      schemas/          Pydantic request/response models
      services/         domain logic such as stats aggregation
    alembic/            database migrations
    tests/              pytest tests
  frontend/
    src/
      api/              typed API client
      auth/             auth context
      components/       shared UI
      pages/            route pages
```

## Run With Docker

1. Copy the environment file:

```bash
cp .env.example .env
```

2. Start the stack:

```bash
docker compose up --build
```

3. Open the app:

```text
Frontend: http://localhost:8080
API docs: http://localhost:8000/docs
Health: http://localhost:8000/health
```

The backend container runs `alembic upgrade head` on startup.

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL=http://localhost:8000/api` if your API runs somewhere else.

## Tests

```bash
cd backend
pytest
```

## API Overview

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/users/me`
- `GET /api/matches`
- `POST /api/matches`
- `GET /api/matches/{match_id}`
- `PATCH /api/matches/{match_id}`
- `DELETE /api/matches/{match_id}`
- `GET /api/stats/dashboard`
- `GET /api/coaching/insights`
- `GET /api/matches/{match_id}/replays`
- `POST /api/matches/{match_id}/replays`
- `GET /api/matches/{match_id}/replays/{replay_id}`
- `PATCH /api/matches/{match_id}/replays/{replay_id}`
- `DELETE /api/matches/{match_id}/replays/{replay_id}`
- `POST /api/matches/{match_id}/replays/uploads`
- `POST /api/matches/{match_id}/replays/{replay_id}/confirm-upload`
- `POST /api/matches/{match_id}/replays/{replay_id}/download-url`

## Private MP4 Replay Storage

MP4 replay videos are uploaded directly from the browser to private S3-compatible object storage using short-lived presigned URLs. FastAPI remains the authorization/control plane: it verifies `Replay -> Match -> User` ownership, creates storage keys, confirms uploads with object metadata, and issues short-lived download URLs. PostgreSQL stores only Replay metadata and stable private storage keys, never MP4 bytes or temporary presigned URLs.

Cloudflare R2 is the first intended production provider through its S3-compatible API. Keep the R2 bucket private; do not enable public bucket access for replay videos.

Required backend environment variables:

```text
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
S3_BUCKET_NAME=guilty-gear-coach-replays
S3_REGION=auto
S3_ACCESS_KEY_ID=<r2-access-key-id>
S3_SECRET_ACCESS_KEY=<r2-secret-access-key>
S3_PRESIGNED_UPLOAD_EXPIRATION_SECONDS=900
S3_PRESIGNED_DOWNLOAD_EXPIRATION_SECONDS=300
MAX_MP4_UPLOAD_SIZE_BYTES=2147483648
```

For Docker, place these values in `.env`. The `backend` service reads `.env` through `env_file`, while `DATABASE_URL` is still supplied by `docker-compose.yml` for the local Postgres service. Do not commit real R2 credentials.

Minimum Cloudflare R2 setup:

1. Create or choose a private R2 bucket.
2. Create R2 API credentials that can put, read, and inspect objects in that bucket.
3. Set `S3_ENDPOINT_URL` to the account-level S3-compatible endpoint.
4. Keep `S3_REGION=auto` for R2.
5. Add a CORS policy to the bucket for the frontend origins that will use presigned URLs.

Local R2 CORS example:

```json
[
  {
    "AllowedOrigins": ["http://localhost:8080", "http://localhost:5173"],
    "AllowedMethods": ["PUT", "GET"],
    "AllowedHeaders": ["Content-Type"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

For production, replace the localhost origins with the exact deployed frontend origin, such as `https://app.example.com`. Do not include path components or trailing slashes in `AllowedOrigins`. The implemented browser upload sends a `PUT` request with `Content-Type: video/mp4`; downloads use short-lived presigned `GET` URLs.

Manual end-to-end MP4 verification:

1. Copy `.env.example` to `.env` and fill in real R2 values without committing secrets.
2. Start the app with `docker compose up --build`.
3. Sign in and open an existing Match Detail page.
4. In Replay Sources, select a small `.mp4` file.
5. Click `Upload MP4`.
6. In the browser network tools, verify the backend upload initialization request succeeds.
7. Verify the direct browser `PUT` request to the R2 presigned URL succeeds.
8. Verify the backend confirmation request succeeds.
9. Confirm the Replay row displays `Uploaded video` with the file size.
10. Confirm the object exists in the private R2 bucket.
11. Click `Download video` and verify the authorized presigned download opens.
12. Sign in as another user and verify direct backend access to the other user's match/replay/download route returns `404`.
13. Try a non-MP4 file and confirm the frontend rejects it before upload.
14. Try a zero-byte or oversized MP4 and confirm it is rejected.

## Deterministic Coaching Thresholds

Phase 3 coaching uses manually entered match/set history only. Thresholds are intentionally conservative so the app does not pretend weak evidence is strong evidence:

- Recent performance windows: last 5 sets and last 10 sets.
- Performance trend: compare the recent 10 sets against the previous 10 sets; a 15 percentage-point change is improving or declining, otherwise stable.
- Matchup qualification: at least 3 recorded sets against a character before labeling strongest or weakest qualified matchup.
- Recent matchup trend: at least 6 sets against the same character, comparing the latest 3 against the prior history; a 20 percentage-point change is surfaced.
- Repeated mistake and practice patterns: at least 2 matching structured tags or exact normalized practice notes.
- Recommendations: limited to the top 5 evidence-backed findings.

The coaching response is structured into performance, streaks, character usage, matchups, patterns, and recommendations. Recommendations include type, priority, title, message, evidence, and sample size.

## Product Vision: Stockfish For Guilty Gear Strive

The long-term goal is a "Stockfish for Guilty Gear Strive": structured replay analysis that identifies gameplay decisions, mistakes, strengths, and practice priorities. The current `Match` record represents one completed match or set that the player wants to review. It does not model every game or round yet.

Terminology:

- A round is one health-bar battle.
- A game is won by taking two rounds.
- A set contains multiple games.
- Standard online and tournament formats may use different numbers of games required to win a set.

Future replay-aware architecture may introduce this hierarchy:

- Replay
- Set
- Game
- Round
- Gameplay event
- Deterministic analysis finding
- Coaching recommendation
- Optional LLM explanation

Future analysis may eventually identify neutral losses, missed anti-airs, failed punish opportunities, unsafe attacks, burst mistakes, tension or meter usage, defensive habits, repeated mistakes, wall-break decisions, decision quality by timestamp, game-level turning points, and round-level turning points.

The analysis system should produce structured, deterministic findings first. Phase 3 implements the deterministic finding and recommendation layers using manually entered match data. Future replay analysis should feed richer evidence into the same coaching system rather than replacing it. An LLM may later explain those findings in natural language, but it should not invent the underlying gameplay analysis. Do not add replay, game, round, gameplay-event, OpenAI, or external-AI infrastructure until a later phase explicitly calls for it.

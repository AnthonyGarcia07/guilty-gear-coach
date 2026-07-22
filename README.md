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
- Deterministic coaching insights from existing match history only
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

## Product Vision: Stockfish For Guilty Gear Strive

The long-term goal is a "Stockfish for Guilty Gear Strive": structured replay analysis that identifies gameplay decisions, mistakes, strengths, and practice priorities. The current `Match` record represents one completed match or set that the player wants to review. It does not model every game or round yet.

Terminology:

- A round is one health-bar battle.
- A game is won by taking two rounds.
- A set contains multiple games.
- Standard online and tournament formats may use different numbers of games required to win a set.

Future replay-aware architecture may introduce this hierarchy:

- Replay session
- Set
- Game
- Round
- Gameplay event
- Analysis finding
- Coaching recommendation

Future analysis may eventually identify neutral losses, missed anti-airs, failed punish opportunities, unsafe attacks, burst mistakes, tension or meter usage, defensive habits, repeated mistakes, wall-break decisions, decision quality by timestamp, game-level turning points, and round-level turning points.

The analysis system should produce structured, deterministic findings first. An LLM may later explain those findings in natural language, but it should not invent the underlying gameplay analysis. Do not add replay, game, round, gameplay-event, OpenAI, or external-AI infrastructure until a later phase explicitly calls for it.

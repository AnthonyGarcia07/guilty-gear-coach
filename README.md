# Guilty Gear Coach

Guilty Gear Coach is a Phase 1 full-stack match tracker for Guilty Gear players. It focuses on useful manual logging before AI coaching, replay parsing, or video analysis are introduced.

## What Phase 1 Includes

- React + TypeScript frontend with a responsive dark esports dashboard
- FastAPI backend with JWT signup/login
- PostgreSQL-backed users and matches
- Alembic database migration for the initial schema
- Match CRUD API routes scoped to the authenticated user
- Dashboard stats for total matches, win rate, matchup win rate, mistake tags, loss reasons, and recent matches
- Manual match form with player character, opponent character, win/loss, date, rank, duration, notes, mistake tags, strength tags, reason for loss, practice focus, and replay/video filename placeholder
- Focused unit test for dashboard stat aggregation

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

## Phase 2 Ready Areas

The schema keeps replay/video as a placeholder filename now, while leaving room for a future upload table, parsing job queue, OpenAI-generated coaching summaries, matchup knowledge, and video event extraction.

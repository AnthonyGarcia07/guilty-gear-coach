# Library Docs

Project-specific usage patterns for the third-party libraries and external tools used by Guilty Gear Coach. This file explains what each dependency owns, where it is used, the approved integration pattern, and the boundaries that must remain stable. It is not a replacement for official documentation.

Last verified against `frontend/package-lock.json`, `frontend/package.json`, `backend/requirements.txt`, the Dockerfiles, and current source imports: 2026-10-17.

---

## Before Using Any Library

Before changing library-dependent code:

1. Read `AGENTS.md` and the relevant context files for project constraints.
2. Check whether an applicable installed skill or configured connector exists. Follow it before changing integration code.
3. Check the version declared or locked in this repository.
4. Read the relevant section below for the project's approved integration pattern.
5. Consult the linked official documentation for that major or pinned version.
6. Inspect existing source and tests before introducing a new pattern.
7. Do not add or upgrade a dependency without an approved need.

When guidance appears to conflict, use this order:

```text
current task and AGENTS.md
  -> installed version, repository contracts, and tests
  -> project-specific rules in this file
  -> applicable skills/connectors and official version-matched documentation
  -> general training knowledge
```

Skills and official documentation explain supported APIs; they do not override this project's ownership, privacy, evidence, or architecture rules. Documentation for the latest release may not match the version installed here.

Prefer project conventions over a generic tutorial when both use supported APIs. If official documentation and the installed version disagree, stop and verify the installed package rather than guessing.

### Current Integration Map

| Capability | Primary project files |
| --- | --- |
| React root and routing | `frontend/src/main.tsx`, `frontend/src/App.tsx` |
| Authentication state | `frontend/src/auth/AuthContext.tsx`, `backend/app/api/deps.py`, `backend/app/core/security.py` |
| Frontend HTTP transport | `frontend/src/api/client.ts`, `frontend/src/api/errors.ts` |
| Match API and validation | `backend/app/api/routes/matches.py`, `backend/app/schemas/match.py` |
| Replay API | `backend/app/api/routes/replays.py`, `backend/app/schemas/replay.py` |
| Database setup and models | `backend/app/core/database.py`, `backend/app/models/` |
| R2 integration | `backend/app/services/storage.py` |
| Video metadata and frames | `backend/app/services/video_inspection.py`, `backend/app/services/frame_extraction.py` |
| Deterministic HUD analysis | `backend/app/services/ggst_hud_detection.py`, `backend/app/services/replay_hud_timeline.py`, `backend/app/services/replay_gameplay_windows.py` |
| Frontend tests | `frontend/src/**/*.test.ts`, `frontend/src/**/*.test.tsx` |
| Backend tests | `backend/tests/` |

### Version Sources

| Dependency type | Source of truth |
| --- | --- |
| Frontend direct dependency request | `frontend/package.json` |
| Frontend resolved dependency version | `frontend/package-lock.json` |
| Backend direct dependency version | `backend/requirements.txt` |
| Python runtime | `backend/Dockerfile` |
| FFmpeg and `ffprobe` | Debian package installed by `backend/Dockerfile`; exact version is image-build dependent |
| PostgreSQL | `postgres:16-alpine` in `docker-compose.yml` |
| Nginx | `nginx:1.27-alpine` in `frontend/Dockerfile` |

Useful read-only version checks:

```text
frontend: npm ls --depth=0
backend:  python -m pip freeze
media:    ffmpeg -version
media:    ffprobe -version
database: SELECT version();
```

Run media and backend checks inside the backend container when the host does not have those dependencies installed.

---

## Canonical Integration Recipes

These examples show the intended shape of common library interactions. Reuse the pattern, but keep feature-specific names and validation explicit.

### Load Typed API Data in a React Page

Use the shared API client, represent failure explicitly, and prevent abandoned work from updating the page:

```typescript
useEffect(() => {
  let active = true;

  async function loadStats(): Promise<void> {
    setLoading(true);
    setError("");

    try {
      const response = await api.stats();
      if (active) setStats(response);
    } catch (error: unknown) {
      if (active) {
        setError(normalizeUnknownError(error, "Unable to load dashboard.").message);
      }
    } finally {
      if (active) setLoading(false);
    }
  }

  void loadStats();
  return () => {
    active = false;
  };
}, []);
```

Rules:

- Do not call `fetch` directly from the page when the operation belongs in `frontend/src/api/client.ts`.
- Render loading, success, empty, and error states separately.
- An ignored or rejected promise must not leave permanent loading UI.
- An active flag prevents stale state updates; use `AbortController` only when the transport operation supports meaningful cancellation.

### Authorize a User-Owned FastAPI Resource

Scope the database query to the authenticated user instead of fetching first and trusting a client-side ownership check:

```python
@router.get("/{match_id}", response_model=MatchRead)
def get_match(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Match:
    match = db.scalar(
        select(Match).where(
            Match.id == match_id,
            Match.owner_id == current_user.id,
        )
    )
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )
    return match
```

Rules:

- Replay authorization first resolves the owned parent match, then the replay under that match.
- Preserve the established not-found behavior for inaccessible resources.
- Never accept `owner_id` from the browser as proof of ownership.

### Translate a Service Failure at the HTTP Boundary

Services expose a deliberately safe message; routes choose the HTTP status:

```python
try:
    metadata = inspector.inspect(video_path)
except VideoInspectionError as error:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=error.public_message,
    ) from error
```

Rules:

- Service exceptions must not depend on FastAPI.
- Catch only failures the route can translate meaningfully.
- Do not send local paths, subprocess output, storage details, or stack traces to the client.

### Inject an External Adapter for Tests

Define the smallest protocol the service needs and supply a fake in tests:

```python
class S3Client(Protocol):
    def head_object(self, Bucket: str, Key: str) -> dict[str, Any]:
        ...


storage = S3CompatibleStorageService(
    endpoint_url="https://example.invalid",
    bucket_name="test-bucket",
    region="auto",
    access_key_id="test-key",
    secret_access_key="test-secret",
    presigned_upload_expiration_seconds=900,
    presigned_download_expiration_seconds=300,
    client=fake_client,
)
```

Rules:

- Mock the project-owned boundary rather than boto3 internals when possible.
- Keep protocols narrow and behavior-based.
- Do not create a general dependency-injection framework for ordinary constructor or FastAPI dependency injection.

---

## Frontend Dependency Snapshot

`frontend/package.json` currently requests `latest` for every direct dependency. The lockfile provides the reproducible version snapshot below, but an intentional install or update can move versions, including major versions. Never rely on the word `latest` as an API contract.

| Library | Locked version | Responsibility |
| --- | ---: | --- |
| React | 19.2.7 | Component rendering and state |
| React DOM | 19.2.7 | Browser root and server-style test rendering |
| React Router DOM | 7.18.1 | Client-side routes, links, navigation, and route state |
| Lucide React | 1.24.0 | Interface icons |
| Vite | 8.1.4 | Development server and production bundling |
| `@vitejs/plugin-react` | 6.0.3 | React transformation for Vite |
| TypeScript | 7.0.2 | Strict static type checking |
| Vitest | 4.1.10 | Frontend unit and component-output tests |
| `@types/react` | 19.2.17 | React TypeScript declarations |
| `@types/react-dom` | 19.2.3 | React DOM TypeScript declarations |

Do not manually edit `package-lock.json`. When an approved dependency change occurs, update the manifest and lockfile together and run both tests and the production build.

---

## React and React DOM

Official documentation:

- [React reference](https://react.dev/reference/react)
- [React hooks](https://react.dev/reference/react/hooks)
- [Using TypeScript with React](https://react.dev/learn/typescript)
- [React DOM client APIs](https://react.dev/reference/react-dom/client)

### Project Usage

- The application is a browser-rendered single-page application, not a server-component application.
- `frontend/src/main.tsx` creates one React root, enables `StrictMode`, installs `BrowserRouter`, and mounts `AuthProvider` above `App`.
- Route pages own page-level loading and API state.
- Reusable forms, dialogs, replay controls, and shell elements live in `frontend/src/components/`.
- Tests currently use `react-dom/server` and `renderToStaticMarkup` for many output assertions.

### Rules

- Use effects to synchronize with external systems or asynchronous operations, not for values that can be derived during rendering.
- Include every reactive dependency used by an effect. If that causes unwanted reruns, fix the data flow rather than suppressing the dependency.
- Clean up object URLs, timers, subscriptions, and abandoned asynchronous work.
- Keep state local until multiple components genuinely require shared ownership.
- Do not add a state-management library for ordinary page or form state.
- Expect `StrictMode` to expose unsafe effect behavior during development.
- Do not add memoization automatically. Use it only for demonstrated expensive work or a required stable identity.
- Preserve controlled inputs and explicit busy/error states in forms.

### Testing Limitation

The project does not currently configure a browser-like Vitest environment or React Testing Library. Static rendering is appropriate for output and attributes, but it does not prove focus movement, browser events, effect cleanup, or interactive dialog behavior. Adding `jsdom`, a browser runner, or a testing library is a separate dependency decision and should be justified by an interaction that cannot be tested reliably with the current setup.

---

## React Router DOM

Official documentation:

- [Declarative routing](https://reactrouter.com/start/declarative/routing)
- [`BrowserRouter`](https://reactrouter.com/api/declarative-routers/BrowserRouter)
- [Navigation](https://reactrouter.com/start/declarative/navigating)
- [`useNavigate`](https://reactrouter.com/api/hooks/useNavigate)

### Project Usage

- The application uses declarative `BrowserRouter`, `Routes`, and `Route` APIs.
- `Protected` in `frontend/src/App.tsx` guards authenticated pages.
- `Link` and `NavLink` handle user-initiated navigation.
- `useNavigate` handles navigation after successful mutations or authentication changes.
- Navigation state carries short-lived success messages and match-history return locations.

### Rules

- Use `Link` or `NavLink` for ordinary user navigation so browser and accessibility behavior remain intact.
- Reserve `useNavigate` for programmatic transitions such as a completed submission or deletion.
- Validate any `returnTo` value before navigating; do not accept an arbitrary external URL.
- Keep authentication enforcement on the backend even when a frontend route is protected.
- Do not migrate to data routers, loaders, actions, or another routing mode without an approved reason and a route-wide plan.
- Preserve query parameters and navigation state deliberately when returning from detail or edit pages.

---

## Vite and the React Plugin

Official documentation:

- [Vite guide](https://vite.dev/guide/)
- [Vite features and TypeScript behavior](https://vite.dev/guide/features.html)
- [Environment variables and modes](https://vite.dev/guide/env-and-mode)
- [Vite CLI](https://vite.dev/guide/cli)

### Project Usage

- `frontend/vite.config.ts` enables the React plugin and serves development traffic on port 5173.
- `npm run build` runs `tsc` before `vite build`; Vite transformation alone is not the project's type check.
- `VITE_API_URL` is the only current custom browser environment variable. It defaults to `/api`.
- Nginx serves the production bundle and proxies API traffic according to `frontend/nginx.conf`.

### Rules

- Any variable prefixed with `VITE_` is browser-visible and must not contain a secret.
- Read values through `import.meta.env`, not Node-only `process.env` in browser code.
- Restart the development server after changing environment files.
- Keep Vite configuration small. Do not add plugins for behavior already supplied by the platform or existing tooling.
- Use `npm run build` to verify both strict TypeScript and the production bundle.
- Do not use `vite preview` as a production server.

---

## TypeScript

Official documentation:

- [TypeScript handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [TSConfig reference](https://www.typescriptlang.org/tsconfig/)

### Project Usage

- `frontend/tsconfig.json` enables strict checking, isolated modules, DOM libraries, and the React JSX transform.
- Shared frontend domain contracts live in `frontend/src/types.ts`.
- Type-only imports use `import type`.

### Rules

- Preserve strict mode and isolated-module compatibility.
- Use `unknown` plus narrowing instead of `any`.
- Treat assertions as boundary exceptions, not normal control flow.
- Update frontend types together with backend response schemas.
- Vite transpilation does not replace `tsc`; both are part of the current build command.

---

## Vitest

Official documentation:

- [Vitest guide](https://vitest.dev/guide/)
- [Mocking guide](https://vitest.dev/guide/mocking.html)
- [Vitest API](https://vitest.dev/api/)

### Project Usage

- `npm test` runs `vitest run` once; it is not watch mode.
- There is no separate Vitest configuration file, so Vitest uses the Vite configuration.
- Existing tests cover pure utilities, API error normalization, submission navigation, validation, and static component output.

### Rules

- Reset or restore mocks that change shared state.
- Mock at API or external-system boundaries, not inside the behavior being tested.
- Prefer small typed fixtures over large snapshots.
- Test visible output, returned values, navigation, and error behavior.
- Do not claim a static-rendering test verifies browser focus, effects, or event propagation.

---

## Lucide React

Official documentation:

- [Lucide guide](https://lucide.dev/guide/packages/lucide-react)
- [Lucide icons](https://lucide.dev/icons/)

### Project Usage and Rules

- Use Lucide for interface icons rather than introducing another icon library.
- The existing default icon size is 18px; match the surrounding registered UI pattern.
- Pair important navigation, upload, inspection, and destructive icons with visible text.
- Treat decorative icons as hidden from assistive technology when necessary.
- An icon must not be the only signal for success, failure, priority, or evidence confidence.

---

## Backend Dependency Snapshot

The table lists direct versions pinned in `backend/requirements.txt`.

| Library | Pinned version | Responsibility |
| --- | ---: | --- |
| FastAPI | 0.111.1 | HTTP API, dependency injection, request validation, response mapping |
| SQLAlchemy | 2.0.32 | ORM models, queries, sessions, and transactions |
| Alembic | 1.13.2 | Forward database migrations |
| Psycopg | 3.2.1 | PostgreSQL driver through `psycopg[binary]` |
| Pydantic Settings | 2.4.0 | Environment-backed settings |
| boto3 | 1.34.162 | S3-compatible Cloudflare R2 client |
| Pillow | 10.4.0 | Deterministic image loading and HUD measurements |
| python-jose | 3.3.0 | JWT encoding and validation |
| Passlib | 1.7.4 | Password hashing context |
| bcrypt | 4.0.1 | Password-hash implementation used by Passlib |
| Uvicorn | 0.30.5 | ASGI server |
| pytest | 8.3.2 | Backend tests |
| python-multipart | 0.0.9 | Form-data support required by FastAPI workflows |
| email-validator | 2.2.0 | Pydantic email validation |

Pydantic is imported directly throughout `backend/app/schemas/` but is not explicitly pinned as a direct requirement. It currently arrives transitively through FastAPI and Pydantic Settings. Treat its exact installed version as unresolved until checked inside the backend environment.

---

## FastAPI

Official documentation:

- [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Response models](https://fastapi.tiangolo.com/tutorial/response-model/)
- [Handling errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Testing](https://fastapi.tiangolo.com/tutorial/testing/)

### Project Usage

- `backend/app/main.py` creates the app, configures CORS, and registers routers under `/api`.
- Route modules use synchronous path functions and synchronous SQLAlchemy sessions.
- Dependencies provide the current user, database session, settings, and replaceable external services.
- Pydantic schemas define JSON request and response contracts.
- Binary frame samples return an explicit `Response` with `image/jpeg` media type.

### Rules

- Keep HTTP status selection, dependency resolution, and error translation in route modules.
- Keep reusable storage, subprocess, analysis, and domain behavior in services.
- Declare `response_model` for structured JSON responses when an appropriate schema exists.
- Validate ownership before returning whether a nested resource exists.
- Use `HTTPException` for intentional public HTTP failures, not as a service-layer domain type.
- Do not add async route functions around synchronous database, boto3, FFmpeg, or filesystem calls without an explicit concurrency design.
- Keep the current typed REST response shapes; do not introduce a generic success wrapper locally.

---

## Pydantic and Pydantic Settings

Official documentation:

- [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/)
- [Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

### Project Usage

- The codebase uses Pydantic v2-style APIs: `model_dump`, `field_validator`, `model_validator`, and `ConfigDict`.
- `backend/app/core/config.py` uses `BaseSettings` with a repository `.env` file.
- API schemas validate field bounds and cross-field match/replay rules.
- Read schemas use attribute-based conversion for SQLAlchemy objects.

### Rules

- Do not introduce Pydantic v1 methods such as `.dict()` or `@validator` into new code.
- Keep server-owned fields out of request schemas.
- Use `exclude_unset=True` when PATCH semantics must distinguish omission from an explicit null.
- Keep safe configuration defaults appropriate for local development, but require real secrets in deployed environments.
- Call `get_settings()` rather than constructing settings repeatedly in application code.
- If Pydantic behavior becomes version-sensitive, first identify and pin the direct Pydantic version in an approved dependency task.

---

## SQLAlchemy 2 and Psycopg 3

Official documentation:

- [SQLAlchemy ORM quick start](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [Using the Session](https://docs.sqlalchemy.org/en/20/orm/session.html)
- [SQLAlchemy select statements](https://docs.sqlalchemy.org/en/20/tutorial/data_select.html)
- [Declarative tables and `mapped_column`](https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html)
- [Psycopg 3 documentation](https://www.psycopg.org/psycopg3/docs/)

### Project Usage

- Models use SQLAlchemy 2 typed declarative mapping with `Mapped` and `mapped_column`.
- Queries use `select`, `Session.scalar`, and `Session.scalars` rather than the legacy `Query` API.
- `backend/app/core/database.py` creates one engine and session factory; `get_db` owns request-scoped session cleanup.
- The connection URL uses the `postgresql+psycopg` dialect.
- PostgreSQL-specific `ARRAY` columns store match tags.

### Rules

- Keep session lifetime outside services that merely query or transform data; accept a session when database work is required.
- Keep transactions short and explicit. Commit at the logical operation boundary.
- Roll back a caught failed transaction before reusing its session.
- Do not share a `Session` across threads, tasks, or future worker jobs.
- Use explicit ownership filters and deterministic ordering.
- Do not replace PostgreSQL tests with SQLite when PostgreSQL-specific behavior such as arrays, constraints, or dialect semantics matters.
- Avoid legacy `session.query(...)` in new code.

---

## Alembic

Official documentation:

- [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Migration operation reference](https://alembic.sqlalchemy.org/en/latest/ops.html)

### Project Usage and Rules

- Migration files live in `backend/alembic/versions/` and use sequential project revision names.
- The backend container currently runs `alembic upgrade head` before starting Uvicorn.
- Add one new migration for each approved schema change.
- Review autogenerated output; autogeneration cannot understand every data migration or project invariant.
- Never edit an applied migration to represent a new change.
- Plan existing-data backfills before making a column non-null or adding restrictive constraints.
- Do not run migrations against non-disposable data without explicit authorization.
- Verify the current revision and intended target before upgrade or downgrade work.

---

## PostgreSQL 16

Official documentation:

- [PostgreSQL 16 documentation](https://www.postgresql.org/docs/16/)

### Project Usage and Rules

- PostgreSQL is the authoritative store for users, matches, replay metadata, processing state, and future structured analysis provenance.
- Large MP4s and derived binary artifacts do not belong in PostgreSQL.
- Use database constraints for invariants that must survive every caller.
- Index ownership and lookup fields based on demonstrated query paths.
- Preserve timezone-aware timestamp columns.
- Use an isolated disposable PostgreSQL database for mutation-heavy integration tests.

---

## boto3 and Cloudflare R2

Official documentation:

- [Cloudflare R2 with boto3](https://developers.cloudflare.com/r2/examples/aws/boto3/)
- [boto3 S3 client reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [Cloudflare R2 presigned URLs](https://developers.cloudflare.com/r2/api/s3/presigned-urls/)

### Project Usage

- `backend/app/services/storage.py` wraps the S3-compatible client behind `S3CompatibleStorageService`.
- The client uses the R2 endpoint, region, credentials, and S3 Signature Version 4.
- The backend creates short-lived presigned PUT and GET URLs.
- The browser uploads MP4 bytes directly to R2 with `Content-Type: video/mp4`.
- Upload confirmation calls `head_object` and trusts object metadata rather than the browser's success claim.
- Tests substitute a small protocol-compatible fake instead of contacting R2.

### Rules

- Keep the bucket private and all long-lived credentials on the backend.
- The upload request's `Content-Type` must match the content type signed into the presigned PUT URL.
- Treat a presigned URL as temporary sensitive capability data; do not log or persist it.
- Validate object metadata again during confirmation.
- Treat database rows and R2 objects as separate resources with partial-failure handling.
- Keep boto3-specific response parsing inside the storage service.
- Do not mock boto3 internals when the storage-service boundary can be faked directly.

---

## Pillow

Official documentation:

- [Pillow handbook](https://pillow.readthedocs.io/en/stable/handbook/index.html)
- [`PIL.Image` reference](https://pillow.readthedocs.io/en/stable/reference/Image.html)

### Project Usage

- `backend/app/services/ggst_hud_detection.py` loads FFmpeg-produced frames, converts them to RGB or grayscale, crops normalized HUD regions, and computes deterministic pixel measurements.
- Images are fully loaded while the source file is open so returned image data does not depend on a closed file handle.
- HUD classification thresholds are application calibration values, not Pillow defaults.

### Rules

- Keep image loading and format failures translated to `GGSTHudDetectionError` with a safe public message.
- Normalize image mode before comparing pixel values.
- Keep dimensions and region coordinates explicit and tested.
- Do not replace deterministic pixel measurements with opaque model output under the same service contract.
- Threshold changes require representative fixtures and regression evidence.
- If future code accepts images not produced by the bounded FFmpeg path, add explicit dimension and decompression-bomb protections.

---

## FFmpeg and `ffprobe`

Official documentation:

- [FFmpeg documentation](https://ffmpeg.org/ffmpeg.html)
- [`ffprobe` documentation](https://ffmpeg.org/ffprobe.html)
- [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html)

### Project Usage

- The backend Docker image installs the Debian `ffmpeg` package, which supplies both executables.
- `FFprobeVideoInspectionService` requests JSON metadata and parses video streams, duration, dimensions, frame rate, and codec.
- `FFmpegFrameExtractionService` extracts one bounded-width JPEG at an explicit timestamp.
- Services use argument arrays, captured output, `check=True`, and timeouts.

### Rules

- Never interpolate user input into a shell command string.
- Preserve explicit timeouts and safe error translation.
- Validate replay readiness and timestamps before downloading or launching a subprocess.
- Do not expose stderr, local paths, or raw command output to the browser.
- Verify that an expected output file exists and is non-empty.
- Mock `subprocess.run` or the service boundary in ordinary tests; reserve real media integration tests for an approved environment.
- Because the Dockerfile does not pin an FFmpeg package version, record the actual executable version when diagnosing version-sensitive media behavior.

---

## Authentication Libraries

Official documentation:

- [python-jose](https://python-jose.readthedocs.io/en/latest/)
- [Passlib](https://passlib.readthedocs.io/en/stable/)
- [bcrypt](https://bcrypt.readthedocs.io/en/latest/)
- [FastAPI OAuth2 and JWT tutorial](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)

### Project Usage

- `backend/app/core/security.py` hashes passwords through a Passlib bcrypt context.
- JWT access tokens use HS256 with `sub` and expiration claims.
- `OAuth2PasswordBearer` extracts bearer tokens; `get_current_user` resolves the user from the token subject.
- The frontend stores the access token under `ggc_token` and attaches it through the shared API client.

### Rules

- Never log passwords, hashes, bearer tokens, or signing keys.
- Never accept an algorithm from an untrusted token; decode only with the configured algorithm allowlist.
- Keep token subjects stable and validate that the referenced user still exists.
- Use a strong deployment secret; the development fallback is not production-safe.
- Treat the pinned Passlib and bcrypt versions as a tested pair. Upgrade them together only after authentication regression tests.
- Authentication proves identity; every resource route must still enforce ownership.

---

## Uvicorn

Official documentation:

- [Uvicorn settings](https://www.uvicorn.org/settings/)

### Project Usage and Rules

- The backend container starts Uvicorn after applying Alembic migrations.
- Development reload behavior is a local concern and should not be copied into the production container command.
- Keep worker count, proxy headers, timeouts, and deployment topology as explicit deployment decisions.
- CPU-heavy full replay analysis should move to a worker process rather than consuming long-lived API requests as that feature matures.

---

## pytest

Official documentation:

- [pytest documentation](https://docs.pytest.org/en/stable/)
- [Built-in fixtures](https://docs.pytest.org/en/stable/builtin.html)
- [Parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html)

### Project Usage

- Pure service tests cover video parsing, frame extraction, HUD detection, timeline building, and gameplay-window inference.
- Route tests use FastAPI's test client and dependency overrides.
- Tests use fakes and monkeypatching for storage and subprocess boundaries.
- Parametrization covers rule variations and invalid configurations.

### Rules

- Prefer the built-in `tmp_path` fixture for test files.
- Keep mocks local and restore changed global or environment state.
- Use `pytest.raises` for intentional failure contracts.
- Do not contact real R2 or run real FFmpeg in ordinary unit tests.
- Verify database isolation before running tests that commit records.
- Preserve the distinction between ambiguous evidence and technical failure in fixtures and assertions.

---

## Small Supporting Libraries

### `email-validator`

Used indirectly by Pydantic's `EmailStr` in authentication schemas. Keep normalization and validation server-side. Do not treat email validation as proof that an address exists.

Official documentation: [email-validator project](https://github.com/JoshData/python-email-validator)

### `python-multipart`

Provides form-data parsing expected by FastAPI features. It is infrastructure support, not the approved path for large replay MP4 transfer; large uploads continue to use direct browser-to-R2 presigned PUT requests.

Official documentation: [python-multipart project](https://github.com/Kludex/python-multipart)

---

## Infrastructure Images

### Docker Compose

Official documentation: [Docker Compose](https://docs.docker.com/compose/)

- Compose provides local PostgreSQL, backend, and frontend containers.
- Do not assume a host-installed Python package or FFmpeg version matches the backend image.
- Persisted PostgreSQL volumes may contain development data; do not treat them as disposable test storage without verification.

### Nginx

Official documentation: [Nginx documentation](https://nginx.org/en/docs/)

- Nginx serves the built frontend assets in the production-style container.
- Preserve SPA fallback routing and `/api` proxy behavior when changing its configuration.
- Do not expose R2 credentials or private object paths through Nginx configuration.

---

## Libraries Not Currently Installed

The architecture discusses future capabilities that do not yet have an approved library implementation. Do not copy integration recipes from another project or assume a specific provider.

| Capability | Current status |
| --- | --- |
| Multimodal LLM provider SDK | Approved roadmap capability; provider and SDK are not selected |
| Background queue framework | Not installed; the planned first worker uses PostgreSQL coordination |
| OCR library | Not installed |
| Machine-learning or ONNX runtime | Not installed |
| Frontend state-management library | Not installed; React state and context are sufficient today |
| Component framework or Tailwind | Not installed; semantic CSS and the UI registry are authoritative |
| Browser interaction testing library | Not installed; add only for an approved testing need |
| Analytics SDK | Not installed |

When one of these capabilities becomes necessary:

1. Use `/architect` for the cross-cutting design.
2. Compare the standard library and existing dependencies before selecting a package.
3. Verify the current official API and licensing or data-retention implications.
4. Define the project-owned boundary and failure behavior before implementation.
5. Add the approved package, tests, configuration, and a new section here in the same feature.

### Multimodal Provider Selection Gates

The application-owned request and response schemas must be designed before choosing an SDK. The selection decision must document:

- support for the bounded frame or clip inputs required by the approved prototype;
- structured-output and schema-validation behavior;
- input retention, model-training use, regional processing, deletion, and audit terms;
- authentication and a backend-only credential path;
- timeout, retry, rate-limit, latency, and cost behavior;
- whether the official SDK provides enough value over a small direct HTTP adapter; and
- how provider responses will be mocked or recorded without committing private user media.

Start with one provider implementation after those gates are approved. Do not add a generic multi-provider framework in anticipation of future integrations.

A multimodal integration must support direct inspection of authorized gameplay clips or sampled frames, not only rewriting deterministic findings. Its contract may return descriptions, decision assessments, candidate missed opportunities or punishes, alternatives, outcome explanations, and practice suggestions. These remain AI-generated hypotheses unless independently validated. The integration must preserve the distinction between measured observations, deterministic findings, recommendations, and generated interpretations, and provider failure must leave deterministic results intact.

---

## Dependency Change Checklist

Before adding, removing, or upgrading a library:

1. State the concrete capability the change enables.
2. Confirm an existing dependency or platform API cannot satisfy the need simply.
3. Check the current resolved version and the target library's official migration notes.
4. Identify affected boundaries, configuration, lockfiles, Docker images, and licenses.
5. Add or update focused tests before changing behavior-sensitive dependencies.
6. Update the appropriate manifest and generated lockfile together.
7. Run the focused tests, broader relevant suite, and production build.
8. Verify migrations, media behavior, authentication, or storage behavior in the correct environment when affected.
9. Update this file only when project-specific library guidance or the supported dependency set changes.

Do not combine a dependency upgrade with an unrelated feature unless the feature truly requires that upgrade.

---

## Known Dependency Documentation Gaps

These are maintenance issues, not authorization to change dependencies:

- Frontend direct dependencies use `latest` in `package.json`; the lockfile is currently the only exact frontend version record.
- Pydantic is a direct source import but is not explicitly pinned in `backend/requirements.txt`.
- FFmpeg and `ffprobe` are installed from an unpinned Debian package during the backend image build.
- The current frontend test setup cannot fully exercise browser focus, effects, or user-event behavior.
- No automated dependency update or compatibility policy is currently documented beyond manual review and testing.

Resolve these through focused, approved maintenance tasks rather than incidental feature work.

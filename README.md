# Secure Task Tracker

Backend API built with FastAPI. Provides secure task management with JWT auth.

## Getting Started After Cloning

1. Clone:
   ```bash
   git clone <repo-url>
   cd python-task-manager
   ```
2. Create environment file:
   - Copy `.env.example` to `.env` (or create manually) and set at least:
     - `POSTGRES_USER=postgres`
     - `POSTGRES_PASSWORD=postgres`
     - `POSTGRES_DB=tasktracker`
     - `JWT_SECRET_KEY=<generate a long random secret>`
     - (Optional) `DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/tasktracker` for local (non‑Docker) run.
3. Choose a run mode:
   - Docker (recommended quickest):
     ```bash
     docker compose up --build
     ```
     This builds the image, runs Alembic migrations automatically, and starts the API on http://localhost:8000.
   - Local (needs a running Postgres):
     ```bash
     python -m venv .venv
     # PowerShell
     . .venv/Scripts/Activate.ps1
     pip install -e .[dev]
     createdb tasktracker   # or: psql -U postgres -c "CREATE DATABASE tasktracker;"
     alembic upgrade head
     uvicorn app.main:app --reload
     ```
4. (Optional) Seed base data (3 users + tasks) AFTER containers/local app can reach DB:
   - Docker:
     ```bash
     docker compose exec app python -m seeds.seed_data --base
     ```
   - Local:
     ```bash
     python -m seeds.seed_data --base
     ```
     Admin user from seed: `alice@example.com` / `Password1!`
5. Run tests (local dev environment recommended):
   ```bash
   pytest
   ```
6. Explore docs: http://localhost:8000/docs

Troubleshooting quick notes:

- If `ModuleNotFoundError: app` when seeding: use `python -m seeds.seed_data` (ensures proper module path).
- If Postgres connection fails in Docker: ensure `POSTGRES_*` vars in `.env` match `docker-compose.yml` and no stale volume conflicts; recreate with `docker compose down -v && docker compose up --build`.
- If redirect 307 logs lack user_id: call canonical path with trailing slash (e.g. `/tasks/`).

## Quickstart (Local Dev)

```bash
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
pip install -e .[dev]
uvicorn app.main:app --reload
```

Docs:

- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

Health & Ops:

- Liveness: GET /live -> {"status":"alive"}
- Readiness: GET /ready -> DB connectivity check
- Basic: GET /health

## .env Example

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=tasktracker
JWT_SECRET_KEY=CHANGEME_SUPER_SECRET
# Local direct connection (app in host, DB via localhost); in Docker the service name is db
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/tasktracker
```

## Docker

Build & run:

```bash
docker compose up --build
```

Migrations run automatically at container start (see `alembic_runner.py` + Dockerfile ENTRYPOINT).

If you recreate/drop the database volume, just start the stack again; Alembic reapplies migrations.

## Configuration

Environment variables (see `app/core/config.py`):

- PROJECT_NAME
- DATABASE_URL
- JWT_SECRET_KEY (required override in prod)
- ACCESS_TOKEN_EXPIRE_MINUTES
- ENV (dev|docker|prod)
- ALLOWED_ORIGINS

## Security Middleware

- CORS configurable via ALLOWED_ORIGINS
- Security headers (CSP, X-Frame-Options, etc.)
- Request timing header `X-Process-Time-ms`

## Testing

```bash
pytest
```

Uses a temporary SQLite test DB (`/tmp/test.db`) isolated from Postgres.

## Seeding Data

A seeding script provides base users (alice=admin, bob, carol) + 3 tasks each.

Inside the running app container (preferred):

```bash
docker compose exec app python -m seeds.seed_data --base
```

Add or ensure N tasks for a specific user:

```bash
docker compose exec app python -m seeds.seed_data --user-email alice@example.com --tasks 15
```

If you run the script directly and see `ModuleNotFoundError: No module named 'app'`, ensure you invoke it with `-m` so Python sets the project root on `sys.path`.

## Logging

Structured JSON logging to stdout (root + uvicorn) with fields:

```
{
  "ts": "2025-09-10T04:59:54.034350Z",
  "level": "INFO",
  "logger": "app",
  "msg": "request_end",
  "cid": "<correlation-uuid>",
  "method": "GET",
  "path": "/tasks/",
  "status": 200,
  "duration_ms": 13.86,
  "user_id": 4,
  "client_addr": "172.19.0.1"
}
```

Notes:

- `user_id` appears only after auth dependency runs (i.e. on the final routed request, not the 307 redirect). Call canonical paths with trailing slashes (`/tasks/`) to avoid an initial redirect log without `user_id`.
- Correlation ID also returned in header `X-Correlation-Id`.

## Common DB Tasks

List databases (inside DB container):

```bash
docker compose exec db psql -U postgres -d postgres -c "\\l"
```

Connect to current app DB:

```bash
docker compose exec db psql -U postgres -d $POSTGRES_DB
```

Re-seed after dropping DB: recreate (or let compose recreate volume), start containers, then run the seed commands again.

## Redirect Behavior

FastAPI by default redirects `/route` -> `/route/` (307). The first 307 log line won't have `user_id` because dependencies haven’t executed yet. To disable this, set `FastAPI(redirect_slashes=False)` and add both route variants if desired.

# Secure Task Tracker

Backend API built with FastAPI. Provides secure task management with JWT auth.

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

## Docker

Create a .env file (copy .env.example) and set strong values:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=secure_task_tracker
JWT_SECRET_KEY=CHANGEME_SUPER_SECRET
```

Build & run:
```bash
docker compose up --build
```
Migrations run automatically at container start.

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
- Security headers set (CSP default-src 'self', X-Frame-Options DENY, etc.)
- Request timing header X-Process-Time-ms

## Testing
```bash
pytest
```

## Roadmap
- Admin bootstrap script
- CI workflow (lint + tests)
- More negative tests & performance profiling
- Rate limiting & audit logging optional

## License
MIT

## Deployment (Render)
1. Push repository to GitHub.
2. In Render dashboard: New + Web Service -> Select repo.
3. Build settings:
   - Environment: Docker
   - Root Directory: (repo root)
   - Auto deploy: Yes
4. Add a Render Postgres instance (creates DATABASE_URL). Adjust to SQLAlchemy format if needed (ensure it starts with `postgresql+psycopg2://`).
5. Set Environment Variables:
   - DATABASE_URL
   - JWT_SECRET_KEY (strong random string)
   - ENV=prod
   - ACCESS_TOKEN_EXPIRE_MINUTES=30
   - ALLOWED_ORIGINS=*
6. Deploy. Health check path (optional): /live
7. Open https://<your-service>.onrender.com/docs for API docs.

Gunicorn workers: defined in Dockerfile (4). Adjust via env GUNICORN_WORKERS (future enhancement).

from fastapi import FastAPI, Depends
from app.api.routes import auth, users, tasks
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.db.session import get_db
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time

app = FastAPI(title=settings.PROJECT_NAME)

# CORS (adjust ALLOWED_ORIGINS in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOC_PATH_PREFIXES = ("/docs", "/redoc", "/openapi.json")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "0")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        # Relax CSP for docs so Swagger/ReDoc assets & inline styles/scripts load
        if request.url.path.startswith(DOC_PATH_PREFIXES):
            # Allow swagger/redoc external CDN assets
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
                "style-src 'self' 'unsafe-inline' https:; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https:; "
                "connect-src 'self' https:;"
            )
        else:
            csp = "default-src 'self'"
        response.headers["Content-Security-Policy"] = csp
        return response

class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response: Response = await call_next(request)
        duration = (time.time() - start) * 1000
        response.headers["X-Process-Time-ms"] = f"{duration:.2f}"
        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestTimingMiddleware)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/live")
async def liveness():
    return {"status": "alive"}


@app.get("/ready")
async def readiness(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")  # simple connectivity check
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

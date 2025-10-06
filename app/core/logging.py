import logging, sys, json, os
from datetime import datetime, timezone
from app.core.config import settings
from starlette.requests import Request
from typing import Optional, Dict, Any

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        data = {
            "ts": datetime.fromtimestamp(record.created, timezone.utc).isoformat().replace('+00:00', 'Z'),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }
        # Include common custom attributes if present
        for field in ["cid", "method", "path", "status", "duration_ms", "user_id", "client_addr"]:
            if hasattr(record, field):
                data[field] = getattr(record, field)
        # Uvicorn access log specific attributes
        if hasattr(record, "status_code") and "status" not in data:
            data["status"] = getattr(record, "status_code")
        if hasattr(record, "client_addr") and "client_addr" not in data:
            data["client_addr"] = getattr(record, "client_addr")
        if hasattr(record, "request_line"):
            rl = getattr(record, "request_line")  # e.g. "GET /path HTTP/1.1"
            try:
                method, remainder = rl.split(" ", 1)
                path = remainder.rsplit(" ", 1)[0]
                data.setdefault("method", method)
                data.setdefault("path", path)
            except Exception:
                data.setdefault("request_line", rl)
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)

def setup_logging():
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root = logging.getLogger()
    # Remove all existing handlers to avoid duplicates / default formatting
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level)
    # Normalize uvicorn / gunicorn loggers to propagate to root with JSON
    for name in ["uvicorn", "uvicorn.error", "uvicorn.access", "gunicorn.error", "gunicorn.access"]:
        lg = logging.getLogger(name)
        lg.handlers = []  # clear their default handlers
        lg.propagate = True
        lg.setLevel(level)

def log_business_step(
    step: str,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
    user_id: Optional[int] = None,
    level: str = "info"
):
    """
    Log business logic steps with consistent format
    
    Args:
        step: Description of the business step (e.g., "user_registration_start")
        details: Additional context data
        request: Request object to extract correlation ID
        user_id: User ID if available
        level: Log level (info, warning, error)
    """
    logger = logging.getLogger("business")
    
    extra_data = {
        "business_step": step,
        **(details or {})
    }
    
    # Add correlation ID from request if available
    if request and hasattr(request.state, 'correlation_id'):
        extra_data["cid"] = request.state.correlation_id
    
    # Add user ID
    if user_id:
        extra_data["user_id"] = user_id
    elif request and hasattr(request.state, 'user_id'):
        extra_data["user_id"] = request.state.user_id
    
    # Log at appropriate level
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(f"Business: {step}", extra=extra_data)

import logging, sys, json, os
from datetime import datetime
from app.core.config import settings

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        data = {
            "ts": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
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

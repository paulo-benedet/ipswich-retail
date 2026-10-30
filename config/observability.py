import json
import logging
import os
import time
import traceback
import uuid
from datetime import datetime, timezone

logger = logging.getLogger("retail")


class SafeJsonFormatter(logging.Formatter):
    """Allowlist fields; never serialize request bodies, URLs, headers or exception messages."""
    def format(self, record):
        event = getattr(record, "event", "application_error" if record.levelno >= logging.ERROR else "application_event")
        data = {"timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
                "level": record.levelname, "event": event}
        for key in ("request_id", "route", "status_code", "duration_ms"):
            if hasattr(record, key):
                data[key] = getattr(record, key)
        if record.exc_info:
            data["exception_type"] = record.exc_info[0].__name__
            data["frames"] = [{"file": os.path.basename(f.filename), "line": f.lineno, "function": f.name}
                              for f in traceback.extract_tb(record.exc_info[2])]
        return json.dumps(data)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.retail_id = str(uuid.uuid4())
        started = time.perf_counter()
        response = self.get_response(request)
        match = getattr(request, "resolver_match", None)
        logger.log(logging.ERROR if response.status_code >= 500 else logging.INFO, "request", extra={
            "event": "request_completed", "request_id": request.retail_id,
            "route": (match.url_name or "unnamed") if match else "unmatched",
            "status_code": response.status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        })
        response["X-Request-ID"] = request.retail_id
        return response

    def process_exception(self, request, exception):
        logger.error("request failure", exc_info=(type(exception), exception, exception.__traceback__),
                     extra={"event": "request_exception", "request_id": request.retail_id})

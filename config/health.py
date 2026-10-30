import logging
import os
import sys
import secrets
import psutil
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@never_cache
@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logging.getLogger("retail").exception("database health failed", extra={"event": "database_health_failed"})
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok", "revision": settings.APP_REVISION})


@never_cache
@require_GET
def metrics(request):
    supplied = request.headers.get("Authorization", "")
    if not settings.MONITORING_TOKEN or not secrets.compare_digest(supplied, "Bearer " + settings.MONITORING_TOKEN):
        return JsonResponse({"detail": "Unauthorized"}, status=401)
    try:
        process = psutil.Process()
        memory = process.memory_info().rss
        memory_kind = "resident"
    except (psutil.Error, OSError):
        # Some restricted Linux environments do not expose this PID through /proc.
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        memory = peak if sys.platform == "darwin" else peak * 1024
        memory_kind = "peak_resident"
    cpu = os.times()
    return JsonResponse({"scope": "responding_worker", "pid": os.getpid(),
                         "memory_bytes": memory, "memory_kind": memory_kind,
                         "cpu_seconds_total": round(cpu.user + cpu.system, 3)})

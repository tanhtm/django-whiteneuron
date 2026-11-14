"""
System status endpoints — kiểm tra nhanh thông tin & tình trạng hệ thống.

Endpoints (mount dưới ``api/system/``):

    GET version/  Public  — tên project, phiên bản package, Django, Python.
    GET health/   Public  — liveness probe, không chạm DB/cache (rất nhẹ).
    GET ready/    Public  — readiness probe: kiểm tra database, cache, celery broker.
                            200 nếu mọi check bắt buộc OK, ngược lại 503.
                            Chi tiết lỗi chỉ hiển thị cho superuser/token.
    GET info/     Admin   — thông tin runtime: uptime, host, pid, timezone,
                            database/cache backend, migration chưa chạy, ...

Cấu hình (settings):

    SYSTEM_API_READY_CHECKS  list[str]  mặc định ["database", "cache"]
                             thêm "celery" để kiểm tra Celery broker.
    SYSTEM_API_TOKEN         str | None nếu đặt, header ``X-System-Token`` hoặc
                             ``Authorization: Bearer <token>`` khớp token
                             cũng được xem như superuser (dùng cho monitoring).
"""

from __future__ import annotations

import hmac
import logging
import os
import platform
import socket
import sys
import time
from datetime import timedelta
from importlib.metadata import PackageNotFoundError, version as pkg_version

import django
from django.conf import settings
from django.core.cache import caches
from django.db import DEFAULT_DB_ALIAS, connections
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)

PACKAGE_NAME = "django-whiteneuron"
DEFAULT_READY_CHECKS = ("database", "cache")
CHECK_TIMEOUT_SECONDS = 2

_STARTED_AT = timezone.now()
_STARTED_MONOTONIC = time.monotonic()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_package_version() -> str:
    try:
        return pkg_version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "unknown"


def _is_privileged(request) -> bool:
    """Superuser, hoặc request mang SYSTEM_API_TOKEN hợp lệ.

    Không dùng ``is_staff`` vì trong whiteneuron mọi user mới (kể cả guest)
    đều mặc định ``is_staff=True``.
    """
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated and user.is_superuser:
        return True

    expected = getattr(settings, "SYSTEM_API_TOKEN", None)
    if not expected:
        return False
    provided = request.headers.get("X-System-Token", "")
    if not provided:
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            provided = auth[7:].strip()
    return bool(provided) and hmac.compare_digest(str(provided), str(expected))


def _json(data: dict, status: int = 200) -> JsonResponse:
    return JsonResponse(data, status=status, json_dumps_params={"ensure_ascii": False})


def _timed(fn):
    """Chạy một check, trả về dict {status, latency_ms[, error]}."""
    start = time.perf_counter()
    try:
        fn()
        result = {"status": "ok"}
    except Exception as exc:  # noqa: BLE001 — mọi lỗi đều là "fail"
        logger.warning("System check failed: %s", exc, exc_info=True)
        result = {"status": "error", "error": f"{exc.__class__.__name__}: {exc}"}
    result["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return result


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_database():
    conn = connections[DEFAULT_DB_ALIAS]
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()


def check_cache():
    cache = caches["default"]
    key = f"system:healthcheck:{os.getpid()}"
    token = str(time.time())
    cache.set(key, token, timeout=10)
    if cache.get(key) != token:
        raise RuntimeError("cache read-back mismatch")
    cache.delete(key)


def check_celery():
    broker_url = getattr(settings, "CELERY_BROKER_URL", None)
    if not broker_url:
        raise RuntimeError("CELERY_BROKER_URL is not configured")
    from kombu import Connection

    with Connection(broker_url, connect_timeout=CHECK_TIMEOUT_SECONDS) as conn:
        conn.ensure_connection(max_retries=1)


CHECKS = {
    "database": check_database,
    "cache": check_cache,
    "celery": check_celery,
}


def run_checks(names=None) -> dict:
    names = names or getattr(settings, "SYSTEM_API_READY_CHECKS", DEFAULT_READY_CHECKS)
    results = {}
    for name in names:
        fn = CHECKS.get(name)
        if fn is None:
            results[name] = {"status": "error", "error": "unknown check"}
            continue
        results[name] = _timed(fn)
    return results


def _pending_migrations() -> int | None:
    try:
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
        targets = executor.loader.graph.leaf_nodes()
        return len(executor.migration_plan(targets))
    except Exception:  # noqa: BLE001
        logger.warning("Cannot compute pending migrations", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@never_cache
@require_GET
def version_view(request):
    return _json({
        "name": getattr(settings, "NAME", None),
        "project": getattr(settings, "PROJECT_NAME", None),
        "version": getattr(settings, "APP_VERSION", None) or get_package_version(),
        "whiteneuron": get_package_version(),
        "django": django.get_version(),
        "python": platform.python_version(),
    })


@never_cache
@require_GET
def health_view(request):
    """Liveness: process còn sống & trả lời được request."""
    return _json({
        "status": "ok",
        "timestamp": timezone.now().isoformat(),
    })


@never_cache
@require_GET
def ready_view(request):
    """Readiness: các dependency bắt buộc đều hoạt động."""
    checks = run_checks()
    healthy = all(c["status"] == "ok" for c in checks.values())

    if not _is_privileged(request):
        for c in checks.values():
            c.pop("error", None)

    return _json(
        {
            "status": "ok" if healthy else "error",
            "timestamp": timezone.now().isoformat(),
            "checks": checks,
        },
        status=200 if healthy else 503,
    )


@never_cache
@require_GET
def info_view(request):
    """Thông tin runtime chi tiết — chỉ dành cho superuser / token."""
    if not _is_privileged(request):
        return _json({"detail": "Forbidden."}, status=403)

    db = connections[DEFAULT_DB_ALIAS]
    cache_cfg = getattr(settings, "CACHES", {}).get("default", {})
    uptime = timedelta(seconds=int(time.monotonic() - _STARTED_MONOTONIC))

    return _json({
        "name": getattr(settings, "NAME", None),
        "project": getattr(settings, "PROJECT_NAME", None),
        "version": getattr(settings, "APP_VERSION", None) or get_package_version(),
        "versions": {
            "whiteneuron": get_package_version(),
            "django": django.get_version(),
            "python": platform.python_version(),
        },
        "runtime": {
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
            "platform": platform.platform(),
            "python_implementation": platform.python_implementation(),
            "executable": sys.executable,
            "started_at": _STARTED_AT.isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime": str(uptime),
        },
        "settings": {
            "debug": settings.DEBUG,
            "time_zone": settings.TIME_ZONE,
            "server_time": timezone.now().isoformat(),
            "language_code": settings.LANGUAGE_CODE,
            "allowed_hosts": list(settings.ALLOWED_HOSTS),
        },
        "database": {
            "vendor": db.vendor,
            "engine": db.settings_dict.get("ENGINE"),
            "pending_migrations": _pending_migrations(),
        },
        "cache": {
            "backend": cache_cfg.get("BACKEND"),
        },
        "celery": {
            "configured": bool(getattr(settings, "CELERY_BROKER_URL", None)),
        },
        "checks": run_checks(),
    })

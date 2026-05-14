from __future__ import annotations

from time import monotonic

from django.conf import settings
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse

_CACHE_TTL_SECONDS = 5.0
_last_checked_at = 0.0
_pending_migrations = False


def has_pending_migrations() -> bool:
    global _last_checked_at, _pending_migrations

    now = monotonic()
    if now - _last_checked_at < _CACHE_TTL_SECONDS:
        return _pending_migrations

    executor = MigrationExecutor(connections["default"])
    targets = executor.loader.graph.leaf_nodes()
    _pending_migrations = bool(executor.migration_plan(targets))
    _last_checked_at = now
    return _pending_migrations


class PendingMigrationsBlockerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            settings.DEBUG
            and getattr(settings, "DEV_BLOCK_ON_PENDING_MIGRATIONS", True)
            and request.path.startswith("/api/")
            and has_pending_migrations()
        ):
            return JsonResponse(
                {
                    "detail": (
                        "Pending database migrations detected. Restart the dev backend "
                        "after applying migrations."
                    )
                },
                status=503,
            )

        return self.get_response(request)

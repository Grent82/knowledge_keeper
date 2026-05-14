from unittest.mock import patch
import json

from django.http import HttpResponse
from django.test import RequestFactory, override_settings

from apps.common.middleware import PendingMigrationsBlockerMiddleware


def _ok_response(_request):
    return HttpResponse("ok")


@override_settings(DEBUG=True, DEV_BLOCK_ON_PENDING_MIGRATIONS=True)
@patch("apps.common.middleware.has_pending_migrations", return_value=True)
def test_pending_migrations_blocker_returns_503_for_api_requests(_mock_pending):
    middleware = PendingMigrationsBlockerMiddleware(_ok_response)
    request = RequestFactory().get("/api/knowledge-notes/")

    response = middleware(request)

    assert response.status_code == 503
    assert json.loads(response.content) == {
        "detail": "Pending database migrations detected. Restart the dev backend after applying migrations."
    }


@override_settings(DEBUG=True, DEV_BLOCK_ON_PENDING_MIGRATIONS=True)
@patch("apps.common.middleware.has_pending_migrations", return_value=False)
def test_pending_migrations_blocker_allows_requests_when_schema_is_current(_mock_pending):
    middleware = PendingMigrationsBlockerMiddleware(_ok_response)
    request = RequestFactory().get("/api/system/health/")

    response = middleware(request)

    assert response.status_code == 200
    assert response.content == b"ok"


@override_settings(DEBUG=False, DEV_BLOCK_ON_PENDING_MIGRATIONS=True)
@patch("apps.common.middleware.has_pending_migrations", return_value=True)
def test_pending_migrations_blocker_is_disabled_outside_debug(_mock_pending):
    middleware = PendingMigrationsBlockerMiddleware(_ok_response)
    request = RequestFactory().get("/api/system/health/")

    response = middleware(request)

    assert response.status_code == 200
    assert response.content == b"ok"

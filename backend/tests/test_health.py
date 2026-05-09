from rest_framework.test import APIRequestFactory

from apps.system.views import health_view


def test_health_endpoint_returns_ok():
    factory = APIRequestFactory()
    request = factory.get("/api/system/health/")

    response = health_view(request)

    assert response.status_code == 200
    assert response.data == {"status": "ok"}

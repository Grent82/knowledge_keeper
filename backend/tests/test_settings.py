from django.conf import settings


def test_csrf_trusted_origins_include_ipv6_localhost() -> None:
    assert "http://[::1]:3000" in settings.CSRF_TRUSTED_ORIGINS

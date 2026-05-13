import importlib
import os

from django.conf import settings

import config.settings as settings_module


def test_csrf_trusted_origins_include_ipv6_localhost() -> None:
    assert "http://[::1]:3000" in settings.CSRF_TRUSTED_ORIGINS


def test_knowledge_note_provider_setting_exists() -> None:
    assert settings.KNOWLEDGE_NOTE_PROVIDER in {"stub", "openai_compatible"}


def test_csrf_trusted_origins_keep_loopback_entries_when_env_override_is_narrow(
    monkeypatch,
) -> None:
    original = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS")
    monkeypatch.setenv("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:3000,http://localhost:3001")

    reloaded = importlib.reload(settings_module)
    assert "http://127.0.0.1:3001" in reloaded.CSRF_TRUSTED_ORIGINS
    assert "http://[::1]:3001" in reloaded.CSRF_TRUSTED_ORIGINS

    if original is None:
        monkeypatch.delenv("DJANGO_CSRF_TRUSTED_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("DJANGO_CSRF_TRUSTED_ORIGINS", original)
    importlib.reload(settings_module)

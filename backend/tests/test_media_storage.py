import importlib
import sys

from django.conf import settings

import config.settings as settings_module


def test_local_provider_save_copies_file(tmp_path) -> None:
    from apps.media_library.storage import LocalMediaStorageProvider

    source_path = tmp_path / "source.txt"
    source_path.write_text("hello media storage")
    relative_path = "nested/copied.txt"

    provider = LocalMediaStorageProvider(tmp_path)

    stored_path = provider.save(relative_path, str(source_path))

    destination = tmp_path / relative_path
    assert stored_path == relative_path
    assert destination.exists()
    assert destination.read_text() == "hello media storage"


def test_local_provider_delete_removes_file(tmp_path) -> None:
    from apps.media_library.storage import LocalMediaStorageProvider

    source_path = tmp_path / "source.txt"
    source_path.write_text("delete me")
    relative_path = "nested/delete-me.txt"
    provider = LocalMediaStorageProvider(tmp_path)

    provider.save(relative_path, str(source_path))
    provider.delete(relative_path)

    assert not (tmp_path / relative_path).exists()


def test_local_provider_delete_missing_file_is_silent(tmp_path) -> None:
    from apps.media_library.storage import LocalMediaStorageProvider

    provider = LocalMediaStorageProvider(tmp_path)

    provider.delete("missing/file.txt")



def test_local_provider_get_url_contains_relative_path(tmp_path) -> None:
    from apps.media_library.storage import LocalMediaStorageProvider

    relative_path = "nested/file.txt"
    provider = LocalMediaStorageProvider(tmp_path)

    url = provider.get_url(relative_path)

    assert settings.MEDIA_URL in url
    assert relative_path in url



def test_get_storage_provider_returns_local_by_default(monkeypatch) -> None:
    from apps.media_library.storage import LocalMediaStorageProvider, get_storage_provider

    monkeypatch.delenv("MEDIA_STORAGE_PROVIDER", raising=False)
    reloaded = importlib.reload(settings_module)
    monkeypatch.setattr(
        settings,
        "MEDIA_STORAGE_PROVIDER",
        reloaded.MEDIA_STORAGE_PROVIDER,
        raising=False,
    )

    provider = get_storage_provider()

    assert isinstance(provider, LocalMediaStorageProvider)



def test_s3_provider_not_imported_when_local(monkeypatch) -> None:
    monkeypatch.delenv("MEDIA_STORAGE_PROVIDER", raising=False)

    original_boto3 = sys.modules.pop("boto3", None)
    original_storage = sys.modules.pop("apps.media_library.storage", None)

    try:
        importlib.import_module("apps.media_library.storage")

        assert "boto3" not in sys.modules
    finally:
        if original_storage is not None:
            sys.modules["apps.media_library.storage"] = original_storage
        else:
            sys.modules.pop("apps.media_library.storage", None)

        if original_boto3 is not None:
            sys.modules["boto3"] = original_boto3

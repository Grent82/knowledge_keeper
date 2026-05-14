import os
import urllib.parse
from pathlib import Path


def env_list(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


def merge_env_list(name: str, defaults: list[str]) -> list[str]:
    merged: list[str] = []
    for item in [*defaults, *env_list(name, "")]:
        if item and item not in merged:
            merged.append(item)
    return merged

BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me-only-for-dev")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = merge_env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://[::1]:3000",
        "http://[::1]:3001",
        "http://[::1]:3002",
        "http://[::1]:3003",
    ],
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.accounts",
    "apps.access_control",
    "apps.coach",
    "apps.media_library",
    "apps.playback",
    "apps.knowledge_notes",
    "apps.system",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "apps.common.middleware.PendingMigrationsBlockerMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

_database_url = os.getenv("DATABASE_URL")
if _database_url:
    _parsed = urllib.parse.urlparse(_database_url)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _parsed.path.lstrip("/"),
            "USER": _parsed.username,
            "PASSWORD": _parsed.password,
            "HOST": _parsed.hostname,
            "PORT": str(_parsed.port or 5432),
            "CONN_MAX_AGE": 600,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
        }
    }

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR.parent / "var" / "static"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR.parent / "var" / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
# Run tasks synchronously in dev when no broker is available
CELERY_TASK_ALWAYS_EAGER = (
    os.getenv("CELERY_TASK_ALWAYS_EAGER", "true" if DEBUG else "false").lower()
    == "true"
)
CELERY_TASK_EAGER_PROPAGATES = True

TRANSCRIPTION_PROVIDER = os.getenv("TRANSCRIPTION_PROVIDER", "stub")

# faster-whisper settings
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")  # tiny, base, small, medium, large-v3
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_MODEL_DIR = os.getenv("WHISPER_MODEL_DIR", str(BASE_DIR.parent / "var" / "whisper_models"))

# AI / Summary provider
KNOWLEDGE_NOTE_PROVIDER = os.getenv("KNOWLEDGE_NOTE_PROVIDER", "stub")
SUMMARY_PROVIDER = os.getenv("SUMMARY_PROVIDER", "stub")
AI_HUB_BASE_URL = os.getenv("AI_HUB_BASE_URL", "")
AI_HUB_API_KEY = os.getenv("AI_HUB_API_KEY", "")
AI_HUB_MODEL = os.getenv("AI_HUB_MODEL", "qwen-3.5-122b-sovereign")
RETRIEVAL_PROVIDER = os.getenv("RETRIEVAL_PROVIDER", "stub")
CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "stub")
DEV_BLOCK_ON_PENDING_MIGRATIONS = (
    os.getenv("DEV_BLOCK_ON_PENDING_MIGRATIONS", "true" if DEBUG else "false").lower() == "true"
)

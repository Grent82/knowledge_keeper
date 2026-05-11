FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend/src

RUN pip install --upgrade pip --no-cache-dir && \
    apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies before copying source for layer caching
COPY backend/pyproject.toml backend/
RUN pip install --no-cache-dir -e backend/

# ── dev stage ──────────────────────────────────────────────────────────────────
FROM base AS dev

COPY backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 9000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "backend/manage.py", "runserver", "0.0.0.0:9000"]

# ── production stage ───────────────────────────────────────────────────────────
FROM base AS prod

RUN pip install --no-cache-dir gunicorn

COPY backend/ backend/
COPY backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 9000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:9000", "--workers", "4", "--timeout", "120"]

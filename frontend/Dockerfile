FROM node:22-alpine AS base

WORKDIR /app

RUN npm install -g pnpm

# Install dependencies (separate layer for caching)
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY frontend/package.json frontend/
RUN pnpm install --frozen-lockfile

# ── dev stage ──────────────────────────────────────────────────────────────────
FROM base AS dev

EXPOSE 3000
CMD ["pnpm", "--filter", "@knowledge-keeper/frontend", "dev", "--", "--host"]

# ── builder stage ──────────────────────────────────────────────────────────────
FROM base AS builder

COPY frontend/ frontend/
RUN pnpm --filter @knowledge-keeper/frontend build

# ── production stage (nginx) ───────────────────────────────────────────────────
FROM nginx:1.27-alpine AS prod

COPY --from=builder /app/frontend/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

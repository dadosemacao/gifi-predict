# Imagem gifi-serving (API FastAPI + SPA) — bake de artefatos de release
# Autor: Emerson Antônio
# Data: 2026-07-14

# syntax=docker/dockerfile:1

ARG RELEASE_RUN_ID

FROM node:20-bookworm-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
ARG RELEASE_RUN_ID
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin gifi

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

COPY config ./config
COPY config/serving.docker.yaml ./config/serving.yaml
COPY docs/kb ./docs/kb
COPY database/serving_audit ./database/serving_audit
COPY --from=web /web/dist ./web/dist

COPY releases/${RELEASE_RUN_ID}/models ./models
COPY releases/${RELEASE_RUN_ID}/reports ./reports

RUN mkdir -p /app/logs && chown -R gifi:gifi /app
USER gifi
EXPOSE 8000
# Typer com um único comando: entrypoint é `serve` (não `serve run`)
CMD ["sh", "-c", "serve --host 0.0.0.0 --port ${PORT:-8000}"]

# AEGIS backend image: the API, the migration job and both worker roles
# (DECISIONS.md D-051). Build from the repository root:
#
#   docker build -f infrastructure/docker/backend.Dockerfile -t aegis/backend:local .
#
# backend.Dockerfile.dockerignore limits the build context to the files the
# image needs, so .env files and secrets can never be copied in.
#
# Local builds only: images must not be published or distributed until the
# distribution-compliance review is complete (D-059, THIRD_PARTY_NOTICES.md).

# python:3.11.18-slim-trixie (multi-architecture index digest)
ARG PYTHON_IMAGE=python:3.11.18-slim-trixie@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535

# --- Build stage: install the locked runtime dependencies into a venv --------
FROM ${PYTHON_IMAGE} AS build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_NO_INPUT=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN python -m venv /opt/venv
COPY apps/backend/requirements.lock /tmp/requirements.lock
# Exact versions with SHA-256 hashes; binary wheels only, so no package can
# run build code during installation. The installer itself is then removed:
# the application does not need it at runtime.
RUN /opt/venv/bin/pip install --require-hashes --only-binary=:all: -r /tmp/requirements.lock \
    && /opt/venv/bin/python -m pip uninstall --yes pip setuptools

# --- Runtime stage ------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS runtime

LABEL org.opencontainers.image.title="AEGIS backend" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.source="https://github.com/mohamedalieujagitay/AEGIS"

# Unprivileged user with no home directory and no login shell. The base
# image's own packaging tools are removed: nothing is installed at runtime,
# and the application uses only the virtual environment.
RUN groupadd --system --gid 10001 aegis \
    && useradd --system --uid 10001 --gid aegis --no-create-home \
       --home-dir /nonexistent --shell /usr/sbin/nologin aegis \
    && python -m pip uninstall --yes --root-user-action=ignore pip setuptools wheel

COPY --from=build /opt/venv /opt/venv

WORKDIR /app
# Application code is owned by root and read-only for the aegis user.
COPY apps/backend/alembic.ini ./alembic.ini
COPY apps/backend/migrations ./migrations
COPY apps/backend/app ./app
RUN /opt/venv/bin/python -m compileall -q /app/app /app/migrations

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER 10001:10001
EXPOSE 8000

# The API. Compose adds --forwarded-allow-ips for the frontend proxy only.
# --no-server-header: never disclose the server software (D-042).
# --no-access-log: requests are logged by the application without query strings.
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--no-access-log", "--timeout-graceful-shutdown", "20"]

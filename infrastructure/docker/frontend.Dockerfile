# AEGIS frontend image: the built single-page application served by
# unprivileged nginx, which also proxies /api/ to the backend on the same
# origin (DECISIONS.md D-051, D-052). Build from the repository root:
#
#   docker build -f infrastructure/docker/frontend.Dockerfile -t aegis/frontend:local .
#
# Local builds only: images must not be published or distributed (D-059).

# node:22.23.5-trixie-slim and nginxinc/nginx-unprivileged:1.30.6-alpine
# (multi-architecture index digests)
ARG NODE_IMAGE=node:22.23.5-trixie-slim@sha256:68c76cfad89921b927eae28ba21407475e29d0ce450afcdbe70c1532db042b64
ARG NGINX_IMAGE=nginxinc/nginx-unprivileged:1.30.6-alpine@sha256:f5116ed4606f3eb015dd4a8e28cb9b351476dc0ad4bc6e9f93b19cec130cdf03

# --- Build stage --------------------------------------------------------------
FROM ${NODE_IMAGE} AS build

ENV NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_AUDIT=false

WORKDIR /src
COPY apps/frontend/package.json apps/frontend/package-lock.json ./
# picomatch is installed from a patched copy (GHSA-fc5q-39xc-vjpf), so the
# vendored package and the patch tool must be present before installing.
COPY apps/frontend/vendor/ ./vendor/
COPY apps/frontend/scripts/picomatch-security-patch.mjs apps/frontend/scripts/picomatch-guard.js.txt ./scripts/
# Exact versions from the lock file. Install scripts are disabled: no
# dependency needs one, and none may run code during the build. The picomatch
# patch is our own script, run explicitly, and the build fails if any installed
# copy of picomatch is still unpatched.
RUN npm ci --ignore-scripts     && node scripts/picomatch-security-patch.mjs apply     && node scripts/picomatch-security-patch.mjs verify

COPY apps/frontend/ ./
RUN npm run build

# --- Runtime stage ------------------------------------------------------------
FROM ${NGINX_IMAGE} AS runtime

LABEL org.opencontainers.image.title="AEGIS frontend" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.source="https://github.com/mohamedalieujagitay/AEGIS"

# Configuration is baked in, so the container can run with a read-only root
# filesystem. The image's entrypoint scripts that edit configuration at
# startup (IPv6 listen, templates) are not needed.
COPY infrastructure/docker/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY infrastructure/docker/nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /src/dist /usr/share/nginx/html

ENV NGINX_ENTRYPOINT_QUIET_LOGS=1

# The base image runs as nginx (UID 101) and listens on 8080.
USER 101:101
EXPOSE 8080

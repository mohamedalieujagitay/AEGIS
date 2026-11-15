# AEGIS — Third-Party Notices

AEGIS uses or plans to use third-party software and libraries.

This document is the dependency licensing register for AEGIS. It records each planned dependency, its licence as currently understood and its review status. Attribution notices required for distribution will be added as dependencies complete review.

## Review Status Definitions

| Status | Meaning |
|---|---|
| **Proposed** | Suggested for use. Not yet approved as part of the stack. |
| **Planned** | Approved as part of the stack. Licence review not yet completed. |
| **Reviewed** | Licence review completed for a specific version and distribution. |
| **Approved** | Reviewed and accepted for inclusion in a release. |
| **Deferred** | Not approved for the current release. Requires separate evaluation. |

**Only one licence review is complete:** psycopg 3.3.9 for Windows (see "psycopg Licence Review" below). All other licences below are preliminary and must be verified against the exact version and distribution selected.

## Dependency Policy

Before introducing a dependency, contributors must review:

- License compatibility.
- Security history.
- Maintenance status.
- Dependency requirements, including transitive dependencies.
- Redistribution obligations.

Running a tool as an external process is not assumed to resolve licensing obligations.

## Core Technologies

| Technology | Purpose | License (preliminary) | Status | Notes |
|---|---|---|---|---|
| Python 3.11 | Backend language | PSF-2.0 | Planned | |
| FastAPI 0.163 | Backend framework | MIT | Planned | Installed in `apps/backend`. Requires `opentelemetry-api` (see Backend Packages). |
| Uvicorn 0.54 | ASGI server | BSD-3-Clause | **Approved** | Approved in the Phase 1.3 Bundle 1 review. Run with `--no-server-header` in deployments (DECISIONS.md D-042). |
| SQLAlchemy 2.1 | ORM | MIT | Planned | Installed (2.1.8) in `apps/backend`. |
| Alembic 1.20 | Database migrations | MIT | Planned | Installed (1.20.1) in `apps/backend`. |
| Celery | Background processing | BSD-3-Clause | Planned | Transitive dependencies (for example kombu) are recorded during Phase 01.3. |
| PostgreSQL | Database | PostgreSQL License | Planned | |
| Valkey | Message broker | BSD-3-Clause | Planned | Compatibility with Celery's Redis transport is **not yet verified**; to be tested in Phase 01. |
| React | Frontend framework | MIT | Planned | |
| TypeScript 7 | Frontend language | Apache-2.0 | Planned | Compatibility with linting and testing tools to be tested (DECISIONS.md D-026). |
| Tailwind CSS 4 | Styling | MIT | Planned | Installed through the official Vite plugin (see Frontend Packages). |
| Node.js 22 (>=22.22.0) | Frontend toolchain runtime | MIT | Planned | Not redistributed by AEGIS. Bundles third-party components under their own licences. |
| npm | Frontend package manager | Artistic-2.0 | Planned | Bundled with Node.js. Not redistributed by AEGIS. |
| Docker Engine (Moby) | Container runtime | Apache-2.0 | Planned | Not redistributed by AEGIS. |
| Docker Compose | Service orchestration | Apache-2.0 | Planned | Not redistributed by AEGIS. |
| Docker Desktop | Container runtime on Windows and macOS | Proprietary (Docker Subscription Service Agreement) | Planned | Not redistributed by AEGIS. Free for personal use, education and small businesses; larger organisations require a paid subscription. Users are responsible for their own licence. |

### Why Valkey instead of Redis

Redis 7.4 and later are licensed under RSALv2/SSPLv1, and Redis 8 adds AGPLv3 as an option. Valkey is a BSD-3-Clause fork that is designed to be protocol-compatible with Redis. AEGIS has selected Valkey as its message broker (DECISIONS.md D-009), subject to the compatibility verification noted above.

## Python Libraries

| Library | Purpose | License (preliminary) | Status | Notes |
|---|---|---|---|---|
| psycopg 3 (`psycopg[binary]`) | PostgreSQL driver | LGPL-3.0-only | **Reviewed (Windows)** | Installed (3.3.9, with `psycopg-binary` 3.3.9) in `apps/backend`. Used unmodified as a separately installed library. Windows wheel reviewed: bundles libpq 18.4 and OpenSSL 3.6.5. **Linux wheel review pending (task 1.5).** See "psycopg Licence Review". |
| pydantic | Data validation | MIT | Planned | Installed (2.14.3). |
| pydantic-settings | Configuration management | MIT | Planned | Installed (2.16.3). |
| argon2-cffi | Argon2id password hashing | MIT | Planned | |
| cryptography | Ed25519 job signing | Apache-2.0 OR BSD-3-Clause | Planned | Binary wheels bundle OpenSSL; verify during review. |
| redis-py | Client used by Celery to connect to Valkey | MIT | Planned | |
| import-linter | Architectural import contracts | BSD-2-Clause | Planned | Development dependency only. |

## Backend Packages

Installed in the backend virtual environment from `apps/backend/pyproject.toml` (Python 3.11).

Runtime, required by FastAPI, pydantic-settings and Uvicorn:

- starlette (BSD-3-Clause), anyio (MIT), annotated-doc (MIT), annotated-types (MIT), pydantic-core (MIT), typing-inspection (MIT), typing-extensions (PSF-2.0), python-dotenv (BSD-3-Clause), click (BSD-3-Clause), h11 (MIT), idna (BSD-3-Clause).
- **opentelemetry-api (Apache-2.0)**, a required dependency of FastAPI 0.163. It is the instrumentation API only: without an OpenTelemetry SDK and exporter, which AEGIS does not install, it records and sends nothing. This is consistent with the no-telemetry requirement (PRD §4.6).

Development only, required by Pytest and httpx2:

- iniconfig (MIT), pluggy (MIT), packaging (Apache-2.0 OR BSD-2-Clause), Pygments (BSD-2-Clause), colorama (BSD-3-Clause, Windows), httpcore2 (BSD-3-Clause), truststore (MIT).

Database, required by SQLAlchemy, Alembic and psycopg:

- Mako (MIT), MarkupSafe (BSD-3-Clause), tzdata (Apache-2.0; installed on Windows by psycopg).
- psycopg-binary (LGPL-3.0-only) bundles libpq 18.4 (PostgreSQL License) and OpenSSL 3.6.5 (Apache-2.0) in the Windows wheel; see "psycopg Licence Review".

Build only: setuptools (MIT).

## psycopg Licence Review

Engineering review of the installed packages, not legal advice. Reviewed on 2026-11-15.

**Scope:** `psycopg` 3.3.9 and `psycopg-binary` 3.3.9, wheel for CPython 3.11 on 64-bit Windows (`cp311-win_amd64`).

| Component | Version (measured) | Licence | Copyright | Licence text in the wheel |
|---|---|---|---|---|
| psycopg (Python code) | 3.3.9 | LGPL-3.0-only | Daniele Varrazzo and contributors | Yes |
| psycopg-binary (compiled extension) | 3.3.9 | LGPL-3.0-only | Daniele Varrazzo and contributors | Yes (same text) |
| libpq, bundled | 18.4 (build and runtime) | PostgreSQL License | PostgreSQL Global Development Group; Regents of the University of California | No |
| OpenSSL (libssl-3, libcrypto-3), bundled | 3.6.5 | Apache-2.0 | The OpenSSL Project Authors | No |

Findings:

- The bundled libraries form a closed set: libpq depends only on the bundled OpenSSL, and OpenSSL only on Windows system libraries. No Kerberos, LDAP, zlib or iconv library is bundled.
- AEGIS uses psycopg unmodified, as a separately installed package loaded through Python's import mechanism. AEGIS's own code remains Apache-2.0, which is compatible with this use of an LGPL-3.0 library.

Obligations:

- **Current distribution (source code only):** AEGIS declares psycopg as a dependency and users install it from PyPI. AEGIS does not distribute psycopg, libpq or OpenSSL, so their redistribution obligations do not apply to AEGIS.
- **If AEGIS distributes these binaries** (for example in a published container image):
  - LGPL-3.0 (psycopg): state prominently that psycopg is used and is covered by the LGPL; include the GPL-3.0 and LGPL-3.0 texts; keep psycopg replaceable (a separately installed package satisfies this); and provide the corresponding source of the distributed psycopg version (for example its source distribution), as required for conveying object code.
  - PostgreSQL License (libpq): keep the copyright notice and permission paragraph with every copy.
  - Apache-2.0 (OpenSSL): include a copy of the licence and keep its notices.
  - The libpq and OpenSSL licence texts are not in the wheel; AEGIS must supply them itself.
- **If psycopg is modified** (not planned): the modified source must be made available under the LGPL-3.0.

**Pending:** the Linux (manylinux) wheels used in containers are built separately and may bundle additional libraries (for example Kerberos, SASL or LDAP). Review them in task 1.5, before container images are built or distributed.

## Frontend Packages

Versions as installed in `apps/frontend/package-lock.json`.

| Package | Purpose | License (preliminary) | Status | Notes |
|---|---|---|---|---|
| react 19.3.1 | UI library | MIT | Planned | Shipped in the production bundle. |
| react-dom 19.3.1 | React DOM renderer | MIT | Planned | Shipped in the production bundle. |
| scheduler 0.28.0 | React dependency | MIT | Planned | Transitive; shipped in the production bundle. |
| vite 8.3.8 | Build tool and development server | MIT | Planned | Development only. |
| @vitejs/plugin-react 6.3.0 | React support for Vite | MIT | Planned | Development only. |
| @types/react, @types/react-dom, @types/node | Type definitions | MIT | Planned | Development only. |
| react-router 8.5.1 | Routing | MIT | Planned | Shipped in the production bundle. |
| @remix-run/route-pattern 0.22.1 | React Router dependency | MIT | Planned | Transitive; shipped in the production bundle. |
| cookie-es 3.1.1 | React Router dependency | MIT | Planned | Transitive; shipped in the production bundle. |
| tailwindcss 4.3.5 | Utility-first CSS framework | MIT | Planned | Development only. Generates CSS at build time; only the generated CSS is shipped. |
| @tailwindcss/vite 4.3.5 | Official Tailwind CSS integration for Vite | MIT | Planned | Development only. |
| oxlint 1.93.0 | Linter | MIT | Planned | Development only. Platform-specific binaries (`@oxlint/binding-*`, MIT); bundled components to be verified during review. |
| oxlint-tsgolint 7.0.2007 | Type-aware lint rules for Oxlint, built on TypeScript 7 | MIT | Planned | Development only. Platform-specific binaries (`@oxlint-tsgolint/*`, MIT); bundled components to be verified during review. |
| prettier 3.10.1 | Code formatter | MIT | Planned | Development only. |
| prettier-plugin-tailwindcss 0.8.1 | Tailwind CSS class sorting for Prettier | MIT | Planned | Development only. |

Transitive development dependencies (build time only, not shipped in the production bundle):

- rolldown, postcss, picomatch, tinyglobby, fdir, nanoid, csstype, undici-types and the platform-specific TypeScript and rolldown binaries: MIT or Apache-2.0.
- source-map-js: BSD-3-Clause. picocolors: ISC. detect-libc: Apache-2.0. tslib: 0BSD.
- Tailwind CSS build dependencies: @tailwindcss/node, @tailwindcss/oxide and its platform-specific binaries, enhanced-resolve, jiti, magic-string, tapable and @jridgewell/*: MIT.
- graceful-fs: BlueOak-1.0.0 (Blue Oak Model License, a permissive licence).
- **lightningcss (MPL-2.0)**, a CSS transformer used by Vite and Tailwind CSS. MPL-2.0 is a file-level copyleft licence. It is used unmodified as a build tool and is not included in the shipped bundle. **Requires licence review.**
- Some optional WebAssembly fallback packages (`@emnapi/*`) are pre-release versions. They are not installed on Windows, macOS or Linux x64.

## Testing Tools

| Tool | Purpose | License (preliminary) | Status | Notes |
|---|---|---|---|---|
| Pytest 9.2 | Backend tests | MIT | Planned | Development dependency only. Installed in `apps/backend`; full configuration in task 1.6. |
| httpx2 2.16 | HTTP client used by the FastAPI/Starlette TestClient | BSD-3-Clause | **Approved** | Approved in the Phase 1.3 Bundle 1 review. Development dependency only. Starlette 1.10 deprecates `httpx` for its TestClient in favour of `httpx2` (same author, Pydantic organisation). |
| Vitest | Frontend unit tests | MIT | Planned | Development dependency only. |
| React Testing Library | Frontend component tests | MIT | Planned | Development dependency only. |
| Playwright | End-to-end tests | Apache-2.0 | Planned | Development dependency only. Downloaded browser binaries carry their own licences. |

## Container Images

| Image | Purpose | License (preliminary) | Status | Notes |
|---|---|---|---|---|
| PostgreSQL | Database | PostgreSQL License | Planned | Base OS packages carry their own licences. |
| Valkey | Message broker | BSD-3-Clause | Planned | Base OS packages carry their own licences. |
| Python 3.11 (Debian-based) | Backend and worker base image | PSF-2.0, plus base OS package licences | Planned | The Debian base image includes GPL-licensed packages. Publishing only a Dockerfile does not redistribute them. **If AEGIS publishes prebuilt images, source-availability obligations for those packages apply** and must be addressed before publishing. |

## Not Yet Selected

The following have not been chosen and are therefore not listed as dependencies:

- Python lint, formatting and type-checking tools (Phase 01.6).
- Python dependency locking tool (Phase 01).
- DNS library (Phase 03).
- PDF generation library (Phase 05).
- Frontend data-fetching library.

## Security Assessment Integrations

| Tool | License | Status | Notes |
|---|---|---|---|
| Nmap | Nmap Public Source License (NPSL) | Deferred | The NPSL addresses software designed to execute Nmap and parse its results. Not bundled or integrated in the MVP. |
| Scapy | GPL-2.0 | Deferred | Not included in the MVP. |
| OWASP ZAP | Apache-2.0 | Deferred | Candidate for an optional, isolated integration after v0.1.0. |

## License Verification

The licences listed above are preliminary references.

The exact licence and redistribution obligations must be verified against the selected dependency version and distribution before release.

This document must be updated whenever dependencies are added, removed or upgraded.

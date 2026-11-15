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

**No dependency has completed licence review yet.** The licences below are preliminary and must be verified against the exact version and distribution selected. Full dependency approval happens during Phase 01.3.

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
| FastAPI | Backend framework | MIT | Planned | |
| Uvicorn | ASGI server | BSD-3-Clause | **Proposed** | Pending approval in Phase 01.3. |
| SQLAlchemy 2.x | ORM | MIT | Planned | |
| Alembic | Database migrations | MIT | Planned | |
| Celery | Background processing | BSD-3-Clause | Planned | Transitive dependencies (for example kombu) are recorded during Phase 01.3. |
| PostgreSQL | Database | PostgreSQL License | Planned | |
| Valkey | Message broker | BSD-3-Clause | Planned | Compatibility with Celery's Redis transport is **not yet verified**; to be tested in Phase 01. |
| React | Frontend framework | MIT | Planned | |
| TypeScript 7 | Frontend language | Apache-2.0 | Planned | Compatibility with linting and testing tools to be tested (DECISIONS.md D-026). |
| Tailwind CSS | Styling | MIT | Planned | Not yet installed; integrated in a later Phase 01.2 task. |
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
| psycopg 3 | PostgreSQL driver | LGPL-3.0 | Planned | **Requires licence review.** Intended to be used unmodified as a separately installed library. The `psycopg[binary]` distribution bundles libpq (PostgreSQL License) and OpenSSL (Apache-2.0); bundled components and their versions must be verified during review. |
| pydantic | Data validation | MIT | Planned | |
| pydantic-settings | Configuration management | MIT | Planned | |
| argon2-cffi | Argon2id password hashing | MIT | Planned | |
| cryptography | Ed25519 job signing | Apache-2.0 OR BSD-3-Clause | Planned | Binary wheels bundle OpenSSL; verify during review. |
| redis-py | Client used by Celery to connect to Valkey | MIT | Planned | |
| import-linter | Architectural import contracts | BSD-2-Clause | Planned | Development dependency only. |

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
| react-router 8 | Routing | MIT | Planned | **Not yet installed**; installed during the routing task. |

Transitive development dependencies (build time only, not shipped in the production bundle):

- rolldown, postcss, picomatch, tinyglobby, fdir, nanoid, csstype, undici-types and the platform-specific TypeScript and rolldown binaries: MIT or Apache-2.0.
- source-map-js: BSD-3-Clause. picocolors: ISC. detect-libc: Apache-2.0. tslib: 0BSD.
- **lightningcss (MPL-2.0)**, a CSS transformer used by Vite. MPL-2.0 is a file-level copyleft licence. It is used unmodified as a build tool and is not included in the shipped bundle. **Requires licence review.**
- Some optional WebAssembly fallback packages (`@emnapi/*`) are pre-release versions. They are not installed on Windows, macOS or Linux x64.

## Testing Tools

| Tool | Purpose | License (preliminary) | Status | Notes |
|---|---|---|---|---|
| Pytest | Backend tests | MIT | Planned | Development dependency only. |
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

- Lint, formatting and type-checking tools (Phase 01).
- Python dependency locking tool (Phase 01).
- DNS library (Phase 03).
- PDF generation library (Phase 05).
- Frontend linting and formatting tools (oxlint from the Vite template was removed; DECISIONS.md D-025).
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

# AEGIS — Decision Register

**Status:** Living document  
**Last Updated:** 2026-11-15  
**Related:** [PROJECT_VISION.md](../PROJECT_VISION.md) · [PRODUCT_REQUIREMENTS.md](../PRODUCT_REQUIREMENTS.md) · [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) · [DEVELOPMENT_ROADMAP.md](../development/DEVELOPMENT_ROADMAP.md)

This register records approved product and architecture decisions. Changing one of these decisions requires a new entry that supersedes the old one. Entries are never edited silently.

| ID | Decision | Date | Status |
|---|---|---|---|
| D-001 | Modular monolith | 2026-11-15 | Approved |
| D-002 | Apache 2.0 licence, subject to dependency review | 2026-11-15 | Approved |
| D-003 | No Nmap or Scapy in the MVP; native TCP connection engine | 2026-11-15 | Approved |
| D-004 | Server-side sessions in httpOnly cookies; Argon2id | 2026-11-15 | Approved |
| D-005 | Workspace RBAC: Owner, Admin, Analyst, Viewer | 2026-11-15 | Approved |
| D-006 | Three authorization mechanisms: DNS TXT, HTTP, administrative attestation | 2026-11-15 | Approved |
| D-007 | Python 3.11 with pip, venv and `pyproject.toml` | 2026-11-15 | Approved |
| D-008 | Synchronous SQLAlchemy 2.x with psycopg 3 | 2026-11-15 | Approved |
| D-009 | Valkey as the message broker | 2026-11-15 | Approved |
| D-010 | Enforced separation between assessment workers and the database | 2026-11-15 | Approved |
| D-011 | Signed job payloads, per-job ingestion tokens, separate ingestion listener | 2026-11-15 | Approved |
| D-012 | Administrator and CLI password reset only in v0.1.0 | 2026-11-15 | Approved |
| D-013 | Withdrawn | 2026-11-15 | Withdrawn |
| D-014 | Root `tests/` for end-to-end tests; no `packages/` or top-level `workers/` | 2026-11-15 | Approved |
| D-015 | GitHub Actions for CI | 2026-11-15 | Approved |
| D-016 | Frontend tooling deferred until frontend implementation | 2026-11-15 | Resolved by D-021 to D-026 (data-fetching library still open) |
| D-017 | Domain verification does not authorize active assessment of resolved IPs | 2026-11-15 | Approved |
| D-018 | Instance administrator; CLI bootstrap; open registration off by default | 2026-11-15 | Approved |
| D-019 | Third-party lookups disabled by default | 2026-11-15 | Approved |
| D-020 | Two worker roles: assessment and internal | 2026-11-15 | Approved |
| D-021 | Vite 8 as the frontend build tool | 2026-11-15 | Approved |
| D-022 | React Router 8 for routing | 2026-11-15 | Approved |
| D-023 | npm as the frontend package manager | 2026-11-15 | Approved |
| D-024 | Node.js 22 LTS, version 22.22.0 or later | 2026-11-15 | Approved |
| D-025 | Template linter (oxlint) removed; linter chosen in its roadmap task | 2026-11-15 | Approved |
| D-026 | TypeScript 7, subject to compatibility testing | 2026-11-15 | Approved, conditional |

---

## D-001 — Modular monolith

One backend application with clearly bounded modules, plus background workers. It is easier to develop, test and operate than microservices. Microservices require explicit approval.

**Affects:** SYSTEM_ARCHITECTURE §1.

## D-002 — Apache 2.0 licence

Proposed project licence, subject to a complete dependency licence review before release. Dependencies are tracked in `THIRD_PARTY_NOTICES.md`.

## D-003 — No Nmap or Scapy in the MVP

Nmap's licence (NPSL) treats software designed to execute Nmap and parse its results as potentially derivative work. Scapy is GPL-2.0. Neither is bundled or integrated in the MVP. Running a tool as an external process is not assumed to resolve licensing obligations. AEGIS uses its own TCP connection-based assessment engine. OWASP ZAP may become an optional, isolated integration after v0.1.0.

**Affects:** PRD §2.2, SYSTEM_ARCHITECTURE §15, ROADMAP Phase 04 and 06.

## D-004 / D-005 / D-006 — Authentication, RBAC and authorization mechanisms

Defined in PRD §3.1–3.3 and SYSTEM_ARCHITECTURE §9–10.

## D-007 — Python 3.11

The existing virtual environment uses Python 3.11. Migration to a newer Python or to `uv` is deferred.

## D-008 — Synchronous SQLAlchemy 2.x with psycopg 3

Simpler to test and reason about than the async stack. FastAPI runs synchronous endpoints in a thread pool, which is sufficient for a self-hosted platform. psycopg 3 is LGPL-3.0 and is noted in `THIRD_PARTY_NOTICES.md`.

## D-009 — Valkey

Redis 7.4+ uses RSALv2/SSPLv1, and Redis 8 adds AGPLv3. Valkey is BSD-3-Clause and protocol-compatible.

**Affects:** SYSTEM_ARCHITECTURE §2.4, `THIRD_PARTY_NOTICES.md`.

## D-010 — Worker and database separation

Worker-side packages must not import database sessions, models or database libraries. This is enforced by import-linter contracts in CI, and at runtime by giving assessment workers no database credentials and no access to the `data` network.

**Affects:** SYSTEM_ARCHITECTURE §4.5.

## D-011 — Job integrity and result ingestion

- Jobs are signed with Ed25519. Only the backend holds the private key, so workers cannot forge jobs.
- Each job carries a random ingestion token. The database stores only its hash, and the token is valid only while the job is active.
- Results are submitted to a separate internal listener on the `ingest` network and validated for token, state, schema, scope and idempotency.

Known limitation: assessment workers sharing a queue can read each other's job payloads.

**Affects:** SYSTEM_ARCHITECTURE §6.4–6.5.

## D-012 — Password reset

v0.1.0 supports only instance-administrator and CLI password reset. Self-service and email-based reset wait for SMTP support (Phase 09).

**Affects:** PRD FR-AUTH-005.

## D-013 — Withdrawn

This entry has been withdrawn.

## D-014 — Repository layout

The root `tests/` directory holds Playwright end-to-end tests. The empty `packages/` and top-level `workers/` directories were removed. Workers live in `apps/backend/app/workers/`, and a shared package directory will be introduced only when a genuine shared package exists.

## D-015 — Continuous integration

GitHub Actions runs linting, formatting checks, type checking, import contracts and tests on every pull request. The specific tools are selected in Phase 01.

## D-016 — Frontend tooling

Build tool, router and data-fetching library are decided when frontend implementation begins.

**Update:** build tool, router, package manager, Node.js version and TypeScript version were decided at the start of Phase 01.2 (D-021 to D-026). The data-fetching library remains open.

## D-017 — Domain verification and resolved IP addresses

A verified domain may resolve to infrastructure the user does not own (CDNs, hosting and SaaS providers).

- DNS inspection, certificate transparency and TLS inspection of the hostname on port 443 require only domain scope.
- TCP port assessment, service identification and TLS on other ports require every target IP to be covered by an `ip` or `cidr` scope entry. Such an entry can be created through attestation.

**Affects:** PRD FR-ASSET-004, SYSTEM_ARCHITECTURE §10.2.

## D-018 — Instance administration

- An instance-level administrator flag exists, separate from workspace roles.
- It grants no implicit workspace data access.
- The first administrator is created through the CLI, and no default credentials are shipped.
- Open registration is disabled by default.

**Affects:** PRD FR-AUTH-001, FR-AUTH-006.

## D-019 — Third-party lookups

Certificate transparency, passive DNS and future intelligence feeds are disabled by default. The instance administrator enables them after seeing a privacy notice, and workspaces can opt out. AEGIS sends no telemetry.

**Affects:** PRD §4.6, SYSTEM_ARCHITECTURE §12.5.

## D-020 — Two worker roles

Report generation needs database access, but assessment workers must not have it. The two roles are:

- **Assessment workers:** untrusted, with outbound access and no database.
- **Internal workers:** trusted, with database access and no outbound access.

**Affects:** SYSTEM_ARCHITECTURE §6.1.

## D-021 — Vite 8

Vite 8 is the frontend build tool and development server. The application was initialized from the official `react-ts` template (create-vite 9.3.4), with all demonstration content removed.

**Affects:** SYSTEM_ARCHITECTURE §2.1, `THIRD_PARTY_NOTICES.md`.

## D-022 — React Router 8

React Router 8 is the routing library. It is installed during the routing task of Phase 01.2, not before. It requires Node.js 22.22.0 or later (D-024).

## D-023 — npm

npm, bundled with Node.js, is the frontend package manager. `package-lock.json` is committed for reproducible installs. No additional package manager is required.

## D-024 — Node.js 22.22.0 or later

The frontend requires Node.js 22 LTS, version 22.22.0 or later, declared in the `engines` field of `apps/frontend/package.json`. This is the minimum required by React Router 8.

## D-025 — No linter in the initial scaffold

The Vite template's default linter (oxlint) was removed because it was not an approved dependency. The frontend linting and formatting tools are selected in the roadmap task "Configure frontend linting and formatting".

## D-026 — TypeScript 7

The frontend uses TypeScript 7 (`~7.0.2`), the version shipped with the official template. TypeScript 7 is a new native compiler, and some tooling may lag behind it. Compatibility is tested when linting and testing tools are introduced. If a required tool is incompatible, the fallback is the latest TypeScript 5.x release, recorded as a new decision.

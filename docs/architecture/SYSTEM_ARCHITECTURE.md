# AEGIS
## SYSTEM ARCHITECTURE DOCUMENT

**Project:** AEGIS  
**Document:** System Architecture  
**Version:** 1.1  
**Status:** Approved  
**Last Updated:** 2026-11-16  
**Related:** [PROJECT_VISION.md](../PROJECT_VISION.md) · [PRODUCT_REQUIREMENTS.md](../PRODUCT_REQUIREMENTS.md) · [DEVELOPMENT_ROADMAP.md](../development/DEVELOPMENT_ROADMAP.md) · [DECISIONS.md](DECISIONS.md)  
**Target Release:** v0.1.0

---

# 1. ARCHITECTURAL OVERVIEW

## 1.1 Architecture Philosophy

AEGIS will use a modular monolithic architecture.

The application will initially operate as one primary backend application containing independently organized functional modules.

Background security assessment tasks will execute through isolated worker processes.

The architecture prioritizes:

- Security.
- Modularity.
- Maintainability.
- Scalability.
- Testability.
- Extensibility.
- Operational simplicity.

Microservices will not be introduced unless future requirements justify their additional complexity.

## 1.2 High-Level Architecture

AEGIS consists of five major architectural layers:

1. Presentation Layer.
2. Application Layer.
3. Data Layer.
4. Background Processing Layer.
5. Infrastructure Layer.

### Architecture Flow

```text
                  USERS
                    |
                    v
             REACT FRONTEND
                    |
                HTTPS / API
                    |
                    v
             FASTAPI BACKEND
                    |
          +---------+----------+
          |         |          |
          v         v          v
      SERVICES   DATABASE   JOB QUEUE
          |         |          |
          |         v          v
          |     POSTGRESQL    VALKEY
          |                    |
          |                    v
          |          ASSESSMENT WORKERS
          |                    |
          |                    v
          |             SECURITY ENGINES
          |                    |
          |                    v
          +<--------- CONTROLLED RESULT
                     INGESTION API
```

Assessment workers must not have direct PostgreSQL access.

Results must enter the application through a controlled internal result-ingestion interface.

Internal workers (§6.1) are trusted backend components that handle tasks such as report generation. They never contact assessment targets. They are omitted from this diagram.

---

# 2. TECHNOLOGY STACK

## 2.1 Frontend

**Framework:** React

**Language:** TypeScript

**Styling:** Tailwind CSS

**Build Tool:** Vite 8

**Routing:** React Router 8

**Package Manager:** npm, with Node.js 22.22.2 or later (development and CI baseline 22.23.5, in `apps/frontend/.nvmrc`)

See DECISIONS.md D-021 to D-026 and D-047. The data-fetching library will be decided later.

Responsibilities:

- User interface.
- Authentication interface.
- Workspace management.
- Asset management.
- Assessment configuration.
- Assessment monitoring.
- Vulnerability management.
- Reporting interface.
- Dashboard visualization.

The frontend must not execute security assessment tools directly.

All security-sensitive operations must be initiated through authenticated backend APIs.

## 2.2 Backend

**Framework:** FastAPI

**Language:** Python 3.11

**Packaging:** pip, venv and `pyproject.toml`

Responsibilities:

- API management.
- Authentication.
- Authorization.
- Business logic.
- Asset management.
- Assessment orchestration.
- Scope validation.
- Finding management.
- Reporting.
- Audit logging.

The backend is the central application authority.

## 2.3 Database

**Database:** PostgreSQL

**ORM:** SQLAlchemy 2.x (synchronous API)

**Driver:** psycopg 3 (`psycopg[binary]`)

The synchronous API is used deliberately: it is simpler to test and reason about, and FastAPI runs synchronous endpoints in a thread pool, which is sufficient for a self-hosted platform.

**Migration Tool:** Alembic

Responsibilities:

- User records.
- Session records.
- Workspace records.
- Workspace memberships.
- Assets.
- Authorization records.
- Assessment scopes.
- Assessment metadata.
- Vulnerability findings.
- Evidence metadata.
- Audit logs.
- Reports.

PostgreSQL is the authoritative persistent data store.

## 2.4 Background Processing

**Task Queue:** Celery

**Message Broker:** Valkey

Valkey is a BSD-3-Clause, protocol-compatible fork of Redis. It was chosen over Redis 7.4+ (RSALv2/SSPLv1) and Redis 8 (adds AGPLv3) to keep licensing straightforward.

Responsibilities:

- Asynchronous assessments.
- Long-running operations.
- Scheduled tasks in future releases.
- Background report generation (internal worker).
- Assessment status management.

Rules:

- Celery uses JSON serialization only. Pickle is disabled.
- Valkey must not be treated as the permanent storage location for assessment evidence.
- Assessment results do not return through a Celery result backend. They are submitted to the ingestion interface (§6.5).

---

# 3. FRONTEND ARCHITECTURE

## 3.1 Application Structure

The frontend will use a feature-oriented structure.

Proposed organization:

```text
apps/frontend/
│
├── src/
│   ├── app/
│   │   ├── router/        # routes.tsx, router.ts, paths.ts
│   │   ├── layout/        # AppLayout (application shell)
│   │   ├── navigation/    # primary navigation configuration
│   │   ├── pages/         # application-level pages (not found, errors)
│   │   └── providers/
│   │
│   ├── components/
│   │   ├── ui/            # Button, Input, Card, Badge, EmptyState, typography
│   │   ├── layout/        # PageContainer, SideNav, SkipLink
│   │   ├── icons/         # inline SVG icons and the AEGIS logo
│   │   ├── data/          # StatCard, charts, DataTable, ActivityList, FilterTabs, ViewToggle
│   │   └── shared/
│   │
│   ├── features/
│   │   ├── authentication/
│   │   ├── dashboard/     # pages/OverviewPage (landing route)
│   │   ├── activity/      # pages/ActivityPage (audit log)
│   │   ├── assessments/   # pages/AssessmentsPage
│   │   ├── settings/      # pages/SettingsPage
│   │   ├── workspaces/
│   │   ├── assets/
│   │   ├── reconnaissance/
│   │   ├── network/
│   │   ├── vulnerabilities/
│   │   └── reports/
│   │
│   ├── hooks/
│   ├── lib/               # small utilities (cx, document titles)
│   ├── services/
│   ├── types/
│   └── styles/
│
├── public/
├── tests/
├── package.json
└── tsconfig.json
```

## 3.2 Frontend Responsibilities

The frontend must:

- Display application information.
- Collect user input.
- Validate user input before submission.
- Communicate with backend APIs.
- Display assessment progress.
- Display security findings.
- Generate user-facing reports through backend functionality.

Frontend validation must never replace backend validation.

## 3.3 Authentication Handling

Authentication will use secure HTTP-only session cookies.

The frontend must:

- Support login.
- Support registration.
- Maintain authenticated application state.
- Handle expired sessions.
- Handle unauthorized responses.
- Support logout.

Sensitive authentication credentials must not be stored in localStorage.

CSRF protection must be implemented for state-changing requests.

Implementation (roadmap 2.1, DECISIONS.md D-061 to D-068):

- `src/lib/api.ts` sends every request to the same origin with `credentials: 'same-origin'`, adds the `X-CSRF-Token` header to state-changing requests, checks the shape of every response before use, and raises API errors in the shared error format. The CSRF token is held in memory only; nothing is stored in `localStorage` or `sessionStorage`, and the session cookie is `HttpOnly`.
- `features/authentication` holds the sign-in, registration (shown only when open registration is enabled) and reset-password pages, the `AuthProvider`, which asks `GET /api/v1/auth/me` who is signed in, and the route guards: every application page requires a session; sign-in and registration redirect signed-in users. A 401 from any API call returns the user to the sign-in page, with a notice when the session expired.
- The guards only decide what to show. The backend enforces authentication and authorization on its own.

---

# 4. BACKEND ARCHITECTURE

## 4.1 Application Organization

The backend will follow a modular architecture.

Repository layout:

```text
C:\AEGIS (repository root)
├── apps/
│   ├── backend/         # FastAPI application and both worker roles
│   └── frontend/        # React application
├── docs/
├── infrastructure/      # Dockerfiles, service configuration and operational scripts
├── tests/               # Playwright end-to-end tests
├── docker-compose.yml   # secure, production-like base (project "aegis")
└── docker-compose.dev.yml  # development override
```

There is no top-level `workers/` or `packages/` directory. Workers are part of the backend codebase, and a shared package directory will be introduced only when a genuine shared package exists.

Backend structure:

```text
apps/backend/
│
├── app/
│   ├── main.py            # create_app() application factory
│   │
│   ├── api/
│   │   ├── router.py          # assembles /api/v1 from registered routers
│   │   ├── v1/                # public API
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── admin.py       # instance administration
│   │   │   ├── workspaces.py
│   │   │   ├── assets.py
│   │   │   ├── scopes.py
│   │   │   ├── assessments.py
│   │   │   ├── findings.py
│   │   │   └── reports.py
│   │   └── internal/          # ingestion listener only (§6.5)
│   │
│   ├── core/
│   │   ├── config.py      # Settings: AEGIS_* environment variables
│   │   ├── errors.py      # AppError and the standard error handlers
│   │   ├── request_context.py  # request IDs and request logging
│   │   ├── request_limits.py   # request body size limit
│   │   ├── security.py
│   │   ├── permissions.py
│   │   └── logging.py
│   │
│   ├── database/
│   │   ├── config.py      # connection URL from AEGIS_DATABASE_* settings
│   │   ├── engine.py      # engine and connection pool
│   │   ├── session.py     # Database lifecycle, per-request session
│   │   ├── base.py        # declarative Base, naming convention, mixins
│   │   └── errors.py      # 503 for unavailable database
│   │
│   ├── models/
│   ├── schemas/
│   ├── services/
│   │
│   ├── contracts/             # signed job and result schemas (no database imports)
│   ├── netguard/              # destination validation (no database imports)
│   │
│   ├── modules/
│   │   ├── assets/
│   │   ├── reconnaissance/
│   │   │   ├── engine/        # assessment logic (no database imports)
│   │   │   └── service.py     # API-side orchestration
│   │   ├── network/
│   │   │   ├── engine/
│   │   │   └── service.py
│   │   ├── vulnerabilities/
│   │   ├── web_security/      # later phase
│   │   ├── system_audit/      # later phase
│   │   └── threat_intel/      # later phase
│   │
│   └── workers/
│       ├── assessment/        # untrusted role (no database imports)
│       └── internal/          # trusted role
│
├── migrations/
├── tests/
└── pyproject.toml
```

Directories are created when the phase that needs them begins. Later-phase modules are shown for orientation only.

## 4.2 API Layer

FastAPI endpoints will expose application functionality.

Responsibilities:

- Request validation.
- Authentication.
- Authorization.
- Request processing.
- Response serialization.
- Error handling.

API routes must remain relatively thin.

Business logic belongs in services and domain modules.

## 4.3 Service Layer

The service layer contains application business logic.

Examples:

- Authentication service.
- Workspace service.
- Asset service.
- Scope validation service.
- Assessment orchestration service.
- Finding management service.
- Reporting service.

Services should not depend directly on frontend implementation details.

## 4.4 Domain Modules

Each security module must maintain clear boundaries.

Modules should expose defined interfaces rather than importing arbitrary internal implementation details from other modules.

The vulnerability management module receives standardized findings from assessment modules.

## 4.5 Enforced Import Boundaries

The following packages form the **worker side** of the application:

- `app.workers.assessment`
- `app.modules.*.engine`
- `app.netguard`
- `app.contracts`

Worker-side packages must not import:

- `app.database`, `app.models`, `app.services` or `app.api`.
- `sqlalchemy`, `psycopg` or `alembic`.

Enforcement:

1. **Static:** import-linter "forbidden" contracts, configured in `apps/backend/pyproject.toml` and run in CI (`lint-imports`). A violation fails the build. Direct and indirect imports are both checked (DECISIONS.md D-048).
2. **Runtime:** assessment worker containers receive no database credentials and are not attached to the `data` network (§12.2).

Both worker roles use the same container image with a different command. The image therefore contains the database driver code, which is why the static contract and the absence of credentials and network access are used together.

Engines of one module must not import the internals of another module.

---

# 5. DATABASE ARCHITECTURE

## 5.1 Database Responsibilities

PostgreSQL stores all authoritative application records.

Initial entities include:

```text
users
sessions
instance_settings
workspaces
workspace_members
workspace_invitations
assets
asset_relationships
authorization_records
scope_entries
assessments
assessment_scope_snapshots
assessment_jobs
observations
findings
finding_evidence
finding_history
audit_logs
reports
```

Entity names are indicative. The definitive schema is defined by Alembic migrations.

## 5.2 Entity Relationships

Conceptual relationships:

```text
USER (instance administrator flag)
 |
 +---- WORKSPACE MEMBERSHIPS (role) ---- WORKSPACE
                                           |
                                           +---- INVITATIONS
                                           |
                                           +---- AUTHORIZATION RECORDS (dns | http | attestation)
                                           |       |
                                           |       +---- SCOPE ENTRIES (domain | ip | cidr)
                                           |
                                           +---- ASSETS (domain | ip_address | cidr_range | service)
                                           |       |
                                           |       +---- ASSET RELATIONSHIPS
                                           |
                                           +---- ASSESSMENTS
                                           |       |
                                           |       +---- SCOPE SNAPSHOT (immutable)
                                           |       +---- JOBS
                                           |       +---- OBSERVATIONS
                                           |
                                           +---- FINDINGS (linked to assets and assessments)
                                           |       |
                                           |       +---- EVIDENCE (references observations)
                                           |       +---- HISTORY
                                           |
                                           +---- REPORTS
                                           |
                                           +---- AUDIT LOGS
```

Scope entries belong to the workspace, not to assets. Assets are inventory; scope is permission (PRD FR-ASSET-004).

## 5.3 Database Rules

- Models use SQLAlchemy 2.x typed mappings on `app.database.base.Base`, and are registered in `app/models/__init__.py`.
- Primary keys are random UUIDs (`UUIDPrimaryKeyMixin`); timestamps are `timestamptz` in UTC (`TimestampMixin`).
- Constraint and index names follow the naming convention in `app/database/base.py`.
- SQL is built with the ORM, Core expressions or bound parameters; never by formatting values into SQL strings.
- Connections are configured with `AEGIS_DATABASE_*` settings; connection strings and credentials are never logged (DECISIONS.md D-043).
- Every workspace-owned resource must have a workspace association.
- Workspace isolation must be enforced in backend queries.
- Database migrations must be version-controlled.
- Sensitive information must be protected.
- Foreign key relationships must be explicit.
- Appropriate indexes must be created.
- Deletion behavior must be documented.

Assessment history and audit records must not be silently discarded when application resources are changed.

---

# 6. BACKGROUND WORKER ARCHITECTURE

## 6.1 Overview

AEGIS uses Celery workers for work that must not run inside an API request.

The API must not execute lengthy security assessments synchronously.

There are two worker roles. They use the same image with different commands and queues.

| | Assessment worker | Internal worker |
|---|---|---|
| Trust | Untrusted: processes data influenced by assessment targets | Trusted backend component |
| Queues | `assessment.*` | `internal.*` |
| Database access | None: no credentials, not on the `data` network, import contract (§4.5) | Yes |
| Outbound internet | Yes, through the `egress` network under §12.2 controls | None |
| Typical tasks | DNS, subdomain, TCP, service and TLS engines; HTTP verification requests | Report generation; expiring tokens, scopes and invitations |
| Result path | Internal ingestion listener (§6.5) | Backend services directly |

The internal worker must never execute assessment engines or contact assessment targets.

## 6.2 Job Execution Flow

```text
USER
 |
 v
FRONTEND
 |
 v
FASTAPI
 |
 v
AUTHENTICATION
 |
 v
AUTHORIZATION (workspace RBAC)
 |
 v
SCOPE VALIDATION (including resolved IP addresses)
 |
 v
JOB CREATION (scope snapshot, ingestion token, Ed25519 signature)
 |
 v
VALKEY QUEUE
 |
 v
ASSESSMENT WORKER
 |
 v
SIGNATURE AND EXPIRY CHECK
 |
 v
ASSESSMENT EXECUTION (destination re-validated before every connection)
 |
 v
INTERNAL INGESTION LISTENER
 |
 v
RESULT VALIDATION (token, job state, schema, scope snapshot, idempotency)
 |
 v
POSTGRESQL
```

## 6.3 Assessment Worker Responsibilities

Assessment workers must:

- Verify the job signature and expiry before execution, and reject unsigned or invalid jobs.
- Execute only the engine named in the job. There is no shell execution and no subprocess built from user input.
- Enforce the job's scope snapshot and the destination controls in §12.2 for every connection.
- Enforce execution timeouts, concurrency limits and rate limits.
- Collect assessment evidence.
- Submit results, progress and failures through the ingestion listener.
- Stop execution when a progress submission reports that the job has been cancelled.

## 6.4 Job Integrity: Signed Payloads

The backend signs every job payload with an **Ed25519** private key.

- Only the backend holds the private key. Assessment workers hold only the public key, so a compromised worker cannot forge jobs that other workers would accept. A shared HMAC key could not provide this guarantee.
- The signed payload contains: job ID, assessment ID, workspace ID, engine, targets, scope snapshot, execution limits, ingestion token, issued-at time, expiry time and signing key ID.
- Workers reject payloads with an invalid signature, an unknown key ID, an expired timestamp or an unknown engine.
- The signed document is carried as a JSON task argument.
- Keys are generated at installation, supplied as secrets, never committed to Git, and rotated using the key ID.

Limitation: payloads are signed, not encrypted. Any assessment worker can read the job payloads in its queues, including other jobs' ingestion tokens.

## 6.5 Result Ingestion

The backend exposes ingestion on a **separate listener** (a separate ASGI application on its own port):

- The listener serves only ingestion routes. The public API does not serve them.
- It is attached only to the `ingest` network and is never published to the host.

Per-job ingestion token:

- A 256-bit random token is generated when the job is created.
- The database stores only its hash.
- The token is valid only while the job is in a non-terminal state.

Every submission must pass these checks:

1. The token matches the job.
2. The job is in a state that accepts results.
3. The payload matches the engine's strict, size-limited result schema.
4. Every host, address and name in the results lies within the job's scope snapshot. Out-of-scope data is rejected and audit-logged as a security event.
5. An idempotency key (job ID and sequence number) prevents duplicate processing.

Accepted results are normalized into observations and findings by backend services.

Workers must not be trusted simply because they operate inside Docker.

Limitation: a compromised assessment worker could submit fabricated, in-scope results for another active job whose token it read from the queue. Mitigations:

- Tokens are short-lived and bound to one job.
- The scope snapshot check prevents injecting out-of-scope data.
- All submissions are audit-logged.

Per-worker queue isolation and credentials are possible future work. AEGIS does not provide per-worker task isolation; the limitation, its mitigations and remediation options are tracked as SR-001 in [docs/security/SECURITY_RISKS.md](../security/SECURITY_RISKS.md).

## 6.6 Worker Container Hardening

Assessment worker containers must:

- Run as a non-root user.
- Use a read-only root filesystem, with a tmpfs for temporary files.
- Drop all Linux capabilities. TCP connection-based assessment needs none, including `NET_RAW`.
- Set `no-new-privileges` and never run in privileged mode.
- Apply CPU, memory and process-count limits.
- Apply Celery soft and hard task time limits.

Valkey access:

- Separate ACL users for the backend, assessment workers and internal workers.
- Workers are denied administrative and dangerous commands (for example `CONFIG`, `FLUSHALL`, `FLUSHDB`, `KEYS`, `DEBUG`, `MODULE`).
- Key patterns restrict each role to its own queues. Validated in Phase 01.5 against Celery 5.7 and Valkey 9.1: each role uses its own exchange, queues and unacknowledged-message keys (`internal.*`, `assessment.*`, `_kombu.binding[_permanent].<role>`), and remote control, events and Pub/Sub are disabled. The ACL rules are listed in DECISIONS.md D-055.

---

# 7. SECURITY ASSESSMENT ENGINE ARCHITECTURE

## 7.1 Engine Design

Assessment engines must be modular.

Each engine must have:

- Defined input schema.
- Defined output schema.
- Execution limits.
- Error handling.
- Scope enforcement.
- Evidence collection.
- Test coverage.

## 7.2 Initial Assessment Engines

The MVP includes:

**DNS Engine**

Responsible for DNS record inspection and DNS-related observations.

**Subdomain Discovery Engine**

Responsible for controlled subdomain discovery using approved passive and configured discovery methods.

**TCP Assessment Engine**

Responsible for TCP connection-based port assessment. Targets must be IP addresses covered by `ip` or `cidr` scope entries.

**Service Identification Engine**

Responsible for collecting and classifying available service information.

**TLS Assessment Engine**

Responsible for certificate and TLS configuration inspection.

**Verification Fetcher**

Performs HTTP verification requests (§10.1) under the same destination controls as the engines.

## 7.3 Engine Integration

Assessment engines must not directly modify arbitrary application database records.

They return structured results that pass through the result-ingestion process.

Engines receive a validated job and perform network access only through `app.netguard`. They do not import database code (§4.5).

---

# 8. VULNERABILITY MANAGEMENT ARCHITECTURE

## 8.1 Central Finding Model

All assessment modules must produce findings using a standardized structure.

Conceptual model:

```text
Finding
 |
 +-- ID
 +-- Workspace ID
 +-- Asset ID
 +-- Assessment ID
 +-- Title
 +-- Description
 +-- Category
 +-- Severity
 +-- Confidence
 +-- Evidence
 +-- Source
 +-- First Detected
 +-- Last Detected
 +-- Status
 +-- Remediation
```

## 8.2 Finding Processing

```text
ASSESSMENT MODULES
        |
        v
STRUCTURED RESULTS
        |
        v
RESULT VALIDATION
        |
        v
FINDING NORMALIZATION
        |
        v
EVIDENCE ASSOCIATION
        |
        v
VULNERABILITY MANAGEMENT
        |
        v
DASHBOARD / REPORTS
```

## 8.3 Finding Rules

- Findings must have identifiable sources.
- Evidence must be associated with assessments.
- Severity must be explainable.
- Confidence must be represented.
- Finding history must be preserved.
- Duplicate findings must be handled consistently.

---

# 9. AUTHENTICATION AND AUTHORIZATION ARCHITECTURE

## 9.1 Authentication

Authentication uses secure server-managed sessions.

Session requirements:

- Cryptographically secure identifiers.
- HTTP-only cookies.
- Secure cookie attributes.
- SameSite protection.
- Session expiration.
- Session revocation.
- CSRF protection.

Passwords must use Argon2id.

Implementation (roadmap 2.1):

- **Accounts and administration** (D-061): email address and username, an instance-administrator flag and an active flag. Open registration is off by default. The first administrator is created with the CLI (`python -m app.cli create-admin`), which never takes passwords as arguments.
- **Passwords** (D-062, D-063): Argon2id, RFC 9106 low-memory profile, with a concurrency limit per process; 12 to 128 characters, no composition rules; a dummy verification for unknown accounts keeps failures uniform in time.
- **Device cookie** (D-070): after a sign-in, `__Host-aegis_device` (at most 30 days) lets that browser skip the account-wide sign-in delay. Only a hash of its token is stored; a password change or reset, or deactivation, revokes all of an account's devices; the owner can list and revoke them through `/api/v1/auth/devices`, and in Settings → Security → Trusted devices (the page explains that a device does not sign anyone in). A device never authenticates; sign-out does not revoke it.
- **Sessions** (D-064): 256-bit random tokens stored as SHA-256 hashes in `user_sessions`; cookie `__Host-aegis_session` (`HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/`); 60 minutes idle and 12 hours absolute expiry; revoked at sign-out, on a new sign-in from the same browser and, for all of a user's sessions, on password reset.
- **CSRF** (D-065): deny-by-default middleware for every state-changing API request: `Origin` check, double-submit token in `X-CSRF-Token` and the `__Host-aegis_csrf` cookie, HMAC-signed and bound to the session (or `anonymous` before sign-in), rotated at sign-in and sign-out.
- **Rate limiting** (D-066, D-070): Valkey counters per client address, per account and address with progressive delays, and per account with one admitted attempt per delay. Attempts reserve their slot atomically before the password is checked, so concurrent requests cannot all pass. A browser with a valid device cookie is exempt from the per-account scope only. No permanent lockout; fails closed with 503 when Valkey is unavailable.
- **Security logging** (D-067): structured `auth.*` events without email addresses, passwords, tokens or cookies.

Endpoints: `GET /api/v1/auth/csrf`, `GET /api/v1/auth/options`, `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`, `POST /api/v1/auth/password/reset`; instance administration: `GET`/`PUT /api/v1/admin/settings/registration`, `POST /api/v1/admin/password-resets`.

## 9.2 Authorization

The system uses workspace-based role permissions.

Roles:

- Owner.
- Admin.
- Analyst.
- Viewer.

Every sensitive backend operation must validate:

1. User authentication.
2. Workspace membership.
3. Required role permissions.
4. Resource ownership.
5. Assessment scope where applicable.

Frontend restrictions are not security boundaries.

### Instance Administrator

The instance administrator is an instance-level flag, separate from workspace roles.

- It allows management of user accounts, registration settings and third-party lookup providers (PRD FR-AUTH-006).
- It grants no implicit access to workspace data.
- The first instance administrator is created through the CLI. No default credentials are shipped.

## 9.3 Account Recovery

In v0.1.0, password reset is performed by the instance administrator or through a CLI command on the server (PRD FR-AUTH-005). Every reset revokes the user's sessions. There is no self-service or email-based reset until SMTP support is introduced.

The administrator issues a single-use reset token, valid for 60 minutes and stored as a hash, shown once as a link `/reset-password#token=…` to hand to the user out of band; the token travels in the URL fragment, which browsers never send to a server. The CLI (`python -m app.cli reset-password`) sets a new password directly (DECISIONS.md D-068).

---

# 10. ASSET AUTHORIZATION ARCHITECTURE

## 10.1 Authorization Mechanisms

| Mechanism | Applies to | Proof |
|---|---|---|
| DNS TXT verification | Public domains | `_aegis-verification.<domain>` TXT record `aegis-verification=<token>` |
| HTTP verification | Public domains resolving to public addresses | Token file under `/.well-known/aegis-verification/` |
| Administrative attestation | Private IPs and CIDRs, lab environments, public IPs and CIDRs | Recorded statement by an Owner or Admin, with optional evidence reference and expiry |

HTTP verification rules:

- It is performed by an assessment worker, never by the API process.
- Every destination passes the controls in §12.2.
- Domains resolving to private or reserved addresses are refused; those targets use attestation.
- Redirects to a different host are never followed.
- Response size and time are limited.
- Tokens are compared in constant time.

Verification tokens are random, single-purpose and expire. Authorization records expire and must be renewed.

## 10.2 Scope Model

Scope entries belong to the workspace and reference an authorization record. The full model and coverage rules are defined in PRD FR-ASSET-004.

The key rule: verifying a domain does not authorize active network assessment of the addresses it resolves to. TCP port assessment, service identification and TLS inspection on ports other than 443 require `ip` or `cidr` scope entries.

## 10.3 Scope Enforcement

Scope is enforced at three points:

1. **API, at job creation.** Checks authorization status, expiry, workspace association and target membership. Domain targets of network assessments are resolved, and only covered addresses are included. The scope snapshot is stored.
2. **Assessment worker, before every connection.** The worker resolves the name, checks every resulting address against the snapshot and the denylist (§12.2), then connects to that exact address without resolving again. This is the primary defense against DNS rebinding.
3. **Ingestion listener.** Results containing data outside the snapshot are rejected (§6.5).

Redirects and DNS resolution must not allow assessments to escape approved scope.

Technical verification of asset control must not be treated as conclusive proof of legal authorization.

---

# 11. API ARCHITECTURE

## 11.1 API Design

The backend will expose versioned REST APIs.

Initial API prefix:

`/api/v1/`

## 11.2 Initial API Groups

```text
/api/v1/auth
/api/v1/users
/api/v1/admin
/api/v1/workspaces
/api/v1/assets
/api/v1/scopes
/api/v1/assessments
/api/v1/findings
/api/v1/reports
```

Assessment workers communicate with the backend only through the internal ingestion listener (§6.5). It runs on a separate port that is not reachable from the public API network.

## 11.3 API Requirements

- Consistent response structures.
- Appropriate HTTP status codes.
- Request validation.
- Pagination.
- Filtering.
- Authentication.
- Authorization.
- Error handling.
- API documentation.

---

# 12. INFRASTRUCTURE ARCHITECTURE

## 12.1 Docker Services

Docker Compose project `aegis` (DECISIONS.md D-050 to D-055):

```text
AEGIS
 |
 +-- frontend            (nginx: built application, same-origin /api proxy; 127.0.0.1:8080)
 |
 +-- backend             (public API; internal ingestion listener in a later phase)
 |
 +-- migrate             (one-shot: alembic upgrade head, as the schema owner)
 |
 +-- postgres            (PostgreSQL 18)
 |
 +-- valkey              (Valkey 9, ACL users per role)
 |
 +-- worker-assessment   (untrusted role)
 |
 +-- worker-internal     (trusted role)
```

- One backend image runs the API, the migration job and both worker roles; the frontend image serves the built application with unprivileged nginx (D-051). Images are built locally only and are not distributed (D-059).
- Every container runs as a non-root user with a read-only root filesystem, no Linux capabilities, `no-new-privileges`, CPU, memory and process limits, and no Docker socket (D-052). This applies to PostgreSQL and Valkey as well.
- Only the frontend is published, on `127.0.0.1`. The development override (`docker-compose.dev.yml`) also publishes the API on `127.0.0.1:8000` and runs migrations automatically.
- Startup order uses health conditions: postgres healthy, then migrations (development), then the backend healthy (readiness), then the frontend. Both workers wait for a healthy Valkey; only the internal worker also waits for PostgreSQL.
- PostgreSQL roles (D-054): `aegis_owner` owns the schema and is used only for migrations; `aegis_app`, used by the API and the internal worker, can only read and change rows. The superuser cannot connect over the network.

## 12.2 Network Segmentation and Egress Controls

### Networks

| Network | Compose `internal` | Members | Purpose |
|---|---|---|---|
| `edge` | No | frontend, backend (public API) | User traffic. Also gives the backend outbound DNS for scope validation. |
| `data` | Yes | backend, worker-internal, postgres | Database access |
| `queue` | Yes | backend, worker-assessment, worker-internal, valkey | Job queue |
| `ingest` | Yes | backend (ingestion listener), worker-assessment | Result submission |
| `egress` | No | worker-assessment only | Outbound assessment traffic |

Subnets for all AEGIS networks are set explicitly in Compose so they can be added to the denylist: `<prefix>.0.0/24` (edge) to `<prefix>.4.0/24` (egress), with `AEGIS_SUBNET_PREFIX` defaulting to `10.213`. The frontend has the fixed address `<prefix>.0.10`; the backend trusts forwarding headers only from it.

Implemented in `docker-compose.yml` and verified on the running containers (D-058): the assessment worker cannot resolve or connect to PostgreSQL, receives no database credentials, and its Valkey user cannot access the internal namespace.

### What Docker Compose cannot do

Docker Compose cannot restrict outbound traffic per destination. A container on a non-internal network such as `egress` can reach:

- The internet.
- The host's local network.
- The host itself, including `host.docker.internal` on Docker Desktop.

The architecture therefore does not rely on Compose for egress filtering.

### Controls

1. **Application-level destination validation (`app.netguard`).** It runs for every connection:
   - Resolve the name.
   - Normalize addresses, including IPv4-mapped IPv6.
   - Check each address against the scope snapshot and the denylist.
   - Connect to that exact address.
2. **Container hardening** (§6.6).
3. **Valkey ACLs** limiting each role's commands and keys (§6.6).
4. **Optional host firewall rules** (the `DOCKER-USER` iptables chain) on Linux hosts, documented as additional hardening. They are not available on Docker Desktop for Windows or macOS.

### Denylist

These addresses are never in scope and never contacted:

- `0.0.0.0/8`, `127.0.0.0/8`, `::/128`, `::1/128`.
- `169.254.0.0/16` and `fe80::/10` (link-local, including the `169.254.169.254` cloud metadata endpoint).
- Known cloud metadata addresses outside link-local ranges (for example `fd00:ec2::254`).
- Multicast (`224.0.0.0/4`, `ff00::/8`), reserved (`240.0.0.0/4`) and broadcast addresses.
- The subnets of AEGIS's own Docker networks.

Private and shared ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `100.64.0.0/10`, `fc00::/7`) are refused unless covered by an attestation-backed scope entry.

### Platform notes

On Docker Desktop (Windows and macOS), containers reach private lab networks through the host's network address translation. Lab assessment works when the host can route to the lab. Host-level firewall hardening is not available, so the application-level controls are the enforced boundary.

## 12.3 Configuration

Configuration must use environment variables.

Sensitive credentials must not be committed to Git.

Uvicorn must be started with `--no-server-header` in deployments, so responses do not disclose the server software (DECISIONS.md D-042).

Secrets include the database password, Valkey ACL passwords, the Ed25519 signing key, the session secret and third-party provider API keys. They are supplied through environment variables or Docker secrets. The assessment worker receives only the secrets it needs: its Valkey credentials and the signing public key.

Provide:

- `.env.example`
- Development configuration.
- Production configuration guidance.

Implementation (DECISIONS.md D-053):

- Secrets are files: `infrastructure/scripts/init_dev_secrets.py` generates them in the gitignored `secrets/` directory without ever overwriting an existing file. Compose mounts each one only into the containers that need it, at `/run/secrets`, and the backend reads them when `AEGIS_SECRETS_DIR` is set. The Valkey ACL file stores password hashes only.
- Non-secret settings are set per service in `docker-compose.yml`; Compose options are documented in the root `.env.example`, and the backend's variables for running outside Docker in `apps/backend/.env.example`.
- The API's server secret (`AEGIS_SECRET_KEY`, for CSRF tokens and rate-limit key names) is the secret file `aegis_secret_key`, mounted only into the API container. `AEGIS_ALLOWED_ORIGINS` lists the browser origins allowed to send state-changing requests; it defaults to the published frontend address on `127.0.0.1` and `localhost` and must be set when AEGIS is reached under another address (D-065).
- Production guidance: use `docker-compose.yml` alone, provide operator-managed secret files, run migrations explicitly (`docker compose --profile migrate run --rm migrate`) after a backup, terminate TLS in front of the frontend, and enable PostgreSQL SSL (`verify-full`) and Valkey TLS if those services are reached over an untrusted network.

## 12.4 Health Checks

Services must expose appropriate health checks.

Implementation (DECISIONS.md D-057):

- `GET /api/v1/health/live`: the API process is serving; no dependency is checked.
- `GET /api/v1/health/ready`: PostgreSQL and Valkey are reachable; otherwise 503 in the standard error format, naming the unavailable dependencies only. Each check is time-limited (2 s by default), results are shared by concurrent requests for 1 s, and pooled connections are reused.
- Worker availability: each worker touches a heartbeat file while connected to Valkey; its container health check fails when the file is stale.
- Every container has a Docker health check (the database, broker and frontend checks use the services' own tools; the backend and worker checks are Python modules). The Valkey check authenticates as the PING-only `healthcheck` user; it is the only check that uses a shell, so its password can be piped to `valkey-cli` from the secret file without appearing in a command line, environment variable or output (D-060).
- Routine liveness and readiness probes are logged at DEBUG by the API and not written to the nginx access log; dependency failures and readiness changes are still logged (D-060).

The system must distinguish:

- Application health.
- Database health.
- Valkey (broker) health.
- Worker availability.

## 12.5 External Data Flows

The table below lists every connection that leaves the deployment.

| Connection | Component | Data sent | Default |
|---|---|---|---|
| DNS resolution | Backend (scope validation), assessment worker | Queried names | Always on; resolver configurable |
| Assessment traffic | Assessment worker | Connections to in-scope targets | On user request |
| HTTP verification | Assessment worker | Request for the verification file | On user request |
| Certificate transparency search | Assessment worker | Domain names | Disabled |
| Passive DNS | Assessment worker | Domain names and API key | Disabled |
| Vulnerability intelligence feeds | To be designed in Phase 07 | Download requests | Disabled |

Requirements are defined in PRD §4.6. AEGIS sends no telemetry, analytics or update checks.

---

# 13. LOGGING AND OBSERVABILITY

## 13.1 Application Logging

The application must use structured logging.

Logs should contain:

- Timestamp.
- Severity.
- Service.
- Event type.
- Request or correlation identifier.

Sensitive credentials and session tokens must never appear in logs.

## 13.2 Audit Logging

Record important security events:

- Authentication events.
- Permission changes.
- Workspace changes.
- Asset authorization.
- Scope modifications.
- Assessment execution.
- Finding modifications.
- Report generation.
- Instance administration actions (account creation, password resets, setting changes).
- Rejected ingestion submissions and blocked out-of-scope connections.

Authentication events are written today as structured security log records (`app.security` logger, `auth.*` and `admin.*` events; DECISIONS.md D-067). Persistent, queryable audit-log storage is roadmap task 2.6.

## 13.3 Error Handling

The application must provide consistent error handling.

Internal stack traces must not be exposed to ordinary users.

---

# 14. TESTING ARCHITECTURE

## 14.1 Backend Testing

Use Pytest.

Test categories:

- Unit tests.
- Integration tests.
- API tests.
- Database tests.
- Authorization tests.
- Security tests.
- Worker tests.
- Import-boundary contract checks.
- Scope-escape and SSRF tests (DNS rebinding, redirects, denylisted addresses).

Configuration is in `apps/backend/pyproject.toml` (DECISIONS.md D-045). Tests live in `apps/backend/tests/`. Database tests run against a disposable PostgreSQL cluster created by the test harness, never an existing database (D-044), and are marked `database` automatically.

## 14.2 Frontend Testing

Use Vitest and React Testing Library.

Test:

- Components.
- Forms.
- Authentication state.
- API interactions.
- Navigation.
- Error states.

Vitest reuses the Vite configuration and runs in jsdom, with React Testing Library, user-event and jest-dom. Tests live next to the code as `src/**/*.test.ts(x)` and are type-checked and linted like application code (DECISIONS.md D-047).

## 14.3 End-to-End Testing

Use Playwright.

Test complete user workflows:

- Registration.
- Login.
- Workspace creation.
- Asset registration.
- Assessment execution.
- Finding management.
- Report generation.

## 14.4 Security Testing

Use controlled local environments and deliberately vulnerable test applications.

Never perform automated security tests against systems without authorization.

## 14.5 Continuous Integration

GitHub Actions runs on every pull request and every push to `main` (and on manual dispatch):

- Linting and formatting checks.
- Type checking.
- Import-boundary contracts (§4.5).
- Backend and frontend tests.
- Container image builds, the container smoke test and the browser tests (Playwright, D-073).

The workflow is `.github/workflows/ci.yml` (DECISIONS.md D-048, D-058). It has three independent jobs on `ubuntu-24.04`:

**Backend (Python 3.11)**, in `apps/backend`:

| Step | What runs |
|---|---|
| PostgreSQL | PostgreSQL 18 server binaries installed from the PostgreSQL project's signed apt repository; no cluster or service is created |
| Dependencies | `pip install --require-hashes -r requirements-dev.lock` (every file hash-checked, D-046), `pip install --no-deps -e .`, `pip check` |
| Linting and formatting | `ruff check`, `ruff format --check` (D-045) |
| Type checking | `mypy` in strict mode |
| Infrastructure scripts | `ruff check`, `ruff format --check` and `mypy --strict` on `infrastructure/scripts/` |
| Import boundaries | `lint-imports` (§4.5) |
| Tests | `pytest` with `AEGIS_TEST_REQUIRE_POSTGRES=1`: the database tests run against a disposable cluster created by the test harness on 127.0.0.1 inside the runner (D-044), and a missing PostgreSQL fails the job instead of skipping them |

**Frontend (Node.js)**, in `apps/frontend`, with the Node.js version from `.nvmrc`:

| Step | What runs |
|---|---|
| Dependencies | `npm ci` from `package-lock.json` |
| Type checking | `npm run typecheck` (`tsc -b`, including the test files) |
| Linting | `npm run lint` (Oxlint with type-aware rules, D-033) |
| Formatting | `npm run format:check` (Prettier) |
| Tests | `npm test` (Vitest, D-047) |
| Build | `npm run build` (production build) |

**Containers (build, smoke test and browser tests)**: `python3 infrastructure/scripts/smoke_test.py --build --e2e` builds the backend and frontend images from the hash-checked `requirements.lock` and `package-lock.json`, starts the production-like stack as the separate Compose project `aegis-smoke` with temporary secrets, and checks service health, the frontend proxy and health endpoints, PostgreSQL role restrictions, Valkey authentication and ACLs, worker isolation, task routing, container security settings and graceful shutdown (D-058). With `--e2e` it then runs the 24 Playwright tests in `apps/frontend/e2e/` against the same disposable stack, after `npm ci` and `npx playwright install --with-deps chromium` (Node.js from `.nvmrc`). A failed browser test fails the job. The development project `aegis` and its volumes are never used. Images are never pushed or uploaded (D-059).

Both workflows run with a read-only token (`contents: read`), use no secrets, trigger on `pull_request` (never `pull_request_target`), pin every action to a full commit hash, have job timeouts and cancel superseded runs. A separate workflow (`pr-title.yml`) checks that pull request titles follow Conventional Commits (D-049). Not covered by CI: a vulnerability scan of the container images' operating-system packages, and `pip-audit`/`npm audit` (run locally before releases).

---

# 15. FUTURE EXTENSIBILITY

The architecture must allow additional modules without requiring a complete redesign.

Future modules include:

- Web and API security.
- Threat intelligence.
- Linux system auditing.
- Continuous monitoring.
- Notifications.
- AI security assistance.

Optional third-party integrations must maintain clear process boundaries and undergo licensing and security review.

Scapy and Nmap are excluded from the MVP.

OWASP ZAP may be introduced as an optional isolated integration in a later release.

---

# 16. ARCHITECTURAL DECISION PRINCIPLES

All major architectural decisions must be documented.

Decisions should consider:

- Security implications.
- Maintenance cost.
- Performance.
- Complexity.
- Licensing.
- Operational requirements.
- Future extensibility.

Contributors must not independently replace approved architectural components or introduce microservices without explicit approval.

---

# 17. ARCHITECTURE COMPLETION CRITERIA

The architecture is considered implemented progressively as:

1. Frontend and backend communicate successfully.
2. Authentication and authorization operate correctly.
3. Database persistence works.
4. Background jobs execute reliably.
5. Workers operate within defined security boundaries.
6. Assessment results enter through controlled interfaces.
7. Findings are normalized.
8. Reports are generated from persistent data.
9. Docker deployment is reproducible.
10. Automated integration tests validate the complete system.

---

# 18. REVISION HISTORY

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-11-15 | Initial proposed architecture. |
| 1.1 | 2026-11-15 | Approved. Python 3.11, synchronous SQLAlchemy 2.x with psycopg 3, Valkey; two worker roles; enforced import boundaries (§4.5); Ed25519-signed jobs, per-job ingestion tokens and a separate ingestion listener (§6.4–6.5); container hardening (§6.6); workspace-level scope model and enforcement points (§10); network segmentation rewritten to state Docker Compose limits (§12.2); external data flows (§12.5); CI (§14.5). See [DECISIONS.md](DECISIONS.md). |

**End of Document.**
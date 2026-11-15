# AEGIS
## SYSTEM ARCHITECTURE DOCUMENT

**Project:** AEGIS  
**Document:** System Architecture  
**Version:** 1.0  
**Status:** Proposed  
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
          |     POSTGRESQL    REDIS
          |                    |
          |                    v
          |              CELERY WORKERS
          |                    |
          |                    v
          |             SECURITY ENGINES
          |                    |
          |                    v
          +<--------- CONTROLLED RESULT
                     INGESTION API
```

Workers must not have direct PostgreSQL access.

Results must enter the application through a controlled internal result-ingestion interface.

---

# 2. TECHNOLOGY STACK

## 2.1 Frontend

**Framework:** React

**Language:** TypeScript

**Styling:** Tailwind CSS

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

**Language:** Python

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

**ORM:** SQLAlchemy

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

**Message Broker:** Redis

Responsibilities:

- Asynchronous assessments.
- Long-running operations.
- Scheduled tasks in future releases.
- Background report generation.
- Assessment status management.

Redis must not be treated as the permanent storage location for assessment evidence.

## 2.5 Infrastructure

**Containerization:** Docker

**Development Orchestration:** Docker Compose

Responsibilities:

- Application deployment.
- Service isolation.
- Environment configuration.
- Reproducible development.
- Dependency management.

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
│   │   ├── router/
│   │   └── providers/
│   │
│   ├── components/
│   │   ├── ui/
│   │   ├── layout/
│   │   └── shared/
│   │
│   ├── features/
│   │   ├── authentication/
│   │   ├── dashboard/
│   │   ├── workspaces/
│   │   ├── assets/
│   │   ├── reconnaissance/
│   │   ├── network/
│   │   ├── vulnerabilities/
│   │   └── reports/
│   │
│   ├── hooks/
│   ├── lib/
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

---

# 4. BACKEND ARCHITECTURE

## 4.1 Application Organization

The backend will follow a modular architecture.

Proposed structure:

```text
apps/backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── workspaces.py
│   │   │   ├── assets.py
│   │   │   ├── assessments.py
│   │   │   ├── findings.py
│   │   │   └── reports.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── permissions.py
│   │   └── logging.py
│   │
│   ├── database/
│   │   ├── session.py
│   │   └── base.py
│   │
│   ├── models/
│   │
│   ├── schemas/
│   │
│   ├── services/
│   │
│   ├── modules/
│   │   ├── assets/
│   │   ├── reconnaissance/
│   │   ├── network/
│   │   ├── web_security/
│   │   ├── system_audit/
│   │   ├── threat_intel/
│   │   └── vulnerabilities/
│   │
│   └── workers/
│
├── migrations/
├── tests/
└── pyproject.toml
```

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

---

# 5. DATABASE ARCHITECTURE

## 5.1 Database Responsibilities

PostgreSQL stores all authoritative application records.

Initial entities include:

```text
users
sessions
workspaces
workspace_members
assets
asset_verifications
assessment_scopes
assessments
assessment_jobs
findings
finding_evidence
finding_history
audit_logs
reports
```

## 5.2 Entity Relationships

Conceptual relationships:

```text
USER
 |
 +---- WORKSPACES
          |
          +---- MEMBERS
          |
          +---- ASSETS
          |       |
          |       +---- ASSESSMENT SCOPES
          |
          +---- ASSESSMENTS
          |       |
          |       +---- FINDINGS
          |               |
          |               +---- EVIDENCE
          |               |
          |               +---- HISTORY
          |
          +---- REPORTS
```

## 5.3 Database Rules

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

AEGIS uses Celery workers for long-running assessment tasks.

The API must not execute lengthy security assessments synchronously.

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
AUTHORIZATION
 |
 v
SCOPE VALIDATION
 |
 v
JOB CREATION
 |
 v
REDIS QUEUE
 |
 v
CELERY WORKER
 |
 v
ASSESSMENT EXECUTION
 |
 v
RESULT VALIDATION
 |
 v
INTERNAL RESULT INGESTION API
 |
 v
POSTGRESQL
```

## 6.3 Worker Responsibilities

Workers must:

- Receive authorized assessment jobs.
- Validate job integrity.
- Execute approved assessment operations.
- Enforce execution timeouts.
- Collect assessment evidence.
- Submit results through the internal result-ingestion interface.
- Record execution failures.

## 6.4 Worker Isolation

Workers must operate with restricted privileges.

Requirements:

- No privileged containers by default.
- No direct PostgreSQL connection.
- Restricted Redis access.
- Controlled outbound networking.
- No arbitrary command execution.
- Resource limits.
- Execution timeouts.
- Controlled result submission.

Network egress must be restricted to approved assessment destinations and required infrastructure endpoints.

Worker access to internal services, cloud metadata endpoints and unrelated private networks must be blocked.

The application must validate resolved IP addresses and revalidate destinations immediately before network connections to mitigate DNS rebinding and related SSRF risks.

## 6.5 Result Ingestion

The backend must expose a private, authenticated result-ingestion interface.

It must:

- Authenticate worker submissions.
- Associate results with valid jobs.
- Validate result structure.
- Reject unauthorized or unexpected results.
- Prevent duplicate processing.
- Store evidence metadata.
- Create standardized findings.

Workers must not be trusted simply because they operate inside Docker.

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

Responsible for TCP connection-based port assessment.

**Service Identification Engine**

Responsible for collecting and classifying available service information.

**TLS Assessment Engine**

Responsible for certificate and TLS configuration inspection.

## 7.3 Engine Integration

Assessment engines must not directly modify arbitrary application database records.

They return structured results that pass through the result-ingestion process.

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

---

# 10. ASSET AUTHORIZATION ARCHITECTURE

## 10.1 Authorization Mechanisms

Public domains may use:

- DNS TXT verification.
- HTTP verification.

Private assessment environments may use:

- Administrative authorization attestation.
- Explicit scope registration.
- Recorded authorization evidence.

## 10.2 Scope Enforcement

Every active assessment must reference an approved scope.

The system must validate:

- Target domain.
- Resolved IP address.
- IP range membership.
- Scope expiration.
- Workspace association.
- Authorization status.

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
/api/v1/workspaces
/api/v1/assets
/api/v1/scopes
/api/v1/assessments
/api/v1/findings
/api/v1/reports
```

Internal worker communication must use a separate, authenticated interface.

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

The initial environment will contain:

```text
AEGIS
 |
 +-- frontend
 |
 +-- backend
 |
 +-- postgres
 |
 +-- redis
 |
 +-- worker
```

## 12.2 Network Segmentation

Docker networks must separate application responsibilities.

Proposed logical networks:

**Frontend Network**

Connects frontend and backend.

**Data Network**

Connects backend to PostgreSQL.

**Queue Network**

Connects backend and workers to Redis.

**Worker Egress Network**

Provides controlled outbound assessment connectivity.

Worker containers must not have unrestricted access to internal application services.

## 12.3 Configuration

Configuration must use environment variables.

Sensitive credentials must not be committed to Git.

Provide:

- `.env.example`
- Development configuration.
- Production configuration guidance.

## 12.4 Health Checks

Services must expose appropriate health checks.

The system must distinguish:

- Application health.
- Database health.
- Redis health.
- Worker availability.

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

## 14.2 Frontend Testing

Use Vitest and React Testing Library.

Test:

- Components.
- Forms.
- Authentication state.
- API interactions.
- Navigation.
- Error states.

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

Claude must not independently replace approved architectural components or introduce microservices without explicit approval.

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

**End of Document.**
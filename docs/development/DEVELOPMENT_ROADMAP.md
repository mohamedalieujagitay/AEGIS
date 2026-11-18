# AEGIS
## DEVELOPMENT ROADMAP

**Project:** AEGIS — Open-Source Cybersecurity Intelligence & Assessment Platform  
**Version:** 1.1  
**Status:** Approved  
**Last Updated:** 2026-11-18  
**Related:** [PROJECT_VISION.md](../PROJECT_VISION.md) · [PRODUCT_REQUIREMENTS.md](../PRODUCT_REQUIREMENTS.md) · [SYSTEM_ARCHITECTURE.md](../architecture/SYSTEM_ARCHITECTURE.md) · [DECISIONS.md](../architecture/DECISIONS.md)  
**Initial Release Target:** v0.1.0  
**License:** Apache 2.0 (subject to dependency and licensing review)

---

# MILESTONE STATUS

Progress against this roadmap. The plan below is unchanged; this table records what has been completed and verified.

| Milestone | Status | Evidence |
|---|---|---|
| Phase 1 — Project Foundation | Closed | Commit `2cc6a83`; CI fix `5f06f5a` |
| Phase 2.1 — Authentication | Closed | Commits `e380686`, `33f94ae`, `50e2210`; DECISIONS.md D-061 to D-074 |
| Phase 2.1 maintenance | Closed | Commit `519e700`; CI run 44308675940 |
| Phase 2.2 — User Management | Closed | Commit `d1228fd`; DECISIONS.md D-075; CI run 44308675940 |
| picomatch security remediation (GHSA-fc5q-39xc-vjpf) | Implemented and verified; the upstream advisory remains open (no fixed release) | Commit `361e190`; DECISIONS.md D-076; CI run 44308675940 |
| Phase 2.3 — Workspace Management | Ready to begin; not started | Section 2.3 below |

---

# 1. INTRODUCTION

## 1.1 Purpose

This document defines the development roadmap for AEGIS.

It establishes the implementation sequence, development phases, milestones, deliverables and completion criteria required to transform AEGIS from an initial concept into a functional open-source cybersecurity platform.

The roadmap is designed around incremental development.

Each phase must produce working, tested and documented functionality before the project progresses to the next phase.

## 1.2 Development Philosophy

AEGIS will follow these principles:

1. Build a reliable foundation before introducing complex functionality.
2. Develop independent modules with clearly defined responsibilities.
3. Prioritize security from the beginning.
4. Avoid unnecessary architectural complexity.
5. Maintain automated testing throughout development.
6. Document functionality as it is implemented.
7. Introduce third-party security tools only after licensing and security reviews.
8. Prioritize functional capabilities over visual demonstrations.

Development will follow a feature-based workflow:

**Plan → Implement → Review → Test → Refactor → Document → Commit**

---

# 2. PROJECT DEVELOPMENT OVERVIEW

AEGIS will be developed across ten major phases.

| Phase | Name | Priority |
|---|---|---|
| 01 | Project Foundation | Critical |
| 02 | Core Platform & Authentication | Critical |
| 03 | Asset Management & Reconnaissance | Critical |
| 04 | Network Security Assessment | Critical |
| 05 | Vulnerability Management & Reporting | Critical |
| 06 | Web & API Security | High |
| 07 | Threat Intelligence | High |
| 08 | Linux System Security Auditing | High |
| 09 | Continuous Monitoring & Notifications | High |
| 10 | Advanced Security Intelligence & AI | Future |

The first five phases establish the initial usable product.

Phases 01–05 constitute the planned scope of AEGIS v0.1.0.

---

# 3. DEVELOPMENT PHASES

# PHASE 01 — PROJECT FOUNDATION

**Priority:** Critical  
**Release:** v0.1.0

## Objective

Establish the technical foundation, repository structure, development environment and engineering standards.

This phase must create a working application foundation without implementing the full security assessment functionality.

## Tasks

### 1.1 Repository Initialization

- Initialize Git repository.
- Establish repository structure.
- Configure `.gitignore`.
- Create README.md.
- Create documentation directory.
- Establish licensing files.
- Configure contribution guidelines.

### 1.2 Frontend Foundation

- Initialize React application.
- Configure TypeScript.
- Integrate Tailwind CSS.
- Establish routing.
- Create reusable UI components.
- Implement application layout.
- Establish design tokens.
- Configure frontend linting and formatting.

### 1.3 Backend Foundation

- Initialize FastAPI on Python 3.11 (pip, venv and `pyproject.toml`).
- Establish modular application structure.
- Configure API routing.
- Implement configuration management.
- Implement centralized exception handling.
- Establish logging.
- Implement request validation.
- Configure API documentation.

### 1.4 Database Foundation

- Configure PostgreSQL.
- Integrate SQLAlchemy 2.x (synchronous API) with psycopg 3.
- Configure Alembic.
- Establish database connection management.
- Create initial migration structure.

### 1.5 Infrastructure

- Create Dockerfiles.
- Configure Docker Compose.
- Configure Valkey as the Celery broker (JSON serialization only, ACL users per role).
- Create the Celery application skeleton with the assessment and internal worker roles (no assessment engines yet).
- Define Docker networks as specified in SYSTEM_ARCHITECTURE §12.2.
- Establish development environment variables.
- Implement health-check endpoints.
- Establish service dependencies.

### 1.6 Engineering Standards

- Configure Pytest.
- Configure Vitest.
- Establish code formatting.
- Establish linting.
- Create the GitHub Actions CI workflow: linting, formatting checks, type checking, import-boundary contracts and tests on every pull request.
- Configure import-linter contracts separating worker-side code from database code (SYSTEM_ARCHITECTURE §4.5).
- Establish pull request conventions.

## Deliverables

- Functional frontend application.
- Functional FastAPI backend.
- PostgreSQL integration.
- Valkey integration.
- Docker development environment.
- Initial automated tests.
- Repository documentation.

## Completion Criteria

- All application services start successfully.
- Frontend communicates with backend.
- Backend connects to PostgreSQL.
- Valkey connection works.
- Import-boundary contracts pass in CI.
- Database migrations execute successfully.
- Health checks return expected results.
- Automated tests pass.
- Development instructions are documented.

---

# PHASE 02 — CORE PLATFORM & AUTHENTICATION

**Priority:** Critical  
**Release:** v0.1.0

## Objective

Implement the foundational application functionality required to support users, workspaces and security assessments.

## Tasks

### 2.1 Authentication

- User registration.
- User login.
- Secure session management.
- Logout.
- Session expiration.
- Session revocation.
- Password hashing using Argon2id.
- Administrator-initiated and CLI password reset (no email reset in v0.1.0; PRD FR-AUTH-005).
- Instance administrator bootstrap through the CLI; open registration disabled by default (PRD FR-AUTH-006).
- Login rate limiting.
- CSRF protection.

Authentication will use secure HTTP-only session cookies.

### 2.2 User Management

- User profiles.
- Account settings.
- Password management.
- Session management.

### 2.3 Workspace Management

Implement workspace functionality.

Features:

- Create workspace.
- Rename workspace.
- Delete workspace.
- Invite existing users through in-app invitations (no email in v0.1.0).
- Remove members.
- Manage workspace permissions.

### 2.4 Role-Based Access Control

Implement four workspace roles.

| Role | Permissions |
|---|---|
| Owner | Full workspace control |
| Admin | Manage users, assets and assessments |
| Analyst | Conduct assessments and manage findings |
| Viewer | Read-only access |

Permissions must be enforced by backend authorization middleware and service-level checks.

The detailed permission matrix is defined in PRD FR-WS-003.

Navigation must follow the permission matrix. The Activity page shows the workspace audit log, which only Owners and Admins may view: hide it from Analysts and Viewers, and refuse their requests in the backend (PRD §5.2, DECISIONS.md D-037). The Phase 1.2 frontend shows Activity to everyone because no authentication exists yet.

### 2.5 Application Dashboard

Implement the initial dashboard.

Components:

- Workspace overview.
- Total registered assets.
- Recent activity.
- Assessment history.
- Security findings summary.
- Navigation sidebar.
- User profile menu.

Dashboard statistics must eventually use real database records rather than hardcoded values.

### 2.6 Audit Logging

Record security-relevant application activities.

Examples:

- Login attempts.
- Authentication events.
- Workspace changes.
- Member invitations.
- Permission changes.
- Asset registration.
- Assessment execution.

## Deliverables

- Functional authentication system.
- Workspace management.
- Role-based permissions.
- User management.
- Initial dashboard.
- Audit logging.

## Completion Criteria

- Users can register and authenticate.
- Sessions are securely managed.
- Workspace permissions work correctly.
- Unauthorized operations are rejected.
- Audit events are recorded.
- Authentication and authorization tests pass.

---

# PHASE 03 — ASSET MANAGEMENT & RECONNAISSANCE

**Priority:** Critical  
**Release:** v0.1.0

## Objective

Develop the asset management and reconnaissance foundation.

AEGIS must be capable of discovering and organizing digital assets belonging to authorized assessment targets.

## Tasks

### 3.1 Asset Management

Support the following asset types:

- Domains (a subdomain is a domain with a parent).
- IP addresses (also represent hosts in v0.1.0).
- CIDR ranges.
- Services (discovered by assessments only).

Asset types are defined in PRD FR-ASSET-001.

Features:

- Register assets.
- Edit asset information.
- Remove assets.
- Categorize assets.
- Assign assets to workspaces.
- View asset relationships.
- Track discovery history.

### 3.2 Authorization Verification

Implement controlled asset authorization.

Supported mechanisms:

**DNS Verification**

- Generate verification tokens.
- Generate DNS TXT verification instructions.
- Verify ownership through DNS.
- Store verification status.

**HTTP Verification**

- Generate verification tokens.
- Provide `.well-known` verification instructions.
- Validate verification files.
- Refuse HTTP verification for domains resolving to private or reserved addresses.
- Execute verification requests in the assessment worker under destination controls.

**Administrative Attestation**

For private networks and authorized laboratory environments:

- Explicit scope registration.
- Authorization confirmation.
- Workspace-level administrative approval.
- Evidence records.
- Authorization expiration.

Authorization records must be auditable.

Verification of technical control must not be represented as conclusive proof of legal permission.

### 3.3 Scope Management

Implement an explicit assessment scope system.

Supported scope definitions:

- Domains, with an explicit `include_subdomains` option.
- Individual IP addresses.
- CIDR ranges.

Requirements:

- Explicit scope registration.
- Scope validation.
- Scope expiration.
- Scope status.
- Scope ownership association.
- Assessment-to-scope association through an immutable scope snapshot.
- Scope belongs to the workspace; assets never grant scope.
- Active network assessment requires target IP addresses to be covered by `ip` or `cidr` entries (PRD FR-ASSET-004).

Every assessment must validate its targets against the approved scope.

### 3.4 DNS Intelligence

Implement DNS inspection.

Supported records:

- A.
- AAAA.
- CNAME.
- MX.
- NS.
- TXT.
- SOA.
- CAA.

Additional functionality:

- DNS resolution.
- DNS response inspection.
- DNS record history.
- DNSSEC status inspection.
- DNS configuration reporting.

### 3.5 Subdomain Discovery

Implement controlled subdomain discovery.

Initial capabilities:

- Certificate transparency lookups (optional third-party lookup, disabled by default; PRD §4.6).
- Passive DNS intelligence where available (optional third-party lookup, disabled by default).
- Configurable wordlist-based discovery within authorized scope (requires `include_subdomains`).

Discovered assets must be recorded with their discovery source and timestamp.

Unverified discoveries must not automatically become authorized scanning targets.

### 3.6 Certificate Intelligence

- Certificate inspection.
- Issuer information.
- Expiration dates.
- Subject alternative names.
- Certificate validity.
- Certificate history where available.

### 3.7 Asset Relationship Visualization

Provide a visual representation of discovered infrastructure.

Examples:

- Domain-to-subdomain relationships.
- Domain-to-IP relationships.
- Host-to-service relationships.
- Certificate-to-domain relationships.

## Deliverables

- Asset management system.
- Authorization verification.
- Scope management.
- DNS inspection engine.
- Subdomain discovery.
- Certificate inspection.
- Asset relationship visualization.

## Completion Criteria

- Users can register and manage assets.
- Authorization verification works.
- Assessment scopes are enforced.
- DNS records are correctly collected.
- Discovered assets retain provenance.
- Unauthorized targets cannot enter active assessment jobs.
- Asset-related tests pass.

---

# PHASE 04 — NETWORK SECURITY ASSESSMENT

**Priority:** Critical  
**Release:** v0.1.0

## Objective

Introduce network assessment capabilities for identifying exposed services and understanding basic network security configurations.

## Tasks

### 4.1 Network Assessment Engine

Develop a native Python-based TCP connection assessment engine.

Initial capabilities:

- TCP connection-based port assessment.
- Configurable port selection.
- Connection timeout configuration.
- Controlled concurrency.
- Rate limiting.
- Assessment progress tracking.

The MVP will not bundle Nmap or Scapy.

Raw packet scanning and packet capture are outside the initial release scope.

### 4.2 Port Assessment

Support:

- Common TCP port assessment.
- Custom TCP port ranges.
- Individual port assessment.
- Open, closed and filtered/unknown result classification where evidence permits.

### 4.3 Service Identification

Implement basic service identification.

Capabilities:

- Service port association.
- Controlled service banner collection.
- Service metadata.
- Service identification confidence.
- Evidence storage.

Do not claim definitive software identification when only a port number or ambiguous banner is available.

### 4.4 Network Inventory

Connect discovered network services to registered assets.

Display:

- Host address.
- Open ports.
- Identified services.
- Assessment timestamp.
- Assessment status.
- Previous observations.

### 4.5 TLS Assessment

Implement TLS configuration inspection.

Features:

- Certificate validity.
- Certificate expiration.
- Issuer information.
- Hostname validation.
- Protocol version inspection.
- Certificate chain inspection.
- Basic configuration warnings.

### 4.6 Assessment Execution

Integrate scanning with Celery workers.

Requirements:

- Background assessment jobs.
- Job status tracking.
- Execution timeouts.
- Controlled concurrency.
- Cancellation support.
- Error handling.
- Result persistence.

### 4.7 Worker Isolation

Implement the worker execution boundaries defined in SYSTEM_ARCHITECTURE §4.5 and §6.

Requirements:

- No database access from assessment workers, enforced by import contracts, missing credentials and network membership.
- Ed25519-signed job payloads, verified before execution.
- Per-job ingestion tokens and the separate ingestion listener.
- Restricted Valkey access through ACL users.
- Container hardening: non-root, read-only filesystem, no capabilities, no privileged mode.
- No arbitrary shell execution.
- Destination validation for every connection (resolve, check against scope snapshot and denylist, connect to the validated address).
- Protection against internal network and metadata endpoint access, DNS rebinding and scope changes.

Workers must not trust frontend-supplied target information.

## Deliverables

- Native TCP assessment engine.
- Port assessment.
- Basic service identification.
- Network inventory.
- TLS assessment.
- Background job execution.
- Worker isolation.

## Completion Criteria

- Authorized assets can be assessed.
- Out-of-scope targets are rejected.
- Port results are recorded accurately.
- TLS findings are generated correctly.
- Background jobs execute reliably.
- Worker restrictions are tested.
- Network assessment tests pass.

---

# PHASE 05 — VULNERABILITY MANAGEMENT & REPORTING

**Priority:** Critical  
**Release:** v0.1.0

## Objective

Build the central vulnerability management layer.

This phase connects findings from previous modules and turns technical observations into organized, evidence-backed security issues.

## Tasks

### 5.1 Unified Finding Model

Create a standardized finding structure.

Each finding should contain:

- Finding ID.
- Title.
- Description.
- Affected asset.
- Finding category.
- Severity.
- Evidence.
- Discovery source.
- First detected timestamp.
- Last detected timestamp.
- Current status.
- Remediation recommendation.

### 5.2 Finding Classification

Support severity levels:

- Critical.
- High.
- Medium.
- Low.
- Informational.

Include confidence levels to distinguish confirmed issues from potential observations.

### 5.3 Vulnerability Inventory

Features:

- View all findings.
- Filter by severity.
- Filter by asset.
- Filter by category.
- Search findings.
- Group related findings.
- View evidence.
- Track finding history.

### 5.4 Risk Assessment

Implement an initial risk prioritization model.

Consider:

- Severity.
- Asset importance.
- External exposure.
- Finding confidence.
- Available vulnerability intelligence.

Risk scoring must be transparent and documented.

Avoid presenting a proprietary risk score as an established industry standard.

### 5.5 Finding Lifecycle

Implement finding statuses:

- Open.
- Acknowledged.
- In Progress.
- Resolved.
- Accepted Risk.
- False Positive.

Maintain status history and record who made each change.

### 5.6 Remediation Management

Provide:

- Remediation recommendations.
- Resolution notes.
- Assignment to workspace members.
- Remediation status.
- Finding reassessment.

### 5.7 Assessment History

Features:

- Assessment history.
- Previous result comparison.
- Newly discovered findings.
- Resolved findings.
- Changed asset observations.
- Historical evidence.

### 5.8 Reporting

Implement PDF and JSON reports.

Report generation runs on the internal worker (SYSTEM_ARCHITECTURE §6.1).

Reports should include:

- Assessment information.
- Authorized scope.
- Assessment date.
- Executive summary.
- Asset inventory.
- Findings summary.
- Severity distribution.
- Detailed findings.
- Evidence.
- Remediation recommendations.

Reports must clearly distinguish observed results from inferred risks.

## Deliverables

- Unified finding model.
- Vulnerability inventory.
- Severity classification.
- Risk prioritization.
- Finding lifecycle.
- Remediation management.
- Assessment history.
- PDF reporting.
- JSON reporting.

## Completion Criteria

- Findings from previous modules enter the unified inventory.
- Findings retain their source and evidence.
- Users can manage finding statuses.
- Historical comparisons work.
- PDF and JSON exports contain accurate information.
- Reporting tests pass.

---

# MILESTONE 01 — AEGIS v0.1.0

Following completion of Phases 01–05, AEGIS should be ready for its first public release, subject to release-readiness review.

## v0.1.0 Feature Set

| Capability | Included |
|---|---|
| Authentication | Yes |
| Workspace management | Yes |
| Role-based access | Yes |
| Asset management | Yes |
| Authorization verification | Yes |
| DNS analysis | Yes |
| Subdomain discovery | Yes |
| TCP port assessment | Yes |
| Basic service identification | Yes |
| TLS assessment | Yes |
| Vulnerability inventory | Yes |
| Risk prioritization | Yes |
| Assessment history | Yes |
| PDF reporting | Yes |
| JSON reporting | Yes |
| Docker deployment | Yes |
| Automated testing | Yes |

## Release Requirements

Before publishing v0.1.0:

- All critical functionality must work.
- Automated tests must pass.
- Security-sensitive functionality must undergo review.
- Docker installation must be documented.
- Database migrations must be verified.
- Default configurations must be secure.
- No credentials or secrets may be committed.
- Dependency licensing must be reviewed.
- Third-party lookups must be verified as disabled by default.
- Known limitations must be documented.
- Security disclosure instructions must be published.

---

# PHASE 06 — WEB & API SECURITY

**Priority:** High  
**Release:** Post-v0.1.0

## Objective

Expand AEGIS into web application and API security assessment.

## Tasks

### 6.1 HTTP Security Analysis

- HTTP security headers.
- Cookie security attributes.
- CORS configuration.
- HTTP-to-HTTPS behavior.
- TLS configuration.
- Basic security misconfiguration detection.

### 6.2 Web Application Assessment

- Technology fingerprinting.
- Security configuration inspection.
- Publicly accessible resource inspection.
- Basic web security checks.
- Evidence collection.

### 6.3 API Security

- OpenAPI specification import.
- API endpoint inventory.
- Authentication configuration analysis.
- Authorization design checks.
- Rate-limit configuration analysis.
- Security misconfiguration detection.

### 6.4 OWASP ZAP Integration

Introduce OWASP ZAP as an optional integration.

Requirements:

- Separate container execution.
- Controlled API communication.
- Explicit assessment scope.
- Passive scanning by default.
- Active scanning only with additional authorization.
- Resource limits.
- Job isolation.

### Deliverables

- Web security assessment module.
- API assessment module.
- Optional ZAP integration.
- Unified finding integration.

---

# PHASE 07 — THREAT INTELLIGENCE

**Priority:** High  
**Release:** Post-v0.1.0

## Objective

Integrate external vulnerability and threat intelligence sources.

Feeds are third-party connections and follow PRD §4.6. Internal workers have no outbound access, so the component that retrieves feeds must be designed before this phase begins.

## Tasks

### 7.1 CVE Intelligence

- NVD integration.
- CVE information retrieval.
- CVSS information.
- Affected software identification.
- Vulnerability history.

### 7.2 CISA KEV Integration

- Known Exploited Vulnerabilities ingestion.
- KEV catalog monitoring.
- Matching against known findings.
- Priority notifications.

### 7.3 Threat Indicators

Support:

- IP indicators.
- Domain indicators.
- URL indicators.
- File hashes where relevant.

### 7.4 MITRE ATT&CK

- Technique information.
- Tactic classification.
- Threat relationship mapping.
- Security finding contextualization.

### 7.5 Threat Intelligence Dashboard

Display:

- Recent vulnerabilities.
- Relevant threat intelligence.
- Affected assets.
- High-priority security alerts.

### Deliverables

- CVE intelligence integration.
- CISA KEV integration.
- Threat indicator management.
- MITRE ATT&CK mapping.
- Threat intelligence dashboard.

---

# PHASE 08 — LINUX SYSTEM SECURITY AUDITING

**Priority:** High  
**Release:** Post-v0.1.0

## Objective

Introduce Linux system auditing capabilities.

## Tasks

### 8.1 System Inventory

- Operating system identification.
- Kernel information.
- Installed package inventory.
- Running services.
- System resource information.

### 8.2 Security Configuration Auditing

- SSH configuration.
- Firewall configuration.
- File permissions.
- User and group configuration.
- Exposed services.
- Security-relevant system settings.

### 8.3 Package Vulnerability Assessment

- Installed package identification.
- Version comparison.
- Known vulnerability correlation.
- Package risk reporting.

### 8.4 Hardening Recommendations

Provide actionable recommendations based on observed configuration issues.

### 8.5 Agent Architecture

Introduce an optional Linux assessment agent.

Requirements:

- Minimal privileges.
- Explicit installation.
- Secure communication.
- Authentication.
- Auditable execution.
- Controlled information collection.

### Deliverables

- Linux inventory.
- Configuration auditing.
- Package vulnerability assessment.
- Hardening recommendations.
- Optional Linux agent.

---

# PHASE 09 — CONTINUOUS MONITORING & NOTIFICATIONS

**Priority:** High  
**Release:** Future

## Objective

Transform AEGIS from a manual assessment application into a continuous security monitoring platform.

## Tasks

### 9.1 Scheduled Assessments

- Assessment scheduling.
- Recurring execution.
- Configurable intervals.
- Assessment history.

### 9.2 Change Detection

Detect:

- New subdomains.
- New IP addresses.
- Newly exposed services.
- Changed certificates.
- Expiring certificates.
- New vulnerability findings.
- Resolved findings.

### 9.3 Notifications

Support:

- In-app notifications.
- Email notifications (introduces SMTP configuration, which also enables email-based password reset and invitations).
- Configurable alert rules.

### 9.4 Monitoring Dashboard

Display:

- Security trends.
- Asset changes.
- Newly detected issues.
- Assessment frequency.
- Resolution progress.

### Deliverables

- Scheduled assessments.
- Change detection.
- Notification system.
- Continuous monitoring dashboard.

---

# PHASE 10 — ADVANCED SECURITY INTELLIGENCE & AI

**Priority:** Future

## Objective

Introduce intelligent analysis capabilities that help users understand security findings and make better remediation decisions.

AI will be introduced only after AEGIS has a reliable evidence collection and vulnerability management foundation.

## Tasks

### 10.1 AI Security Assistant

Allow users to ask questions about their security assessments.

Examples:

- What are my most critical findings?
- Explain this vulnerability.
- What changed since my last assessment?
- Which assets need immediate attention?
- How can I remediate this configuration problem?

### 10.2 Finding Explanation

- Technical explanations.
- Contextual risk interpretation.
- Remediation guidance.
- Related finding analysis.

### 10.3 Security Assessment Summaries

Generate:

- Executive summaries.
- Technical summaries.
- Remediation priorities.
- Assessment comparisons.

### 10.4 AI Safety Requirements

- Ground responses in actual assessment evidence.
- Clearly distinguish facts from generated interpretations.
- Never invent scan results.
- Require user approval for consequential actions.
- Do not execute generated commands automatically.
- Protect sensitive assessment data.

### Deliverables

- AI security assistant.
- Intelligent finding explanations.
- Assessment summaries.
- AI-assisted remediation guidance.

---

# 4. CROSS-PHASE ENGINEERING REQUIREMENTS

The following requirements apply throughout development.

## 4.1 Testing

Every feature must include appropriate automated tests.

Testing categories:

- Unit testing.
- Integration testing.
- API testing.
- Database testing.
- Authorization testing.
- Security testing.
- Frontend component testing.
- End-to-end testing.

Testing must be introduced alongside functionality, not postponed until the final release.

## 4.2 Security

Security must remain a continuous engineering requirement.

Mandatory considerations:

- Secure authentication.
- Backend authorization.
- Scope enforcement.
- SSRF protection.
- DNS rebinding protection.
- Worker isolation.
- Secret management.
- Audit logging.
- Rate limiting.
- Input validation.
- Dependency security.
- Secure container configuration.

## 4.3 Documentation

Every major feature must include:

- Purpose.
- Technical description.
- Configuration requirements.
- API documentation.
- Testing instructions.
- Known limitations.

## 4.4 Code Quality

Requirements:

- Modular architecture.
- Clear naming conventions.
- Type annotations.
- Consistent error handling.
- Minimal code duplication.
- Explicit service boundaries.
- Maintainable database models.
- No unnecessary dependencies.

## 4.5 Dependency Management

Every third-party dependency must undergo review.

Consider:

- License compatibility.
- Maintenance status.
- Security history.
- Dependency size.
- Performance.
- Operational requirements.

Maintain third-party attribution and notices where required.

---

# 5. DEVELOPMENT WORKFLOW

Each development task must follow a controlled workflow.

## Step 1: Task Definition

Define:

- Objective.
- Requirements.
- Expected behavior.
- Files likely to be affected.
- Dependencies.
- Acceptance criteria.

## Step 2: Implementation Planning

Inspect the existing codebase and propose an implementation plan before modifying files.

## Step 3: Implementation

Implement only the agreed feature or task.

Avoid unrelated modifications.

## Step 4: Code Review

Review:

- Architecture.
- Security.
- Correctness.
- Maintainability.
- Error handling.
- Performance.

## Step 5: Testing

Execute relevant automated tests.

Fix failures before proceeding.

## Step 6: Refactoring

Improve implementation quality without changing intended behavior.

## Step 7: Documentation

Update relevant documentation.

## Step 8: Git Commit

Commit the completed functionality using descriptive commit messages.

Example:

`feat(recon): implement DNS record discovery`

---

# 6. RELEASE STRATEGY

AEGIS will follow semantic versioning.

Format:

MAJOR.MINOR.PATCH

Examples:

- v0.1.0 — Initial functional release.
- v0.2.0 — Web and API security capabilities.
- v0.3.0 — Threat intelligence.
- v0.4.0 — Linux security auditing.
- v0.5.0 — Continuous monitoring.
- v1.0.0 — Mature, stable platform.

Version assignments may change depending on development progress.

A release must represent working functionality, not merely completed code.

---

# 7. SUCCESS METRICS

AEGIS development success will be measured using functional and engineering indicators.

## Functional Metrics

- Supported asset types.
- Successful assessment execution.
- Accurate finding collection.
- Assessment completion rate.
- Report generation reliability.
- Historical comparison accuracy.

## Engineering Metrics

- Automated test coverage.
- Critical defect count.
- Dependency security status.
- Documentation completeness.
- Build reliability.
- Deployment reproducibility.

## Open-Source Metrics

- GitHub contributors.
- Community issues.
- Pull requests.
- Forks and stars.
- External integrations.
- Community-reported defects.

Stars and forks are indicators of adoption, not substitutes for software quality.

---

# 8. DEFINITION OF PROJECT SUCCESS

AEGIS will be considered successful when it becomes a reliable, maintainable and extensible open-source cybersecurity assessment platform.

The initial release must demonstrate that the platform can:

1. Securely manage users and workspaces.
2. Register and authorize assessment assets.
3. Discover and organize digital infrastructure.
4. Perform controlled network assessments.
5. Identify basic security misconfigurations.
6. Aggregate findings into one vulnerability inventory.
7. Prioritize security issues.
8. Track remediation.
9. Generate meaningful security reports.
10. Run reproducibly through Docker.

Long-term success means expanding these capabilities without compromising the platform's security, maintainability or architectural integrity.

---

# 9. FINAL DEVELOPMENT PRINCIPLE

AEGIS must be developed incrementally.

No phase should be considered complete merely because its files have been generated.

Completion requires:

- Working functionality.
- Passing tests.
- Security review.
- Updated documentation.
- Verified integration.
- Acceptance criteria satisfied.

The development roadmap is a living document. Changes are permitted when supported by technical evidence, architectural improvements or clearly justified product decisions.

---

# 10. REVISION HISTORY

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-11-15 | Initial proposed roadmap. |
| 1.1 | 2026-11-15 | Approved. Valkey, Python 3.11 and synchronous SQLAlchemy in Phase 01; worker roles, Docker networks, CI and import contracts in Phase 01; administrator/CLI password reset, instance administration and in-app invitations in Phase 02; asset types and scope model aligned with the PRD in Phase 03; worker isolation rewritten in Phase 04; report generation on the internal worker in Phase 05. See [DECISIONS.md](../architecture/DECISIONS.md). |

**AEGIS DEVELOPMENT MOTTO**

Discover. Analyze. Protect.

Build deliberately. Test continuously. Improve relentlessly.
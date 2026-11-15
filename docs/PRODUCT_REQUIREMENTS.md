# AEGIS
## PRODUCT REQUIREMENTS DOCUMENT

**Project:** AEGIS  
**Document:** Product Requirements Specification  
**Version:** 1.0  
**Status:** Proposed  
**Target Release:** v0.1.0

---

# 1. PRODUCT OVERVIEW

## 1.1 Product Description

AEGIS is an open-source, self-hosted cybersecurity intelligence and assessment platform.

It provides a unified environment for discovering digital assets, assessing network infrastructure, identifying security weaknesses, managing vulnerabilities and monitoring security posture.

The platform combines multiple cybersecurity capabilities into a modular application.

## 1.2 Product Objectives

AEGIS aims to:

1. Simplify authorized security assessments.
2. Centralize digital asset discovery.
3. Identify security misconfigurations.
4. Organize security findings.
5. Prioritize vulnerabilities.
6. Track remediation activities.
7. Generate meaningful security reports.
8. Provide an extensible open-source security platform.

## 1.3 Target Users

### Cybersecurity Students

Students should be able to:

- Understand discovered assets.
- Explore security findings.
- Learn about common vulnerabilities.
- Review assessment reports.
- Understand remediation recommendations.

### Ethical Hackers

Authorized security researchers should be able to:

- Discover assets.
- Assess network services.
- Inspect security configurations.
- Organize findings.
- Compare assessment results.

### Security Professionals

Security professionals should be able to:

- Manage multiple workspaces.
- Maintain asset inventories.
- Conduct assessments.
- Prioritize vulnerabilities.
- Monitor remediation.
- Generate reports.

---

# 2. PRODUCT SCOPE

## 2.1 MVP Scope

The initial release, v0.1.0, must include:

- Authentication.
- Workspace management.
- Role-based access control.
- Asset management.
- Authorization verification.
- Assessment scope management.
- DNS analysis.
- Subdomain discovery.
- Certificate inspection.
- TCP port assessment.
- Basic service identification.
- TLS assessment.
- Vulnerability inventory.
- Risk prioritization.
- Assessment history.
- PDF reporting.
- JSON reporting.
- Docker deployment.

## 2.2 Excluded From MVP

The following capabilities are planned for later releases:

- Advanced web vulnerability scanning.
- OWASP ZAP integration.
- Threat intelligence aggregation.
- Linux security auditing.
- Continuous monitoring.
- AI security assistant.
- Raw packet capture.
- Nmap and Scapy integration.

---

# 3. FUNCTIONAL REQUIREMENTS

# 3.1 Authentication and User Management

### FR-AUTH-001: User Registration

The system must allow users to create accounts.

Required information:

- Email address.
- Password.
- Username.

Requirements:

- Validate email format.
- Enforce password requirements.
- Prevent duplicate accounts.
- Hash passwords using Argon2id.
- Provide appropriate registration feedback.

### FR-AUTH-002: User Login

The system must authenticate registered users.

Requirements:

- Validate credentials.
- Create secure sessions.
- Use HTTP-only cookies.
- Implement login rate limiting.
- Reject invalid credentials.
- Record authentication events.

### FR-AUTH-003: Session Management

The system must:

- Support session expiration.
- Support logout.
- Allow session revocation.
- Protect against CSRF.
- Use secure cookie configuration.

### FR-AUTH-004: User Profiles

Users must be able to:

- View account information.
- Update profile information.
- Change passwords.
- Manage active sessions.

---

# 3.2 Workspace Management

### FR-WS-001: Workspace Creation

Authenticated users must be able to create workspaces.

Each workspace must have:

- Unique identifier.
- Name.
- Description.
- Owner.
- Creation timestamp.

### FR-WS-002: Workspace Membership

Workspace owners and authorized administrators must be able to:

- Invite members.
- Remove members.
- Change member roles.
- View workspace membership.

### FR-WS-003: Workspace Roles

The system must support:

**Owner**
- Complete workspace control.
- Manage members.
- Manage settings.
- Manage assets.
- Execute assessments.

**Admin**
- Manage workspace members, assets and assessments.
- View workspace information.

**Analyst**
- Manage authorized assets.
- Execute assessments.
- Manage findings.

**Viewer**
- View assets.
- View assessment results.
- View reports.

All permissions must be enforced by the backend.

---

# 3.3 Asset Management

### FR-ASSET-001: Asset Registration

Users must be able to register:

- Domains.
- Subdomains.
- IP addresses.
- CIDR ranges.
- Hosts.

Each asset must contain:

- Asset identifier.
- Workspace identifier.
- Asset type.
- Asset value.
- Verification status.
- Creation timestamp.
- Last updated timestamp.

### FR-ASSET-002: Asset Management

Users must be able to:

- View registered assets.
- Edit asset information.
- Remove assets.
- Search assets.
- Filter assets.
- View asset relationships.

### FR-ASSET-003: Asset Authorization

The platform must support:

- DNS TXT verification.
- HTTP-based verification.
- Administrative authorization attestations.

The system must distinguish technical ownership verification from legal authorization.

### FR-ASSET-004: Assessment Scope

Every assessment must have an explicitly defined scope.

Supported scope types:

- Domains.
- Individual IP addresses.
- CIDR ranges.

Requirements:

- Validate targets against approved scope.
- Reject unauthorized targets.
- Record scope changes.
- Support authorization expiration.
- Maintain audit history.

Discovered assets must not automatically become authorized assessment targets.

---

# 3.4 Reconnaissance Module

### FR-RECON-001: DNS Analysis

The system must retrieve and organize:

- A records.
- AAAA records.
- CNAME records.
- MX records.
- NS records.
- TXT records.
- SOA records.
- CAA records.

The system should also inspect DNSSEC status.

### FR-RECON-002: Subdomain Discovery

The system must support controlled subdomain discovery.

Initial methods:

- Certificate transparency lookups.
- Passive DNS sources where available.
- Configurable discovery wordlists.

Each discovered subdomain must include:

- Domain name.
- Discovery source.
- Discovery timestamp.
- Verification status.

### FR-RECON-003: Certificate Inspection

The system must inspect:

- Certificate issuer.
- Certificate expiration.
- Subject.
- Subject alternative names.
- Certificate validity.
- Certificate chain.

### FR-RECON-004: Asset Relationships

The system must associate discovered assets.

Examples:

- Domain to subdomain.
- Domain to IP address.
- Host to service.
- Certificate to domain.

---

# 3.5 Network Security Module

### FR-NET-001: TCP Port Assessment

The system must perform controlled TCP connection-based port assessments.

Requirements:

- Configurable ports.
- Connection timeouts.
- Controlled concurrency.
- Rate limiting.
- Assessment progress.
- Cancellation support.

The initial implementation must not require raw socket privileges.

### FR-NET-002: Port Classification

The system must classify observed port states where sufficient evidence exists.

Supported results:

- Open.
- Closed.
- Filtered or unknown.

### FR-NET-003: Service Identification

The system must associate ports with potential services.

Information may include:

- Port number.
- Protocol.
- Service name.
- Collected banner.
- Identification confidence.

The system must not claim definitive software identification without sufficient evidence.

### FR-NET-004: Network Inventory

The system must organize discovered services by host.

Users must be able to inspect:

- Host addresses.
- Open ports.
- Identified services.
- Assessment timestamps.
- Historical observations.

### FR-NET-005: TLS Assessment

The system must inspect:

- Certificate validity.
- Certificate expiration.
- Hostname matching.
- TLS protocol versions.
- Certificate chain.
- Basic configuration weaknesses.

---

# 3.6 Assessment Job Management

### FR-JOB-001: Background Execution

Long-running assessments must execute through background workers.

### FR-JOB-002: Job Status

The system must support:

- Pending.
- Queued.
- Running.
- Completed.
- Failed.
- Cancelled.

### FR-JOB-003: Job Tracking

Users must be able to view:

- Assessment identifier.
- Target.
- Assessment type.
- Start time.
- Completion time.
- Current status.
- Execution errors.

### FR-JOB-004: Execution Security

Workers must:

- Validate assessment scope.
- Enforce execution timeouts.
- Apply concurrency limits.
- Restrict network access.
- Prevent arbitrary command execution.
- Record execution activity.

---

# 3.7 Vulnerability Management

### FR-VULN-001: Unified Findings

All security assessment modules must use a standardized finding structure.

A finding must contain:

- Unique identifier.
- Title.
- Description.
- Affected asset.
- Finding category.
- Severity.
- Confidence.
- Evidence.
- Discovery source.
- First detected timestamp.
- Last detected timestamp.
- Current status.
- Remediation recommendation.

### FR-VULN-002: Severity Classification

Support:

- Critical.
- High.
- Medium.
- Low.
- Informational.

### FR-VULN-003: Finding Management

Users must be able to:

- View findings.
- Search findings.
- Filter findings.
- Inspect evidence.
- Change finding status.
- Assign remediation responsibilities.
- Add resolution notes.

### FR-VULN-004: Finding Lifecycle

Supported statuses:

- Open.
- Acknowledged.
- In Progress.
- Resolved.
- Accepted Risk.
- False Positive.

Status changes must be recorded.

### FR-VULN-005: Risk Prioritization

The platform must consider:

- Finding severity.
- Asset importance.
- External exposure.
- Confidence.
- Available vulnerability intelligence.

Risk calculations must be transparent and documented.

---

# 3.8 Assessment History

### FR-HIST-001: Assessment Records

The system must retain historical assessment records.

### FR-HIST-002: Assessment Comparison

Users must be able to compare assessments.

The platform should identify:

- Newly discovered findings.
- Resolved findings.
- Changed observations.
- Persistent findings.

### FR-HIST-003: Historical Evidence

Previous evidence must remain associated with its corresponding assessment.

---

# 3.9 Reporting

### FR-REPORT-001: PDF Reports

Users must be able to generate downloadable PDF reports.

Reports should contain:

- Assessment details.
- Authorized scope.
- Assessment date.
- Executive summary.
- Asset inventory.
- Findings summary.
- Severity distribution.
- Detailed findings.
- Evidence.
- Remediation recommendations.

### FR-REPORT-002: JSON Reports

The system must support structured JSON exports.

### FR-REPORT-003: Report Accuracy

Reports must distinguish between:

- Confirmed observations.
- Potential vulnerabilities.
- Inferred risks.
- Unverified information.

---

# 4. NON-FUNCTIONAL REQUIREMENTS

## 4.1 Security

The platform must implement:

- Secure authentication.
- Backend authorization.
- Scope enforcement.
- CSRF protection.
- SSRF protection.
- DNS rebinding protection.
- Input validation.
- Rate limiting.
- Audit logging.
- Secret management.
- Secure worker isolation.

## 4.2 Performance

The application should:

- Support asynchronous assessment execution.
- Avoid blocking API requests during scans.
- Use database indexing appropriately.
- Paginate large datasets.
- Apply controlled worker concurrency.

## 4.3 Reliability

The platform should:

- Handle worker failures.
- Preserve completed assessment results.
- Record execution errors.
- Support database migrations.
- Recover from service restarts.
- Avoid duplicate result processing.

## 4.4 Maintainability

The application must:

- Follow modular architecture.
- Use consistent naming conventions.
- Include type annotations.
- Separate business logic from API routes.
- Include automated tests.
- Maintain technical documentation.

## 4.5 Portability

AEGIS must support self-hosted Docker deployment.

Initial deployment target:

- Windows with Docker Desktop.
- Linux servers.
- Compatible Docker environments.

---

# 5. USER INTERFACE REQUIREMENTS

## 5.1 Design Direction

The interface should be:

- Professional.
- Minimal.
- Dark-themed.
- Responsive.
- Data-oriented.
- Easy to navigate.

Primary accent color: Blue.

## 5.2 Main Navigation

The application should provide:

- Overview.
- Assets.
- Reconnaissance.
- Network Security.
- Web & API Security.
- System Security.
- Threat Intelligence.
- Vulnerabilities.
- Monitoring.
- Reports.
- Settings.

Modules scheduled for later releases may initially appear only when implemented.

## 5.3 Dashboard

The dashboard should display:

- Total assets.
- Active services.
- Total findings.
- Critical findings.
- Recent assessments.
- Recent activity.
- Vulnerability severity distribution.

All displayed statistics must originate from actual application data.

---

# 6. SYSTEM INTEGRATION REQUIREMENTS

## 6.1 Frontend and Backend

The frontend must communicate with the backend through documented HTTP APIs.

## 6.2 Database

PostgreSQL must store:

- Users.
- Sessions.
- Workspaces.
- Workspace memberships.
- Assets.
- Authorization records.
- Assessment scopes.
- Assessment jobs.
- Findings.
- Evidence.
- Audit logs.
- Reports.

## 6.3 Background Processing

Celery and Redis must support asynchronous assessment execution.

## 6.4 External Integrations

External security integrations must be modular and optional where practical.

Each integration must undergo:

- Dependency review.
- License review.
- Security review.
- Configuration validation.

---

# 7. ACCEPTANCE CRITERIA

A feature is considered complete only when:

1. Its required functionality works.
2. Input validation is implemented.
3. Authorization is enforced.
4. Relevant tests pass.
5. Error handling is implemented.
6. Documentation is updated.
7. Integration with existing modules is verified.
8. No unresolved critical security defects remain.

---

# 8. MVP ACCEPTANCE CRITERIA

AEGIS v0.1.0 must demonstrate the following complete workflow:

1. A user registers and logs in.
2. The user creates a workspace.
3. The user registers an assessment asset.
4. The user verifies authorization.
5. The user defines an assessment scope.
6. The user initiates an assessment.
7. A background worker executes the assessment.
8. The system collects and stores results.
9. Security findings enter the unified inventory.
10. The user reviews and prioritizes findings.
11. The user generates a PDF or JSON report.

The complete workflow must be reproducible through Docker deployment.

---

# 9. REQUIREMENTS GOVERNANCE

This document is the functional reference for AEGIS development.

Changes to requirements must be documented and reviewed.

Claude must not independently introduce major features, change approved architecture or expand the MVP without explicit approval.

All requirements should remain consistent with:

- PROJECT_VISION.md
- DEVELOPMENT_ROADMAP.md
- SYSTEM_ARCHITECTURE.md

**End of Document.**
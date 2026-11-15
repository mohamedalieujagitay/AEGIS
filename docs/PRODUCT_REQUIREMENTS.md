# AEGIS
## PRODUCT REQUIREMENTS DOCUMENT

**Project:** AEGIS  
**Document:** Product Requirements Specification  
**Version:** 1.2  
**Status:** Approved  
**Last Updated:** 2026-11-15  
**Related:** [PROJECT_VISION.md](PROJECT_VISION.md) · [SYSTEM_ARCHITECTURE.md](architecture/SYSTEM_ARCHITECTURE.md) · [DEVELOPMENT_ROADMAP.md](development/DEVELOPMENT_ROADMAP.md) · [DECISIONS.md](architecture/DECISIONS.md)  
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
- Instance administration.
- Administrator-initiated and CLI password reset.
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
- Self-service and email-based password reset.
- Email delivery of any kind (invitations, notifications).

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

Registration mode:

- No default accounts or credentials are shipped.
- The first account is created through a CLI command on the server and becomes the instance administrator (FR-AUTH-006).
- Open self-registration is **disabled by default**. The instance administrator may enable it.
- While self-registration is disabled, accounts are created by the instance administrator.

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

### FR-AUTH-005: Administrative Password Reset

v0.1.0 supports password reset only through:

- The instance administrator, from the application.
- A CLI command executed on the server host.

Requirements:

- Workspace Owners and Admins cannot reset passwords, because a user account can belong to several workspaces.
- An administrator reset produces a single-use, time-limited reset token that is shown once to the administrator and handed to the user out of band. The user then chooses a new password.
- The CLI command prompts for the new password interactively and never accepts it as a command-line argument.
- Reset tokens are stored only as hashes.
- A completed reset revokes all of the user's existing sessions.
- Every reset is audit-logged (actor, target account, method, timestamp). Passwords and tokens are never logged.

Known limitations (v0.1.0):

- There is no self-service "forgot password" flow and no email delivery.
- Users who lose their password must contact the instance administrator.
- If the only instance administrator loses access, recovery requires CLI access to the server.
- Email-based reset is planned once SMTP support exists (Phase 09).

### FR-AUTH-006: Instance Administration

The system must support an instance administrator role, separate from workspace roles.

The instance administrator can:

- Create, disable and re-enable user accounts.
- Reset passwords (FR-AUTH-005).
- Enable or disable open registration.
- Configure third-party lookup providers (§4.6).
- View the instance-level audit log.

Requirements:

- The instance administrator flag grants **no implicit access to workspace data**. Workspace access always requires membership.
- The first instance administrator is created through the CLI.
- At least one active instance administrator must always exist.
- All instance administration actions are audit-logged.

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

- Invite existing registered users by email address or username.
- Remove members.
- Change member roles.
- View workspace membership.

Invitations in v0.1.0 are delivered in-app only:

- The invited user sees the pending invitation after logging in and must accept it.
- No email is sent.
- Invitations expire and can be revoked.
- Invitation responses must be uniform, so that they cannot be used to enumerate registered accounts.

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

Permission matrix:

| Action | Owner | Admin | Analyst | Viewer |
|---|---|---|---|---|
| View workspace, assets, assessments, findings and reports | ✅ | ✅ | ✅ | ✅ |
| Edit workspace settings | ✅ | ✅ | ❌ | ❌ |
| Delete workspace or transfer ownership | ✅ | ❌ | ❌ | ❌ |
| Invite and remove members, change roles | ✅ | ✅¹ | ❌ | ❌ |
| Register, edit and remove assets | ✅ | ✅ | ✅ | ❌ |
| Start DNS or HTTP verification | ✅ | ✅ | ✅ | ❌ |
| Create administrative attestations | ✅ | ✅ | ❌ | ❌ |
| Create, modify and revoke scope entries | ✅ | ✅ | ❌ | ❌ |
| Start and cancel assessments | ✅ | ✅ | ✅ | ❌ |
| Manage findings (status, assignment, notes) | ✅ | ✅ | ✅ | ❌ |
| Generate reports | ✅ | ✅ | ✅ | ❌ |
| View the workspace audit log | ✅ | ✅ | ❌ | ❌ |

¹ Admins cannot remove, demote or change the role of the Owner, cannot promote anyone to Owner and cannot change their own role.

Every workspace has exactly one Owner.

---

# 3.3 Asset Management

### FR-ASSET-001: Asset Registration

Users must be able to register:

- Domains (including subdomains).
- IP addresses (IPv4 and IPv6).
- CIDR ranges.

Asset types:

| Type | Registered by users | Discovered by assessments | Definition |
|---|---|---|---|
| `domain` | Yes | Yes | Any fully qualified domain name. A subdomain is a `domain` asset with a parent link, not a separate type. |
| `ip_address` | Yes | Yes | A single IPv4 or IPv6 address. In v0.1.0 an IP address also represents a host. |
| `cidr_range` | Yes | No | A network range. |
| `service` | No | Yes | An IP address, port and protocol tuple observed by an assessment. |

Notes:

- A separate Host entity (one machine with several addresses) is deferred beyond v0.1.0.
- Certificates are stored as observations linked to domains and services. They are not assets.

Each asset must contain:

- Asset identifier.
- Workspace identifier.
- Asset type.
- Asset value.
- Parent asset, where applicable (subdomains, services).
- Source (user-registered, or the assessment that discovered it).
- Scope coverage (derived from active scope entries; informational only and never itself a grant of permission).
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

The platform must support three authorization mechanisms:

| Mechanism | Applies to | Who can perform it |
|---|---|---|
| DNS TXT verification | Public domains | Owner, Admin, Analyst |
| HTTP verification | Public domains that resolve to public IP addresses | Owner, Admin, Analyst |
| Administrative attestation | Private IP addresses and CIDR ranges, lab environments, and public IP addresses or ranges that cannot be proven through DNS | Owner, Admin |

DNS TXT verification:

- The user publishes `_aegis-verification.<domain>` with the value `aegis-verification=<token>`.

HTTP verification:

- The user publishes the token under `/.well-known/aegis-verification/` on the domain.
- HTTP verification is refused when the domain resolves to a private or reserved address. Private targets use administrative attestation.
- Redirects to a different host are not followed.

Administrative attestation records:

- The attesting user.
- The attested targets.
- An authorization statement.
- An optional evidence reference (for example, an engagement letter identifier).
- Timestamp and expiry date.

Common requirements:

- Verification tokens are random, single-purpose and expire.
- Authorization records expire. Expired records deactivate the scope entries that depend on them until renewed.
- Authorization records are audit-logged.

The system must distinguish technical ownership verification from legal authorization.

### FR-ASSET-004: Assessment Scope

Scope belongs to the **workspace**, not to individual assets.

**Assets are inventory; scope is permission.** Registering or discovering an asset never grants scope.

Each scope entry contains:

- Identifier and workspace.
- Type: `domain`, `ip` or `cidr`.
- Value.
- `include_subdomains` (domain entries only; default false).
- The authorization record it depends on.
- Status: pending, active, expired or revoked.
- Expiry date.
- Creator and timestamps.

Coverage rules:

| Assessment activity | Required active scope |
|---|---|
| DNS record inspection, certificate transparency and passive DNS lookups | A domain entry covering the name (exact match, or a parent entry with `include_subdomains`) |
| Wordlist-based subdomain discovery | A domain entry with `include_subdomains` enabled |
| TLS and certificate inspection of a hostname on port 443 | A domain entry covering the hostname |
| TCP port assessment, service identification and TLS inspection on other ports | An `ip` or `cidr` entry covering every target IP address |

Rules:

- Verifying a domain does **not** authorize active network assessment of the IP addresses it resolves to. Those addresses may belong to a hosting provider, CDN or SaaS platform.
- When a network assessment targets a domain, AEGIS resolves it and assesses only the addresses covered by an `ip` or `cidr` entry. Other addresses are skipped and recorded as out of scope.
- Each assessment stores an **immutable scope snapshot** taken at creation. Later scope changes cannot widen a running assessment. Revocation or expiry stops pending work at the next check.
- Targets are validated when the job is created and re-validated immediately before every network connection.
- Private and reserved address ranges can be in scope only through attestation-backed `ip` or `cidr` entries.
- Loopback, link-local, cloud metadata and AEGIS's own internal network addresses can never be in scope.
- Scope changes are recorded in the audit history.
- Discovered assets never automatically become scope. A discovered subdomain is assessable only if an existing entry, explicitly created by an Owner or Admin with `include_subdomains`, already covers it.

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

Certificate transparency and passive DNS lookups are third-party lookups. They are disabled by default (§4.6).

Wordlist-based discovery sends DNS queries for candidate names and requires a domain scope entry with `include_subdomains`.

Each discovered subdomain must include:

- Domain name.
- Discovery source.
- Discovery timestamp.
- Scope coverage (derived).

### FR-RECON-003: Certificate Inspection

The system must inspect:

- Certificate issuer.
- Certificate expiration.
- Subject.
- Subject alternative names.
- Certificate validity.
- Certificate chain.

Certificates are stored as observations linked to the domains and services where they were seen.

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

Targets must be IP addresses covered by an active `ip` or `cidr` scope entry (FR-ASSET-004).

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

Network-level hardening options differ by platform. See SYSTEM_ARCHITECTURE §12.2.

## 4.6 Privacy and Third-Party Lookups

AEGIS is self-hosted. Data stays within the deployment except through the outbound connections below.

| Connection | Data sent | Recipient | Default |
|---|---|---|---|
| DNS resolution | Queried names | The configured DNS resolver | Always on (essential); the operator chooses the resolver |
| Assessment traffic | Connections to in-scope targets | The targets | Only when a user starts an assessment |
| HTTP verification | A request for the verification file | The domain being verified | Only when a user starts verification |
| Certificate transparency search | Domain names | A CT search service | **Disabled** |
| Passive DNS | Domain names and the provider API key | A passive DNS provider | **Disabled**; requires an API key |
| Vulnerability intelligence feeds (post-v0.1.0) | Download requests only | NVD, CISA, MITRE | **Disabled** until Phase 07 |

Requirements:

- Third-party lookups are disabled by default.
- Only the instance administrator can enable a provider. Enabling one shows a privacy notice describing what is sent.
- Workspace Owners and Admins can opt their workspace out of any enabled provider.
- Assessment metadata and reports record which third-party sources were consulted.
- Provider API keys are stored as secrets and never appear in logs or reports.
- AEGIS sends no telemetry, analytics or update checks.

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

Navigation is organised around the user's workflow (register assets, run assessments, triage findings, report) rather than around individual security modules.

The application must provide:

- Overview.
- Assets.
- Assessments.
- Findings.
- Reports.
- Activity.
- Settings.

Security modules do not have their own navigation items while they are part of this workflow. Each module's requirements remain in force and are presented as follows:

| Module or requirement | Where it appears | First available |
|---|---|---|
| Reconnaissance (FR-RECON-001 to 004) | Assessments: DNS analysis and subdomain discovery are assessment types. Assets: discovered subdomains, DNS records, certificates and asset relationships | v0.1.0 |
| Network Security (FR-NET-001 to 005) | Assessments: TCP port assessment and TLS assessment are assessment types. Assets: network inventory (services by host) | v0.1.0 |
| Assessment scope and authorization (FR-ASSET-003, FR-ASSET-004) | Assets | v0.1.0 |
| Assessment jobs and history (FR-JOB-003, FR-HIST-001 to 003) | Assessments | v0.1.0 |
| Vulnerability Management (FR-VULN-001 to 005) | Findings | v0.1.0 |
| Reporting (FR-REPORT-001 to 003) | Reports | v0.1.0 |
| Workspace audit log (§4.1, FR-WS-003) | Activity | v0.1.0 |
| Web & API Security | Assessments: new assessment types | Phase 06 |
| Threat Intelligence | Its own navigation item, plus enrichment of Findings | Phase 07 |
| System Security (Linux auditing) | Assessments: new assessment type. Assets: host details | Phase 08 |
| Monitoring | Its own navigation item | Phase 09 |

Modules scheduled for later releases appear only when implemented.

Navigation items follow the permission matrix (FR-WS-003). In particular, Activity shows the workspace audit log, which only Owners and Admins may view: it must be hidden from, and refused to, Analysts and Viewers. This is enforced by the backend and implemented with workspace roles in Phase 02.

## 5.3 Dashboard

The dashboard (Overview) must display:

- Total assets.
- Assessments.
- Open findings.
- Critical risks (open findings with critical severity).
- Risk distribution: total findings by severity.
- Findings trend over a selectable period.
- Recent assessments.
- Recent activity.

Active services are shown in the network inventory on the Assets page (FR-NET-004) rather than as a dashboard metric.

All displayed statistics must originate from actual application data. Until data exists, each metric shows an empty state, never sample values.

---

# 6. SYSTEM INTEGRATION REQUIREMENTS

## 6.1 Frontend and Backend

The frontend must communicate with the backend through documented HTTP APIs.

## 6.2 Database

PostgreSQL must store:

- Users (including the instance administrator flag).
- Sessions.
- Instance settings (including third-party lookup configuration).
- Workspaces.
- Workspace memberships.
- Workspace invitations.
- Assets.
- Authorization records.
- Scope entries.
- Assessment scope snapshots.
- Assessment jobs (including hashed ingestion tokens).
- Observations.
- Findings.
- Evidence.
- Audit logs.
- Reports.

## 6.3 Background Processing

Celery, with Valkey as the message broker, must support asynchronous assessment execution and internal background tasks such as report generation. SYSTEM_ARCHITECTURE §6 defines the two worker roles.

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

1. The instance administrator is bootstrapped through the CLI, a user account is created (by registration if enabled, otherwise by the instance administrator) and the user logs in.
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

Contributors must not independently introduce major features, change approved architecture or expand the MVP without explicit approval.

All requirements should remain consistent with:

- [PROJECT_VISION.md](PROJECT_VISION.md)
- [DEVELOPMENT_ROADMAP.md](development/DEVELOPMENT_ROADMAP.md)
- [SYSTEM_ARCHITECTURE.md](architecture/SYSTEM_ARCHITECTURE.md)
- [DECISIONS.md](architecture/DECISIONS.md)

---

# 10. REVISION HISTORY

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-11-15 | Initial proposed requirements. |
| 1.1 | 2026-11-15 | Approved. Added administrative password reset (FR-AUTH-005), instance administration (FR-AUTH-006), in-app invitations and the permission matrix; defined asset types; rewrote scope as a workspace-level permission model with an IP-scope requirement for active network assessment; added §4.6 Privacy and Third-Party Lookups; replaced Redis with Valkey. See [DECISIONS.md](architecture/DECISIONS.md). |
| 1.2 | 2026-11-15 | §5.2 navigation reorganised around the user workflow (Overview, Assets, Assessments, Findings, Reports, Activity, Settings) with a mapping of every security module; no functional requirement removed. §5.3 dashboard metrics aligned with the approved UI design; active services moved to the Assets network inventory. Activity restricted to Owners and Admins per FR-WS-003. See DECISIONS.md D-037 and D-038. |

**End of Document.**
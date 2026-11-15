# AEGIS — Project Vision

> **Discover. Analyze. Protect.**

| | |
|---|---|
| **Document** | Project Vision |
| **Status** | Approved |
| **Version** | 1.1 |
| **Last updated** | 2026-11-15 |
| **Related** | [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) · [SYSTEM_ARCHITECTURE.md](architecture/SYSTEM_ARCHITECTURE.md) · [DEVELOPMENT_ROADMAP.md](development/DEVELOPMENT_ROADMAP.md) · [DECISIONS.md](architecture/DECISIONS.md) |

This document defines what AEGIS is, why it exists, who it serves and where it is going. It deliberately avoids implementation detail; that belongs in the requirements and architecture documents.

---

## 1. Product identity

**AEGIS** is an open-source, self-hosted cybersecurity assessment platform. It brings asset discovery, security assessment, vulnerability management and reporting into a single, unified environment.

AEGIS is:

- **Self-hosted.** It runs on infrastructure the user controls. Assessment data stays within the deployment unless the user exports it, apart from documented, optional third-party lookups that the instance administrator explicitly enables (see [External Data Flows](architecture/SYSTEM_ARCHITECTURE.md#125-external-data-flows)).
- **Open source.** Licensed under Apache 2.0, subject to a complete dependency licence review.
- **Authorization-first.** It only assesses targets the user has verified control of or has explicitly recorded authorization for.
- **Evidence-driven.** Every finding is traceable to the observation that produced it.

AEGIS is **not** an exploitation framework, an attack tool or a replacement for a professional penetration test.

---

## 2. Problem statement

Security assessment today is fragmented.

A typical assessment of a small organisation's external footprint involves separate tools for DNS enumeration, subdomain discovery, port scanning, TLS analysis, HTTP header checks and vulnerability tracking. Each tool has its own interface, output format and mental model. The practitioner then manually correlates the results in spreadsheets or documents.

This creates real problems:

| Problem | Consequence |
|---|---|
| Disconnected tools | Findings live in different places and formats; correlation is manual and error-prone. |
| No single asset inventory | Teams don't know what they own, so they can't know what is exposed. |
| No history | It is hard to answer "what changed since last month?" |
| Weak scope control | Ad-hoc tooling makes it easy to scan targets that were never authorised. |
| Steep learning curve | Students and newcomers struggle to see how individual findings fit into a coherent picture of risk. |
| Costly commercial alternatives | Integrated platforms exist, but are often expensive, closed and cloud-hosted. |

---

## 3. Vision and mission

### Vision

> A world where any individual or organisation can understand and improve its security posture using transparent, trustworthy and freely available tools.

### Mission

> Build an open, self-hosted platform that discovers digital assets, assesses them safely and only with authorization, and turns individual observations into prioritised, evidence-backed and actionable security intelligence.

---

## 4. Target audiences

AEGIS serves three primary audiences. One product serves all three: an accessible interface on top of professional-grade capabilities.

### 4.1 Cybersecurity students

| | |
|---|---|
| **Who** | University students, bootcamp learners and self-taught practitioners, working mostly in home labs and on deliberately vulnerable environments. |
| **Needs** | Practical, hands-on assessment experience; an understanding of *why* a finding matters, not just *that* it exists. |
| **AEGIS provides** | Clear explanations of findings, safe defaults, first-class support for private lab environments and a coherent view of how reconnaissance, assessment and risk connect. |

### 4.2 Ethical hackers

| | |
|---|---|
| **Who** | Bug bounty hunters, independent consultants and penetration testers working within defined scopes. |
| **Needs** | Fast reconnaissance, reliable asset inventories, strict scope control and exportable evidence. |
| **AEGIS provides** | Recon and assessment in one workflow, enforced scope boundaries, assessment history and structured reports. |

### 4.3 Security professionals

| | |
|---|---|
| **Who** | Security engineers, system administrators and small security teams responsible for an organisation's infrastructure. |
| **Needs** | A continuously up-to-date asset inventory, a unified vulnerability register, prioritisation and change tracking. |
| **AEGIS provides** | Workspaces with role-based access, a unified vulnerability inventory, historical comparison, audit logging and (later) continuous monitoring. |

---

## 5. Core capabilities

AEGIS is organised around six capability areas. Vulnerability Management is the central layer that the other five feed into.

```text
   Reconnaissance ──┐
   Network Security ┤
   Web & API Security ──►  Vulnerability Management  ──►  Dashboards, History & Reports
   System Security ─┤
   Threat Intelligence ┘
```

| Capability | Purpose | First available |
|---|---|---|
| **Reconnaissance** | Discover and map digital assets: domains, subdomains, DNS records, IP addresses, certificates and HTTP services. | v0.1.0 |
| **Network Security** | Understand exposed services: TCP port assessment, service identification and TLS assessment. | v0.1.0 |
| **Vulnerability Management** | Unify findings from all modules into one inventory with severity, evidence, prioritisation, remediation guidance, history and reporting. | v0.1.0 |
| **Web & API Security** | Identify common web weaknesses through passive, non-destructive checks: security headers, cookies, CORS and API inventory. | After v0.1.0 |
| **Threat Intelligence** | Add context from public sources such as NVD, CISA KEV and MITRE ATT&CK. | After v0.1.0 |
| **System Security** | Audit Linux host configuration with explicit, user-provided access. | After v0.1.0 |

The exact scope and order of delivery are defined in [DEVELOPMENT_ROADMAP.md](development/DEVELOPMENT_ROADMAP.md).

---

## 6. Product principles

These principles guide every product and engineering decision. When two options conflict, the principle higher in this list wins.

1. **Authorization before action.**
   AEGIS never assesses a target that is outside a verified or explicitly recorded scope. Scope is enforced by the backend, re-checked at execution time, and every assessment is audit-logged.

2. **Safe by default.**
   Assessments are non-destructive. There is no exploitation, no denial-of-service testing and no arbitrary command execution. Anything more intrusive must be explicitly enabled, clearly labelled and scoped.

3. **Secure by design.**
   AEGIS is a security product and must hold itself to a higher standard than the systems it assesses. That covers authentication, authorization, input validation, secret handling, worker isolation and protection against misuse of the platform itself.

4. **Evidence over assertion.**
   Every finding links to the raw observation that produced it. AEGIS does not report what it cannot show.

5. **Clarity over volume.**
   Fewer accurate, prioritised and explained findings are worth more than a long list of noise. The interface is data-rich but never cluttered.

6. **Self-hosted and private.**
   The user's data stays on the user's infrastructure. Any outbound call to a third-party service is documented and, where it's not essential, optional and disabled by default. AEGIS sends no telemetry. See [PRODUCT_REQUIREMENTS.md §4.6](PRODUCT_REQUIREMENTS.md#46-privacy-and-third-party-lookups).

7. **Open and inspectable.**
   Code, architecture and decisions are documented so that any engineer can understand, audit and extend the system. Dependencies are chosen with licence compatibility in mind.

8. **Working software over breadth.**
   A small number of capabilities that work reliably and are tested and documented beats many half-finished modules.

---

## 7. Scope boundaries

### 7.1 In scope

- Discovery and inventory of assets the user is authorised to assess.
- Passive and non-destructive active assessment of those assets.
- Correlation, prioritisation and tracking of findings over time.
- Reporting and export of results.
- Support for both public infrastructure and private lab environments.
- Multi-user workspaces with role-based access.

### 7.2 Out of scope (non-goals)

AEGIS will **not**:

- Perform exploitation, payload delivery or post-exploitation activity.
- Perform denial-of-service, stress or destructive testing.
- Execute arbitrary user-supplied commands or scripts.
- Assess targets outside a verified or explicitly authorised scope.
- Provide evasion, anonymisation or stealth features.
- Operate as a hosted, multi-tenant SaaS service run by the project.
- Replace a professional penetration test or a formal compliance audit.

### 7.3 A note on authorization

AEGIS's verification mechanisms (DNS TXT records, HTTP verification files and administrative attestation) establish *technical control* or *recorded authorization evidence*. They cannot prove legal permission in every jurisdiction or situation. Users remain responsible for ensuring they are legally permitted to assess their targets. The product will state this clearly.

---

## 8. Long-term direction

AEGIS evolves in three stages.

### Stage 1 — Assessment foundation (v0.1.0)

A reliable, secure platform that discovers assets, assesses networks and TLS, records findings with evidence and produces reports. It is deployable with Docker and covered by automated tests.

### Stage 2 — Broader coverage

- Web and API security assessment.
- Threat intelligence enrichment (NVD, CISA KEV, MITRE ATT&CK).
- Linux system security auditing.
- Optional third-party tool integrations, each adopted only after a licence review.
- Continuous monitoring, change detection and notifications.

### Stage 3 — Security intelligence

Once AEGIS reliably collects trustworthy evidence:

- An AI assistant that explains findings, correlates related issues and helps plan remediation, grounded in collected evidence rather than speculation.
- Advanced analytics: risk trends, attack-surface change over time and prioritisation models.
- An extension model that lets the community add assessment modules safely.

AI is intentionally deferred. It becomes valuable only once the evidence it reasons over is reliable.

---

## 9. Definition of success

Success is measured by working, tested and documented functionality, not by lines of code or the number of features listed.

### 9.1 Success for v0.1.0

v0.1.0 is successful when a new user can:

1. Deploy AEGIS with Docker by following the README, in under 15 minutes.
2. Bootstrap the instance administrator account through the CLI, then create user accounts and a workspace.
3. Register a domain and verify control of it, or register a private lab scope with an attestation.
4. Run reconnaissance and produce an inventory of subdomains, DNS records, IP addresses and certificates.
5. Run a TCP port, service and TLS assessment against in-scope assets (active network assessment requires the target IP addresses to be in scope, not just the domain name).
6. Review the resulting findings in a unified, prioritised vulnerability inventory with evidence.
7. Compare results against a previous assessment.
8. Export a PDF or JSON report.

On the engineering side, it must also:

- Never assess an out-of-scope target, as confirmed by automated tests.
- Pass all automated tests (unit, integration, security and end-to-end) in CI.
- Have no known high or critical vulnerabilities in AEGIS itself at release.
- Have a documented architecture, contribution guide and security disclosure policy.

### 9.2 Long-term indicators

| Indicator | Signal |
|---|---|
| Adoption | Self-hosted deployments, GitHub stars and forks |
| Community | External contributors and merged community pull requests |
| Trust | Responsible disclosures handled well; no critical security incidents caused by AEGIS |
| Education | Use in courses, labs and training material |
| Quality | Test coverage, issue resolution time, release cadence |

---

## 10. Guiding statement

> Someone with a computer engineering background should be able to inspect AEGIS and say: **"This is a serious software engineering project."**
>
> Every decision, from architecture to a single pull request, should be made with that standard in mind.

---

## 11. Revision history

| Version | Date | Changes |
|---|---|---|
| 0.1 | 2026-11-15 | Initial draft. |
| 1.1 | 2026-11-15 | Approved. Fixed document links; clarified that optional third-party lookups are the only exception to data staying in the deployment; aligned success criteria with instance administration and IP-scope rules. See [DECISIONS.md](architecture/DECISIONS.md). |

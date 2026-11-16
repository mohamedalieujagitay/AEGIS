# AEGIS — Security Risk Register

**Status:** Living document  
**Last Updated:** 2026-11-16  
**Related:** [SYSTEM_ARCHITECTURE.md](../architecture/SYSTEM_ARCHITECTURE.md) · [DECISIONS.md](../architecture/DECISIONS.md)

This register records known security limitations of AEGIS: risks that are understood and accepted for now, with their mitigations and the remediation options to consider later. It does not list vulnerabilities to be fixed immediately; those are fixed, or reported privately (CONTRIBUTING.md §9).

Each entry states what is exposed, to whom, how it is mitigated today, what risk remains and what would reduce it. A risk is closed only by a change that is implemented and verified, recorded in DECISIONS.md.

| ID | Risk | Status |
|---|---|---|
| SR-001 | Assessment workers can read each other's task payloads | Accepted for v0.1.0 (D-011) |
| SR-002 | Docker Compose networks do not filter outbound traffic | Accepted; mitigated by application-level destination validation (§12.2) |
| SR-003 | Container images are not ready for distribution | Accepted; image distribution prohibited (D-059) |
| SR-004 | Development secrets are plain files on the developer's machine | Accepted for development only (D-053) |

---

## SR-001 — Assessment workers can read each other's task payloads

**Status:** Accepted for v0.1.0. Recorded in DECISIONS.md D-011 and SYSTEM_ARCHITECTURE §6.4–6.5. AEGIS does **not** provide per-worker task isolation.

**What is exposed.** All assessment worker containers consume the same queues (`assessment.*`) as the same Valkey ACL user, `worker-assessment` (D-055). Valkey ACLs separate *roles* (the internal worker cannot read assessment queues and vice versa, verified by the smoke test), but they cannot separate *workers of the same role*. Job payloads are signed, not encrypted (§6.4). Any assessment worker can therefore read every job payload in its queues, including jobs it does not execute:

- targets, scope snapshot and execution limits of other jobs;
- the per-job ingestion token of other active jobs.

**Who could exploit it.** An attacker who has already compromised one assessment worker container, for example through a flaw in an assessment engine that processes data returned by an assessment target. Assessment workers process untrusted data by design (§6.1).

**Possible impact.**

- Disclosure of other jobs' targets and scope to the compromised worker.
- Submission of fabricated results for another *active* job, using that job's ingestion token, as long as the results stay within that job's scope snapshot (§6.5).

**Current mitigations.**

- Jobs are signed with Ed25519 and only the backend holds the private key: a compromised worker cannot create or alter jobs that other workers would accept (§6.4).
- Ingestion tokens are random, bound to one job, valid only while that job is active, and stored only as hashes (§6.5).
- Every submission is checked for token, job state, schema, scope snapshot and idempotency; out-of-scope data is rejected and audit-logged as a security event (§6.5).
- All submissions are audit-logged.
- Assessment workers have no database credentials, no access to the `data` network, no capabilities, a read-only filesystem and resource limits (D-010, D-052); their Valkey user cannot touch internal queues, Pub/Sub or administrative commands (D-055).

**Residual risk.** A compromised assessment worker can read other jobs' payloads and inject plausible, in-scope results into other active jobs. It cannot escape the scope of those jobs, reach the database, forge jobs or affect internal work.

**Future remediation (security consideration, not scheduled).** Options to evaluate when worker isolation is revisited (at the latest before AEGIS supports mutually untrusted users of one deployment):

1. **Per-worker credentials and queues:** a Valkey ACL user and queue per worker instance, with the backend routing each job to one worker. Requires worker registration and routing in the backend; Celery's shared-queue model would need to change.
2. **Out-of-band ingestion tokens:** keep the token out of the queued payload; the worker obtains it from the ingestion listener with its own worker identity when it starts the job, so reading the queue no longer reveals it.
3. **Payload encryption to the executing worker:** protects payloads at rest in Valkey, but only if each job is encrypted for one specific worker, which also requires per-worker routing (option 1).
4. **One container per job:** short-lived assessment containers that execute a single job, limiting what a compromise can observe.
5. **Detection:** alert on submissions whose timing or source does not match the worker that claimed the job.

Any of these changes the Celery architecture and needs its own decision. No change is made in Phase 01.

---

## SR-002 — Docker Compose networks do not filter outbound traffic

**Status:** Accepted; documented in SYSTEM_ARCHITECTURE §12.2 and DECISIONS.md D-050.

Containers on the non-internal `edge` and `egress` networks can reach the internet, the host's local network and the host itself. Compose cannot restrict destinations. The enforced boundary is application-level destination validation (`app.netguard`, Phase 03) for every connection, plus container hardening and Valkey ACLs; host firewall rules (`DOCKER-USER`) are optional additional hardening on Linux and unavailable on Docker Desktop.

---

## SR-003 — Container images are not ready for distribution

**Status:** Accepted; image distribution is prohibited (DECISIONS.md D-059).

The backend image contains `psycopg-binary` with bundled LGPL libraries and other components whose licences require notices, an attribution and source availability, plus the GPL-licensed packages of the Debian base image (THIRD_PARTY_NOTICES.md, "psycopg Licence Review"). None of this is provided in the images. Images may be built and run locally only, until a separate distribution-compliance review is complete.

---

## SR-004 — Development secrets are plain files on the developer's machine

**Status:** Accepted for development only (DECISIONS.md D-053).

`infrastructure/scripts/init_dev_secrets.py` writes random passwords to `secrets/` (gitignored, directory mode 0700 on Linux and macOS). They are readable by anyone with access to the developer's account. Production deployments must use operator-managed secret files with appropriate host protection.

---

## Resolved

| Former risk | Resolution |
|---|---|
| The runtime database role could read and change Alembic's migration metadata | Every migration run revokes all privileges on `alembic_version` from roles other than its owner; verified by tests (D-060) |
| The Valkey health-check account had no password | It now has its own generated password; unauthenticated and wrong-password access is refused (D-060) |

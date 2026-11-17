# AEGIS — Security Risk Register

**Status:** Living document  
**Last Updated:** 2026-11-17  
**Related:** [SYSTEM_ARCHITECTURE.md](../architecture/SYSTEM_ARCHITECTURE.md) · [DECISIONS.md](../architecture/DECISIONS.md)

This register records known security limitations of AEGIS: risks that are understood and accepted for now, with their mitigations and the remediation options to consider later. It does not list vulnerabilities to be fixed immediately; those are fixed, or reported privately (CONTRIBUTING.md §9).

Each entry states what is exposed, to whom, how it is mitigated today, what risk remains and what would reduce it. A risk is closed only by a change that is implemented and verified, recorded in DECISIONS.md.

| ID | Risk | Status |
|---|---|---|
| SR-001 | Assessment workers can read each other's task payloads | Accepted for v0.1.0 (D-011) |
| SR-002 | Docker Compose networks do not filter outbound traffic | Accepted; mitigated by application-level destination validation (§12.2) |
| SR-003 | Container images are not ready for distribution | Accepted; image distribution prohibited (D-059) |
| SR-004 | Development secrets are plain files on the developer's machine | Accepted for development only (D-053) |
| SR-005 | Sign-in rate limits are shared by users behind one address | Accepted for v0.1.0 (D-066) |
| SR-006 | Passwords are not checked against common or breached password lists | Accepted for v0.1.0 (D-063) |
| SR-007 | Open registration reveals whether an email address or username is taken | Accepted; registration off by default (D-061, D-063) |
| SR-008 | Outside production, a missing secret key is replaced by a temporary one | Accepted for development only (D-065) |
| SR-009 | A browser without a device token waits during a distributed attack; a stolen device token bypasses the account-wide delay | Accepted (owner-approved D-070, with conditions) |
| SR-010 | The account-wide failure counter resets every window, allowing a short burst | Accepted for v0.1.0 (D-070) |

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

## SR-005 — Sign-in rate limits are shared by users behind one address

**Status:** Accepted for v0.1.0 (DECISIONS.md D-066).

Rate limits are keyed by the client address that the API sees (from the frontend proxy, D-052). Users behind one NAT gateway, corporate proxy or VPN share the per-address limit of 30 failed sign-ins per 15 minutes, so many failures from one of them can delay the others' sign-ins from that address until the window ends. Their accounts are not locked, and they can still sign in from another address. Conversely, an attacker controlling many addresses is limited only by the per-account delay (one attempt per 10 seconds after 20 failures). If AEGIS is deployed behind another reverse proxy, the API sees that proxy's address unless forwarding is configured, which makes every user share one address.

**Future remediation:** configurable trusted-proxy handling for deployments behind a TLS proxy; per-account second factors (roadmap Phase 09 or later); alerting on distributed guessing.

---

## SR-006 — Passwords are not checked against common or breached password lists

**Status:** Accepted for v0.1.0 (DECISIONS.md D-063).

The password policy requires 12 to 128 characters and rejects passwords containing the username or email address, but does not reject common passwords such as `password1234`. NIST SP 800-63B recommends such a check. Online guessing is limited by rate limiting (D-066), and offline guessing by Argon2id (D-062).

**Future remediation:** a bundled list of common passwords checked at registration and reset; an optional, disabled-by-default k-anonymity breached-password lookup (it would be a third-party lookup under D-019).

---

## SR-007 — Open registration reveals whether an email address or username is taken

**Status:** Accepted; open registration is off by default (DECISIONS.md D-061, D-063).

When open registration is enabled, registering with an existing email address or username is refused with 409. The message does not say which one is taken, but the refusal itself confirms that one of them exists. Sign-in and password reset do not reveal accounts. Registration attempts are limited to 5 per address per hour (D-066).

**Future remediation:** email-verified registration, where every registration receives the same response and the outcome is sent by email (requires SMTP support, Phase 09).

---

## SR-008 — Outside production, a missing secret key is replaced by a temporary one

**Status:** Accepted for development only (DECISIONS.md D-065).

When `AEGIS_SECRET_KEY` is not configured and the environment is not `production`, the API generates a random key at start-up and logs `auth.ephemeral_secret_key`. CSRF tokens then stop working after a restart, and API processes that do not share the key cannot verify each other's tokens or share rate-limit counters. Production refuses to start without the key. Docker Compose always provides it as a secret file, so this affects only an API run by hand without configuration.

---

## SR-009 — A browser without a device token waits during a distributed attack; a stolen device token bypasses the account-wide delay

**Status:** Accepted for v0.1.0. The project owner approved the trusted-device exemption on 2026-11-17 with ten conditions (DECISIONS.md D-070).

The account-wide sign-in delay (one attempt per 10 seconds after 20 failures, from any address) protects against distributed guessing, and it also slows the account's owner. D-070 exempts a browser that holds a valid device token from that delay. Two residual risks follow:

- **A browser without the token waits.** A new browser, a cleared cookie jar or a second device has no token. While a distributed attack is in progress, its sign-in competes with the attacker for the one attempt the delay admits, and is refused for most of that time. The owner can still sign in from a browser that has signed in before, or after the attack stops.
- **A stolen device token is a bypass.** The token exempts its holder from the account-wide delay, not from the per-address and per-account-and-address limits, and it does not grant a session. It lasts `AEGIS_DEVICE_TRUST_DAYS` (30 by default) and ends at any password change. Sign-out does not end it, because sign-out ends only the session; the owner can revoke the device individually (`DELETE /api/v1/auth/devices/{id}`), and sign-out everywhere is roadmap 2.2. Anyone who steals the cookie can therefore sign in with the password's protection reduced for the trust period, but not without the password itself, and a stolen session is at least as serious.

**Current mitigations.** The cookie is HttpOnly, Secure and SameSite=Strict, and is not readable by scripts. The server stores only the hash of the token, so a database read does not reveal a usable token. A device is valid only for its own account, lasts at most 30 days, and is revoked by a password change or reset, by deactivation, or by its owner. The per-address and per-account-and-address limits still apply. The owner can list and revoke devices (`DELETE /api/v1/auth/devices/{id}`).

**Future remediation:** a device list in the user interface (the API exists); revocation of devices on sign-out everywhere (roadmap 2.2); shorter trust for administrators; alerting when a device is used from a new address.

---

## SR-010 — The account-wide failure counter resets every window, allowing a short burst

**Status:** Accepted for v0.1.0 (DECISIONS.md D-070).

The account-wide failure counter is a fixed 15-minute window. When it expires, up to 20 attempts are admitted quickly before the 10-second delay resumes. The simulation of a sustained distributed attack for one hour admitted 411 attempts against an expected 361, all within these bursts. The long-run rate remains one attempt per delay plus at most 20 per window, so a guessing attack gains a bounded number of extra attempts, not a rate increase.

**Future remediation:** a sliding window for the account counter, or an exponential decay of the failure count.

---

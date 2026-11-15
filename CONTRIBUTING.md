# Contributing to AEGIS

Thank you for your interest in contributing to AEGIS, an open-source, self-hosted cybersecurity assessment platform.

AEGIS is at an early stage of development (Phase 01, Project Foundation). Many tools are not configured yet. This guide marks each expectation as one of two kinds:

- **Current:** applies today.
- **Planned:** will apply once the roadmap task named next to it is complete. Until then, it is not enforced and you should not assume it exists.

Before contributing, please read:

- [Project Vision](docs/PROJECT_VISION.md): what AEGIS is and is not.
- [Product Requirements](docs/PRODUCT_REQUIREMENTS.md): what the software must do.
- [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md): how it is built.
- [Development Roadmap](docs/development/DEVELOPMENT_ROADMAP.md): what is being built, and when.
- [Decision Register](docs/architecture/DECISIONS.md): approved decisions that contributions must respect.

---

## 1. Ground rules

- **Authorization first.** AEGIS must never assess targets outside an approved scope. Contributions that weaken scope enforcement, authentication, authorization or worker isolation will not be accepted.
- **Non-destructive only.** No exploitation, denial-of-service, evasion features or arbitrary command execution (see Project Vision §7.2).
- **Never test against systems you are not authorized to assess.** Use local, controlled environments.
- **One change per pull request.** Work feature by feature, following the roadmap. Do not expand scope without discussion.
- **Respect approved decisions.** Changes to the technology stack or architecture need an issue and maintainer approval first.

---

## 2. Development environment

### Current

Prerequisites:

- Git.
- Python 3.11.
- Node.js 22.22.0 or later, with npm (bundled with Node.js). The minimum is declared in `apps/frontend/package.json`.

Set up the repository:

```bash
git clone https://github.com/mohamedalieujagitay/AEGIS.git
cd AEGIS
```

Create and activate a virtual environment in the repository root:

```powershell
# Windows (PowerShell)
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
python3.11 -m venv .venv
source .venv/bin/activate
```

The `.venv/` directory is gitignored.

Frontend (React, TypeScript and Vite 8, managed with npm):

```bash
cd apps/frontend
npm install        # install dependencies from package-lock.json
npm run dev        # start the development server
npm run build      # type-check and create a production build in dist/
```

Use npm only. Do not commit lock files from other package managers. Commit `package-lock.json` whenever dependencies change.

Line endings are normalized by `.gitattributes`. Text files are stored with LF, and Windows batch files keep CRLF. You do not need to change your editor settings, but do not commit line-ending-only changes.

### Planned

| Item | Roadmap task |
|---|---|
| Backend dependencies declared in `apps/backend/pyproject.toml` and installed with pip | Phase 01.3 |
| Tailwind CSS, routing (React Router 8), TypeScript configuration and frontend structure | Remaining Phase 01.2 tasks |
| Database configuration and migrations | Phase 01.4 |
| Docker Compose development environment and `.env.example` | Phase 01.5 |

There is no dependency manifest yet. Do not submit code that relies on packages that are not declared in the repository.

---

## 3. Repository structure

### Current

```text
AEGIS/
├── apps/
│   ├── backend/          # FastAPI application (foundation begins in Phase 01.3)
│   └── frontend/         # React + TypeScript application built with Vite 8
├── docs/
│   ├── PROJECT_VISION.md
│   ├── PRODUCT_REQUIREMENTS.md
│   ├── architecture/     # SYSTEM_ARCHITECTURE.md, DECISIONS.md
│   ├── development/      # DEVELOPMENT_ROADMAP.md
│   └── security/
├── infrastructure/
│   ├── docker/
│   └── scripts/
├── tests/                # End-to-end tests (Playwright)
├── CONTRIBUTING.md
├── LICENSE
├── README.md
└── THIRD_PARTY_NOTICES.md
```

The planned internal structure of the backend and frontend is described in [SYSTEM_ARCHITECTURE.md §3–4](docs/architecture/SYSTEM_ARCHITECTURE.md).

Architectural boundaries that contributions must respect:

- API routes stay thin. Business logic belongs in services and modules.
- Worker-side code (`app.workers.assessment`, `app.modules.*.engine`, `app.netguard`, `app.contracts`) must not import database code (SYSTEM_ARCHITECTURE §4.5). Automated enforcement is planned for Phase 01.6.
- There is no top-level `workers/` or `packages/` directory. Do not create one without an approved decision.

---

## 4. Branch naming

### Current

`main` is the default branch. Do not push directly to `main`. All changes go through pull requests.

Name branches using the same types as commit messages (section 5):

```text
<type>/<short-kebab-case-description>
<type>/<issue-number>-<short-kebab-case-description>
```

Examples:

```text
feat/dns-record-discovery
fix/42-session-expiry-check
docs/update-architecture-networking
chore/configure-ci
```

Keep branches short-lived and focused on one change.

---

## 5. Commit messages: Conventional Commits

### Current

AEGIS uses [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

```text
<type>(<optional scope>): <short summary>

<optional body: explain what and why, not how>

<optional footer(s)>
```

Types:

| Type | Use for |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `test` | Adding or correcting tests |
| `build` | Build system or dependencies |
| `ci` | Continuous integration configuration |
| `chore` | Maintenance that does not affect source or tests |
| `revert` | Reverting a previous commit |

Suggested scopes: `backend`, `frontend`, `auth`, `workspaces`, `assets`, `scope`, `recon`, `network`, `vulns`, `reports`, `workers`, `infra`, `deps`, `docs`.

Rules:

- Write the summary in the imperative mood ("add", not "added"), in lowercase, with no trailing period.
- Keep the summary line to 72 characters or fewer.
- Mark breaking changes with `!` after the type or scope and a `BREAKING CHANGE:` footer.
- Reference issues in the footer, for example `Refs #12` or `Closes #12`.

Examples:

```text
feat(recon): implement DNS record discovery
fix(auth): revoke sessions after administrative password reset
docs(architecture): describe Docker Compose egress limitations
```

Commit message format is not automatically enforced at present. Reviewers check it during review.

---

## 6. Pull requests

### Current requirements

Every pull request must:

1. Address **one** feature, fix or documentation change.
2. Reference the related issue, where one exists.
3. Describe:
   - What changed and why.
   - The files and modules affected.
   - Any architectural decisions made.
   - Security implications, or an explicit statement that there are none.
   - The tests you ran and their results.
   - Known limitations.
4. Include tests for new behaviour, once the relevant test framework exists (section 7).
5. Update documentation affected by the change.
6. Include an Alembic migration for every database schema change, once migrations exist (Phase 01.4).
7. Update [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) when adding, removing or upgrading a dependency, and explain why the dependency is needed. New dependencies need maintainer approval.
8. Contain no secrets, credentials, private keys, `.env` files or local tool configuration.
9. Not claim that functionality works without having run it.

Pull requests that change authentication, authorization, scope enforcement, SSRF protection, worker isolation or result ingestion receive additional security review.

### Planned

| Item | Roadmap task |
|---|---|
| Pull request and issue templates | Phase 01.6 |
| GitHub Actions CI running linting, formatting checks, type checking, import-boundary contracts and tests on every pull request | Phase 01.6 |
| Required passing CI checks before merge | After Phase 01.6 |

Until CI exists, run the relevant checks locally and state in the pull request description exactly what you ran.

---

## 7. Testing

### Current

No automated tests exist yet. They are introduced alongside the code they test.

Rules that apply to all tests:

- Run tests only against local, controlled environments and deliberately vulnerable test applications. **Never run tests against external systems you are not authorized to assess.**
- **Generate test certificates and keys dynamically at test run time.** Never commit private keys or certificates, including inside test fixture directories. The `.gitignore` blocks common key formats everywhere in the repository.
- Do not use mock data as a substitute for production functionality. Mock data is acceptable inside isolated tests.
- Do not report tests as passing unless you ran them.

### Planned

| Test type | Tool | Location | Roadmap task |
|---|---|---|---|
| Backend unit, integration, API, authorization and security tests | Pytest | `apps/backend/tests/` | Configured in Phase 01.6 |
| Frontend component and form tests | Vitest and React Testing Library | `apps/frontend/` | Configured in Phase 01.6 |
| End-to-end workflow tests | Playwright | `tests/` | Introduced with the first complete user workflows |

Security-sensitive features must include tests for the failure path as well. For example, scope enforcement must be tested with out-of-scope targets, DNS rebinding, redirects and denylisted addresses.

---

## 8. Code style, formatting and linting

### Current

Python:

- Follow PEP 8.
- Use type annotations.
- Keep functions focused and names descriptive.
- Separate business logic from API routes.
- Handle errors explicitly. Never suppress errors without justification.

TypeScript:

- Use strict TypeScript settings.
- Avoid `any` without justification.
- Handle loading and error states.

General:

- Do not reformat code unrelated to your change.
- Remove unused imports and dead code.
- Never log passwords, session tokens, API keys or other secrets.

### Planned

| Item | Roadmap task |
|---|---|
| Python linting, formatting and type-checking tools and configuration | Phase 01.6 (tools not yet selected) |
| Frontend linting and formatting | Phase 01.2 |
| Import-boundary contracts (import-linter) | Phase 01.6 |

When these tools are configured, their configuration in the repository becomes the source of truth and CI will enforce it.

---

## 9. Reporting security vulnerabilities

**Do not report security vulnerabilities through public GitHub issues, pull requests or discussions.**

To report a vulnerability in AEGIS itself:

1. Use GitHub's private vulnerability reporting: open the repository's **Security** tab and select **Report a vulnerability**.
2. If that option is not available, open a public issue that asks the maintainers for a private contact channel. **Do not include any vulnerability details in that issue.**

Include in your report:

- The affected component and version or commit.
- A description of the issue and its potential impact.
- Steps to reproduce, using a local environment.
- Any suggested mitigation.

A dedicated `SECURITY.md` with a full disclosure policy and response expectations will be published before the first release.

Do not test vulnerabilities against AEGIS deployments or other systems that you do not own or are not authorized to test.

---

## 10. Licensing of contributions

AEGIS is licensed under the [Apache License 2.0](LICENSE). Under section 5 of that licence, any contribution you intentionally submit for inclusion is provided under the same licence, unless you explicitly state otherwise.

Only submit code that you have the right to contribute. Do not copy code from sources whose licences are incompatible with Apache 2.0.

---

Thank you for helping build AEGIS.

**Discover. Analyze. Protect.**

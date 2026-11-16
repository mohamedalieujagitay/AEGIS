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
- [Security Risk Register](docs/security/SECURITY_RISKS.md): known, accepted security limitations. Do not describe AEGIS as providing protections listed there as missing.

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
- Node.js 22.22.2 or later, with npm (bundled with Node.js). The minimum is declared in `apps/frontend/package.json`; the development and CI baseline, 22.23.5, is in `apps/frontend/.nvmrc`.
- PostgreSQL server binaries (`initdb`, `pg_ctl`), only to run the database tests (see below). No PostgreSQL server needs to be running.

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

Backend (Python 3.11, FastAPI), with the virtual environment activated:

```bash
cd apps/backend
pip install --require-hashes -r requirements-dev.lock   # exact, hash-checked dependencies
pip install --no-deps -e .                               # the backend itself, editable
pytest                                                   # run the backend tests
uvicorn app.main:create_app --factory --reload           # start the API locally
```

Dependencies are declared with version ranges in `apps/backend/pyproject.toml` and pinned, with SHA-256 hashes, in **two** lock files (DECISIONS.md D-046, D-051):

| Lock file | Contents | Used by |
|---|---|---|
| `apps/backend/requirements-dev.lock` | Runtime dependencies plus the `dev` extra (pytest, Ruff, mypy, import-linter) | Your virtual environment and the CI backend job |
| `apps/backend/requirements.lock` | Runtime dependencies only | The backend container image (Linux); no test or lint tools are installed in the image |

**Whenever you change a dependency declaration in `pyproject.toml`, regenerate both locks and commit them together with `pyproject.toml`.** Use Python 3.11:

```bash
cd apps/backend
pip install "pip-tools>=7.7.0,<7.8"   # the version declared in the `lock` extra; needed only for this step
python -m piptools compile --extra dev --generate-hashes --strip-extras --allow-unsafe --output-file requirements-dev.lock pyproject.toml
python -m piptools compile --generate-hashes --strip-extras --allow-unsafe --output-file requirements.lock pyproject.toml
```

Platform notes:

- Both locks are generated on Windows. pip-tools drops platform markers, so packages that are only required on Windows are pinned unconditionally and are also installed on Linux, where they are harmless: `colorama` (required by pytest on Windows; `requirements-dev.lock` only) and `tzdata` (required on Windows by psycopg, kombu and tzlocal; both locks). Generating the locks on Linux would omit them and break Windows installs, so regenerate on Windows, or check afterwards that `colorama` is still in the development lock and `tzdata` in both.
- Hashes are recorded for every published wheel and source distribution of each pinned version, so the same lock installs on Windows, Linux x86-64 and Linux ARM64. The container image installs with `--only-binary=:all:`, so every runtime dependency must publish Linux wheels.
- Regeneration is reproducible: running the commands again without changing `pyproject.toml` produces identical files.

Configuration comes from `AEGIS_*` environment variables. For local development, copy `apps/backend/.env.example` to `apps/backend/.env`. Never commit `.env` files. Without configuration the backend runs as `production` with debug mode and API documentation off. With `AEGIS_ENVIRONMENT=development`, Swagger UI is available at `http://127.0.0.1:8000/api/docs`.

Database (PostgreSQL), from `apps/backend` with the virtual environment activated:

```bash
alembic upgrade head                                    # apply migrations to the configured database
alembic revision --autogenerate -m "describe change"    # generate a migration from model changes
alembic check                                           # verify models and migrations match
```

- Set the `AEGIS_DATABASE_*` variables (see `.env.example`); `alembic.ini` never contains connection details.
- Database tests create their own throwaway PostgreSQL cluster and never use your databases. They need the PostgreSQL server binaries (`initdb`, `pg_ctl`) on `PATH`, in the standard Windows location, or in `AEGIS_TEST_POSTGRES_BIN`; otherwise they are skipped. Set `AEGIS_TEST_REQUIRE_POSTGRES=1` to make a missing installation fail the run instead, as CI does.
- See `apps/backend/migrations/README.md` for migration rules.

Backend conventions:

- Raise a subclass of `app.core.errors.AppError` for expected errors; never return exception details to clients.
- Extend `app.schemas.base.RequestModel` for request bodies.
- Use `app.database.session.get_db_session` for database access in endpoints; build SQL only with the ORM or bound parameters.
- Never log passwords, tokens, secrets, session identifiers, query strings or request bodies.

Frontend (React, TypeScript and Vite 8, managed with npm):

```bash
cd apps/frontend
npm install        # install dependencies from package-lock.json
npm run dev        # start the development server
npm run typecheck  # run strict TypeScript checks
npm run lint       # lint with Oxlint, including type-aware rules
npm run format     # format with Prettier
npm run check      # typecheck, lint and format check together
npm test           # run the tests once (Vitest)
npm run test:watch # run the tests in watch mode
npm run build      # type-check and create a production build in dist/
```

Use npm only. Do not commit lock files from other package managers. Commit `package-lock.json` whenever dependencies change.

Line endings are normalized by `.gitattributes`. Text files are stored with LF, and Windows batch files keep CRLF. You do not need to change your editor settings, but do not commit line-ending-only changes.

### Docker development environment

Prerequisite: Docker with Docker Compose v2.24 or later (Docker Desktop on Windows and macOS).

The whole stack (frontend, API, PostgreSQL, Valkey and both worker roles) runs as the Compose project `aegis`:

```bash
python infrastructure/scripts/init_dev_secrets.py                        # once: create secrets/ (gitignored)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build   # start everything
```

- Application: http://127.0.0.1:8080. API documentation: http://127.0.0.1:8000/api/docs. Health: http://127.0.0.1:8080/api/v1/health/ready.
- The development override mounts `apps/backend/app` read-only and reloads the API on changes. Restart the workers to pick up worker changes: `docker compose -f docker-compose.yml -f docker-compose.dev.yml restart worker-internal worker-assessment`.
- For frontend work, run `npm run dev` in `apps/frontend` while the stack runs: Vite proxies `/api` to the API on port 8000.
- Migrations run automatically before the API starts (`alembic upgrade head` only). Nothing is ever downgraded or dropped. To start again from an empty database, stop the stack and remove its volumes yourself: `docker compose -f docker-compose.yml -f docker-compose.dev.yml down --volumes` deletes all local AEGIS data.
- PostgreSQL and Valkey have no host ports. Inspect them through their containers, for example `docker compose exec postgres psql --username=postgres --dbname=aegis`.
- Optional settings (ports, subnets, log level, worker concurrency) are in `.env.example`; copy it to `.env` in the repository root to change them. Change `AEGIS_SUBNET_PREFIX` if the default `10.213.x.0/24` networks overlap with networks you use.

Secrets:

- `init_dev_secrets.py` never overwrites an existing file. Never commit `secrets/`, and never put passwords in `.env` or `docker-compose.yml`.
- If the script reports that `secrets/valkey_users.acl` is out of date or does not match the password files (for example after an update adds a new Valkey user, such as `healthcheck`), delete that file, run the script again, and recreate Valkey: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --force-recreate valkey`. The passwords are kept.
- Docker mounts each secret file by reference: after replacing a secret file, recreate the containers that use it.

Container smoke test (also run in CI):

```bash
python infrastructure/scripts/smoke_test.py --build
```

It runs the production-like stack as a separate project, `aegis-smoke`, with temporary secrets, its own networks, port 18080 and its own volumes, checks more than 100 conditions, and then removes only the `aegis-smoke` resources. Your `aegis` stack and data are not touched.

Container rules:

- Images are built locally only. **Never publish, push or distribute AEGIS images** until the distribution-compliance review is complete (DECISIONS.md D-059).
- Keep every service non-root, with a read-only root filesystem, no capabilities, `no-new-privileges` and resource limits. Never mount the Docker socket and never add privileged mode.
- Pin base images by digest. Add files to an image through the Dockerfile's `.dockerignore` allowlist only.
- The assessment worker must never receive database credentials or join the `data` network.

Do not submit code that relies on packages that are not declared in `apps/backend/pyproject.toml` or `apps/frontend/package.json`.

---

## 3. Repository structure

### Current

```text
AEGIS/
├── .github/              # CI workflows, pull request and issue templates
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
│   ├── docker/           # Dockerfiles, nginx, Valkey and PostgreSQL configuration
│   └── scripts/          # init_dev_secrets.py, smoke_test.py
├── tests/                # End-to-end tests (Playwright)
├── .env.example          # optional Docker Compose settings
├── docker-compose.yml    # secure, production-like base
├── docker-compose.dev.yml  # development override
├── CONTRIBUTING.md
├── LICENSE
├── README.md
└── THIRD_PARTY_NOTICES.md
```

The planned internal structure of the backend and frontend is described in [SYSTEM_ARCHITECTURE.md §3–4](docs/architecture/SYSTEM_ARCHITECTURE.md).

Architectural boundaries that contributions must respect:

- API routes stay thin. Business logic belongs in services and modules.
- Worker-side code (`app.workers.assessment`, `app.modules.*.engine`, `app.netguard`, `app.contracts`) must not import database code, directly or indirectly (SYSTEM_ARCHITECTURE §4.5). An import-linter contract in `apps/backend/pyproject.toml` enforces this; run `lint-imports` from `apps/backend`.
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

Use the pull request template, which GitHub fills in automatically. The title must follow Conventional Commits (section 5), because pull requests are squash-merged and the title becomes the commit message; CI checks it.

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
4. Include tests for new behaviour (section 7).
5. Update documentation affected by the change.
6. Include an Alembic migration for every database schema change, and review generated migrations before committing them.
7. Update [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) when adding, removing or upgrading a dependency, and explain why the dependency is needed. Update `requirements-dev.lock` or `package-lock.json` in the same pull request. New dependencies need maintainer approval.
8. Contain no secrets, credentials, private keys, `.env` files or local tool configuration.
9. Not claim that functionality works without having run it.

Pull requests that change authentication, authorization, scope enforcement, SSRF protection, worker isolation or result ingestion receive additional security review.

### Continuous integration

GitHub Actions (`.github/workflows/ci.yml`) runs on every pull request and every push to `main`:

| Job | Checks |
|---|---|
| Backend (Python 3.11) | Hash-checked install and `pip check`, `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, `pytest` (database tests included, against a disposable PostgreSQL 18 cluster) |
| Frontend (Node.js) | `npm ci`, `npm run typecheck`, `npm run lint`, `npm run format:check`, `npm test`, `npm run build` |
| Containers (build and smoke test) | Builds both images and runs `infrastructure/scripts/smoke_test.py`: health, API proxy, worker isolation, Valkey ACLs, database roles, container security and graceful shutdown. Images are never pushed. |
| Conventional Commits title | The pull request title format (`.github/workflows/pr-title.yml`) |

Run the same checks locally before opening a pull request, and state in the description what you ran. A pull request is merged only when all checks pass.

Issues use forms for bug reports and feature requests. Security vulnerabilities are never reported in issues (section 9).

Recommended repository settings (merge method, branch protection and Actions permissions) are listed in [DECISIONS.md D-049](docs/architecture/DECISIONS.md). Maintainers apply them manually.

---

## 7. Testing

### Current

| Test type | Tool | Location | Run |
|---|---|---|---|
| Backend unit, integration, API, database, authorization and security tests | Pytest | `apps/backend/tests/` | `pytest` in `apps/backend` |
| Frontend component, form and routing tests | Vitest, React Testing Library, user-event, jest-dom | `apps/frontend/src/**/*.test.ts(x)`, next to the code | `npm test` in `apps/frontend` |

- Backend: tests that need PostgreSQL are marked `database` automatically. `pytest -m "not database"` runs only the fast tests. Warnings fail the run, so fix deprecations when they appear.
- Frontend: test behaviour as users experience it. Query by role, label and accessible name, use `userEvent` for interaction, and render pages through the real route configuration with a memory router. Test files are type-checked and linted like application code.

Rules that apply to all tests:

- Run tests only against local, controlled environments and deliberately vulnerable test applications. **Never run tests against external systems you are not authorized to assess.**
- **Generate test certificates and keys dynamically at test run time.** Never commit private keys or certificates, including inside test fixture directories. The `.gitignore` blocks common key formats everywhere in the repository.
- Do not use mock data as a substitute for production functionality. Mock data is acceptable inside isolated tests.
- Do not report tests as passing unless you ran them.

### Planned

| Test type | Tool | Location | Roadmap task |
|---|---|---|---|
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

Frontend (configured):

- Oxlint (`apps/frontend/.oxlintrc.json`) with React, React Hooks, jsx-a11y, TypeScript and type-aware rules. Run `npm run lint`.
- Prettier (`apps/frontend/.prettierrc.json`) with Tailwind CSS class sorting. Run `npm run format`, or `npm run format:check` to check without changing files.
- Use design tokens from `src/index.css` for colours, radii and widths. Tailwind's default colour palette is disabled, so do not add arbitrary colour values; add a token instead.
- Run `npm run check` before opening a pull request.

Backend (configured in `apps/backend/pyproject.toml`), run from `apps/backend`:

```bash
ruff check .            # lint (add --fix to apply safe fixes)
ruff format .           # format; ruff format --check . only checks
mypy                    # strict type checking of app, migrations and tests
lint-imports            # import-boundary contracts (SYSTEM_ARCHITECTURE §4.5)
```

- Line length is 100, matching the frontend.
- Suppress a rule only on the affected line (`# noqa: <code>`), with a comment explaining why. Do not use `assert` in application code; it is removed when Python runs with `-O`.

The configuration in the repository is the source of truth, and CI enforces it.

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

# AEGIS — Decision Register

**Status:** Living document  
**Last Updated:** 2026-11-16  
**Related:** [PROJECT_VISION.md](../PROJECT_VISION.md) · [PRODUCT_REQUIREMENTS.md](../PRODUCT_REQUIREMENTS.md) · [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) · [DEVELOPMENT_ROADMAP.md](../development/DEVELOPMENT_ROADMAP.md)

This register records approved product and architecture decisions. Changing one of these decisions requires a new entry that supersedes the old one. Entries are never edited silently.

| ID | Decision | Date | Status |
|---|---|---|---|
| D-001 | Modular monolith | 2026-11-15 | Approved |
| D-002 | Apache 2.0 licence, subject to dependency review | 2026-11-15 | Approved |
| D-003 | No Nmap or Scapy in the MVP; native TCP connection engine | 2026-11-15 | Approved |
| D-004 | Server-side sessions in httpOnly cookies; Argon2id | 2026-11-15 | Approved |
| D-005 | Workspace RBAC: Owner, Admin, Analyst, Viewer | 2026-11-15 | Approved |
| D-006 | Three authorization mechanisms: DNS TXT, HTTP, administrative attestation | 2026-11-15 | Approved |
| D-007 | Python 3.11 with pip, venv and `pyproject.toml` | 2026-11-15 | Approved |
| D-008 | Synchronous SQLAlchemy 2.x with psycopg 3 | 2026-11-15 | Approved |
| D-009 | Valkey as the message broker | 2026-11-15 | Approved |
| D-010 | Enforced separation between assessment workers and the database | 2026-11-15 | Approved |
| D-011 | Signed job payloads, per-job ingestion tokens, separate ingestion listener | 2026-11-15 | Approved; payload-visibility limitation tracked as SR-001 (D-060) |
| D-012 | Administrator and CLI password reset only in v0.1.0 | 2026-11-15 | Approved; implemented by D-068 |
| D-013 | Withdrawn | 2026-11-15 | Withdrawn |
| D-014 | Repository layout; end-to-end tests in `apps/frontend/e2e/` (amended 2026-11-17); no `packages/` or top-level `workers/` | 2026-11-15 | Approved; amended 2026-11-17 |
| D-015 | GitHub Actions for CI | 2026-11-15 | Approved |
| D-016 | Frontend tooling deferred until frontend implementation | 2026-11-15 | Resolved by D-021 to D-026 (data-fetching library still open) |
| D-017 | Domain verification does not authorize active assessment of resolved IPs | 2026-11-15 | Approved |
| D-018 | Instance administrator; CLI bootstrap; open registration off by default | 2026-11-15 | Approved; implemented by D-061 |
| D-019 | Third-party lookups disabled by default | 2026-11-15 | Approved |
| D-020 | Two worker roles: assessment and internal | 2026-11-15 | Approved |
| D-021 | Vite 8 as the frontend build tool | 2026-11-15 | Approved |
| D-022 | React Router 8 for routing | 2026-11-15 | Approved |
| D-023 | npm as the frontend package manager | 2026-11-15 | Approved |
| D-024 | Node.js 22 LTS, version 22.22.0 or later | 2026-11-15 | Superseded by D-047 (minimum 22.22.2) |
| D-025 | Template linter (oxlint) removed; linter chosen in its roadmap task | 2026-11-15 | Resolved by D-033 |
| D-026 | TypeScript 7, subject to compatibility testing | 2026-11-15 | Approved; linting, formatting and testing tools verified (D-033, D-047) |
| D-027 | Strict TypeScript compiler profile | 2026-11-15 | Approved |
| D-028 | Tailwind CSS 4, CSS-first, through the official Vite plugin | 2026-11-15 | Approved |
| D-029 | Frontend routing architecture | 2026-11-15 | Approved |
| D-030 | In-house UI components; no component or class-merging library | 2026-11-15 | Approved |
| D-031 | Application shell, navigation and error handling | 2026-11-15 | Approved; navigation amended by D-034 |
| D-032 | Design tokens; Tailwind default palette removed | 2026-11-15 | Approved; token values superseded by D-035 |
| D-033 | Oxlint with type-aware rules, and Prettier, for the frontend | 2026-11-15 | Approved |
| D-034 | Overview and shell built from the approved UI design, with empty states | 2026-11-15 | Approved; extended by D-035 |
| D-035 | Full AEGIS UI design: stylesheet tokens and all seven pages, with empty states | 2026-11-15 | Approved; input border gap resolved by D-036 |
| D-036 | Form control border token meeting WCAG non-text contrast | 2026-11-15 | Approved |
| D-037 | Workflow-based navigation with a module mapping (PRD §5.2) | 2026-11-15 | Approved |
| D-038 | Dashboard metrics aligned with the approved design (PRD §5.3) | 2026-11-15 | Approved |
| D-039 | Phase 1.3 split into two bundles | 2026-11-15 | Approved |
| D-040 | Backend packaging, application factory and configuration | 2026-11-15 | Approved; lock file chosen in D-046; worker-side packages created by D-048 |
| D-041 | Backend test client and FastAPI's OpenTelemetry dependency | 2026-11-15 | Approved; Uvicorn and httpx2 approved |
| D-042 | Backend errors, logging, request validation and API documentation | 2026-11-15 | Approved; server header and Swagger UI open items resolved by D-051 and D-056; documentation access restricted by D-069 |
| D-043 | Database foundation: configuration, engine, sessions, ORM base and migrations | 2026-11-15 | Approved; psycopg Linux wheel reviewed in D-059 |
| D-044 | Database tests use a disposable PostgreSQL cluster | 2026-11-15 | Approved; CI provisioning in D-048 |
| D-045 | Backend test configuration, linting, formatting and type checking | 2026-11-16 | Approved |
| D-046 | Backend dependency lock file with pip-tools | 2026-11-16 | Approved; runtime lock `requirements.lock` added by D-051, both documented in CONTRIBUTING §2 |
| D-047 | Frontend testing with Vitest; Node.js 22.22.2 or later | 2026-11-16 | Approved; supersedes D-024, resolves D-026 |
| D-048 | Continuous integration workflow and import-boundary contracts | 2026-11-16 | Approved |
| D-049 | Pull request conventions and recommended repository settings | 2026-11-16 | Approved; required checks extended by D-058 |
| D-050 | Phase 1.5 scope and Docker Compose layout | 2026-11-16 | Approved |
| D-051 | Container images | 2026-11-16 | Approved |
| D-052 | Services, networks, frontend proxy and startup order | 2026-11-16 | Approved |
| D-053 | Secrets and environment variables | 2026-11-16 | Approved |
| D-054 | PostgreSQL roles | 2026-11-16 | Approved; migration metadata restricted by D-060 |
| D-055 | Valkey and the Celery application skeleton | 2026-11-16 | Approved; healthcheck user authenticated by D-060 |
| D-056 | Swagger UI served from local assets | 2026-11-16 | Approved |
| D-057 | Health checks | 2026-11-16 | Approved; probe logging and Valkey health check amended by D-060 |
| D-058 | Container smoke test in CI | 2026-11-16 | Approved |
| D-059 | Linux psycopg wheel review; container images are not distributed | 2026-11-16 | Approved; keyutils licence and versions reconciled in D-060; distribution compliance review pending |
| D-060 | Phase 1.5 review corrections | 2026-11-16 | Approved |
| D-061 | Phase 2.1 authentication scope, administration and CLI | 2026-11-17 | Approved |
| D-062 | Argon2id password hashing (argon2-cffi 25.1.0, bindings 26.1.0) | 2026-11-17 | Approved |
| D-063 | Identifiers and password policy | 2026-11-17 | Approved; common-password list deferred (SR-006) |
| D-064 | Server-side sessions in `__Host-` cookies; idle and absolute expiry | 2026-11-17 | Approved |
| D-065 | CSRF protection: Origin check and signed, session-bound double submit | 2026-11-17 | Approved |
| D-066 | Distributed sign-in rate limiting in Valkey, failing closed | 2026-11-17 | Approved; account-wide lockout corrected by D-070; shared-address limitation tracked as SR-005 |
| D-067 | Structured security logging for authentication | 2026-11-17 | Approved; persistent audit log in roadmap 2.6 |
| D-068 | Administrator password reset tokens | 2026-11-17 | Approved |
| D-069 | API documentation restricted to instance administrators | 2026-11-17 | Approved |
| D-070 | Two-phase sign-in rate limiting and trusted-device exemption | 2026-11-17 | Approved by the project owner with ten conditions (2026-11-17); residual risks in SR-009 |
| D-071 | One email normalization for sign-in, registration, CLI and rate limits; lower-case database constraint | 2026-11-17 | Implemented |
| D-072 | Reset-token cleanup, CLI operator record, startup preparation and broker pool | 2026-11-17 | Implemented |
| D-073 | End-to-end authentication and trusted-device tests with Playwright, in CI | 2026-11-17 | Approved by the project owner (2026-11-17); running in the Containers CI job since run 44124113383; see D-074 |
| D-074 | Phase 2.1 closed with one registration browser-test failure unexplained | 2026-11-17 | Approved by the project owner (2026-11-17); see the section below |
| D-075 | Account management: profile, password and sessions (Phase 2.2) | 2026-11-17 | Implemented; verification pending the remote CI run |
| D-076 | Locally maintained security patch for picomatch (GHSA-fc5q-39xc-vjpf) | 2026-11-18 | Implemented and verified locally; upstream advisory open (no fixed release) |

---

## D-001 — Modular monolith

One backend application with clearly bounded modules, plus background workers. It is easier to develop, test and operate than microservices. Microservices require explicit approval.

**Affects:** SYSTEM_ARCHITECTURE §1.

## D-002 — Apache 2.0 licence

Proposed project licence, subject to a complete dependency licence review before release. Dependencies are tracked in `THIRD_PARTY_NOTICES.md`.

## D-003 — No Nmap or Scapy in the MVP

Nmap's licence (NPSL) treats software designed to execute Nmap and parse its results as potentially derivative work. Scapy is GPL-2.0. Neither is bundled or integrated in the MVP. Running a tool as an external process is not assumed to resolve licensing obligations. AEGIS uses its own TCP connection-based assessment engine. OWASP ZAP may become an optional, isolated integration after v0.1.0.

**Affects:** PRD §2.2, SYSTEM_ARCHITECTURE §15, ROADMAP Phase 04 and 06.

## D-004 / D-005 / D-006 — Authentication, RBAC and authorization mechanisms

Defined in PRD §3.1–3.3 and SYSTEM_ARCHITECTURE §9–10.

## D-007 — Python 3.11

The existing virtual environment uses Python 3.11. Migration to a newer Python or to `uv` is deferred.

## D-008 — Synchronous SQLAlchemy 2.x with psycopg 3

Simpler to test and reason about than the async stack. FastAPI runs synchronous endpoints in a thread pool, which is sufficient for a self-hosted platform. psycopg 3 is LGPL-3.0 and is noted in `THIRD_PARTY_NOTICES.md`.

## D-009 — Valkey

Redis 7.4+ uses RSALv2/SSPLv1, and Redis 8 adds AGPLv3. Valkey is BSD-3-Clause and protocol-compatible.

**Affects:** SYSTEM_ARCHITECTURE §2.4, `THIRD_PARTY_NOTICES.md`.

## D-010 — Worker and database separation

Worker-side packages must not import database sessions, models or database libraries. This is enforced by import-linter contracts in CI, and at runtime by giving assessment workers no database credentials and no access to the `data` network.

**Affects:** SYSTEM_ARCHITECTURE §4.5.

## D-011 — Job integrity and result ingestion

- Jobs are signed with Ed25519. Only the backend holds the private key, so workers cannot forge jobs.
- Each job carries a random ingestion token. The database stores only its hash, and the token is valid only while the job is active.
- Results are submitted to a separate internal listener on the `ingest` network and validated for token, state, schema, scope and idempotency.

Known limitation: assessment workers sharing a queue can read each other's job payloads.

**Affects:** SYSTEM_ARCHITECTURE §6.4–6.5.

## D-012 — Password reset

v0.1.0 supports only instance-administrator and CLI password reset. Self-service and email-based reset wait for SMTP support (Phase 09).

**Affects:** PRD FR-AUTH-005.

## D-013 — Withdrawn

This entry has been withdrawn.

## D-014 — Repository layout

Amended 2026-11-17 (project owner approval, Phase 2.1 closure). The Playwright end-to-end tests live in `apps/frontend/e2e/`, next to the frontend that they test, and not in the root `tests/` directory. Playwright is a frontend development dependency, and Node resolves it from the location of the test files, so the root location would need a second dependency tree. The root `tests/` directory is reserved for cross-application tests. The empty `packages/` and top-level `workers/` directories were removed. Workers live in `apps/backend/app/workers/`, and a shared package directory will be introduced only when a genuine shared package exists.

## D-015 — Continuous integration

GitHub Actions runs linting, formatting checks, type checking, import contracts and tests on every pull request. The specific tools are selected in Phase 01.

## D-016 — Frontend tooling

Build tool, router and data-fetching library are decided when frontend implementation begins.

**Update:** build tool, router, package manager, Node.js version and TypeScript version were decided at the start of Phase 01.2 (D-021 to D-026). The data-fetching library remains open.

## D-017 — Domain verification and resolved IP addresses

A verified domain may resolve to infrastructure the user does not own (CDNs, hosting and SaaS providers).

- DNS inspection, certificate transparency and TLS inspection of the hostname on port 443 require only domain scope.
- TCP port assessment, service identification and TLS on other ports require every target IP to be covered by an `ip` or `cidr` scope entry. Such an entry can be created through attestation.

**Affects:** PRD FR-ASSET-004, SYSTEM_ARCHITECTURE §10.2.

## D-018 — Instance administration

- An instance-level administrator flag exists, separate from workspace roles.
- It grants no implicit workspace data access.
- The first administrator is created through the CLI, and no default credentials are shipped.
- Open registration is disabled by default.

**Affects:** PRD FR-AUTH-001, FR-AUTH-006.

## D-019 — Third-party lookups

Certificate transparency, passive DNS and future intelligence feeds are disabled by default. The instance administrator enables them after seeing a privacy notice, and workspaces can opt out. AEGIS sends no telemetry.

**Affects:** PRD §4.6, SYSTEM_ARCHITECTURE §12.5.

## D-020 — Two worker roles

Report generation needs database access, but assessment workers must not have it. The two roles are:

- **Assessment workers:** untrusted, with outbound access and no database.
- **Internal workers:** trusted, with database access and no outbound access.

**Affects:** SYSTEM_ARCHITECTURE §6.1.

## D-021 — Vite 8

Vite 8 is the frontend build tool and development server. The application was initialized from the official `react-ts` template (create-vite 9.3.4), with all demonstration content removed.

**Affects:** SYSTEM_ARCHITECTURE §2.1, `THIRD_PARTY_NOTICES.md`.

## D-022 — React Router 8

React Router 8 is the routing library. It is installed during the routing task of Phase 01.2, not before. It requires Node.js 22.22.0 or later (D-024).

## D-023 — npm

npm, bundled with Node.js, is the frontend package manager. `package-lock.json` is committed for reproducible installs. No additional package manager is required.

## D-024 — Node.js 22.22.0 or later

The frontend requires Node.js 22 LTS, version 22.22.0 or later, declared in the `engines` field of `apps/frontend/package.json`. This is the minimum required by React Router 8.

## D-025 — No linter in the initial scaffold

The Vite template's default linter (oxlint) was removed because it was not an approved dependency. The frontend linting and formatting tools are selected in the roadmap task "Configure frontend linting and formatting".

## D-026 — TypeScript 7

The frontend uses TypeScript 7 (`~7.0.2`), the version shipped with the official template. TypeScript 7 is a new native compiler, and some tooling may lag behind it. Compatibility is tested when linting and testing tools are introduced. If a required tool is incompatible, the fallback is the latest TypeScript 5.x release, recorded as a new decision.

## D-027 — Strict TypeScript compiler profile

Both `tsconfig.app.json` (application code) and `tsconfig.node.json` (build-tool code) set `strict` explicitly, even though TypeScript 7 enables it by default, so that the configuration does not depend on compiler defaults.

Additional checks: `noUncheckedIndexedAccess`, `noImplicitOverride`, `noImplicitReturns`, `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch` and `forceConsistentCasingInFileNames`. Application code also enables `noPropertyAccessFromIndexSignature` and `useUnknownInCatchVariables`.

`exactOptionalPropertyTypes` is not enabled because it conflicts with common React prop patterns. Type checking runs with `npm run typecheck` and as part of `npm run build`.

## D-028 — Tailwind CSS 4

Tailwind CSS 4 is integrated through the official `@tailwindcss/vite` plugin. Configuration is CSS-first: `src/index.css` imports Tailwind and holds base styles, and there is no `tailwind.config` or PostCSS configuration file.

Until the design tokens task, components use Tailwind's default palette (slate neutrals, blue accent). That task replaces these with project tokens.

## D-029 — Frontend routing architecture

- React Router 8 in data-router mode: `createBrowserRouter` with `RouterProvider` from `react-router/dom`.
- `src/app/router/routes.tsx` holds the central route configuration, separate from router creation (`router.ts`), so the same routes can be used with a memory router in tests.
- `src/app/router/paths.ts` holds route path constants. Code uses these instead of hard-coded path strings.
- Pages live outside the router: feature pages in `src/features/<feature>/pages/`, and application-level pages (such as the not-found page) in `src/app/pages/`.
- The landing route `/` is the Overview page of the `dashboard` feature. It shows no statistics until real data exists.

## D-030 — In-house UI components

AEGIS uses its own small component set in `src/components/ui/` (Button, Input, Card, Badge, Heading, Text) and `src/components/layout/` (PageContainer), with no component library.

- Class names are joined with a small local helper (`src/lib/cx.ts`) instead of adding clsx or tailwind-merge. Callers add classes; they do not override a component's built-in styles.
- Components are presentational and contain no business logic. Domain mappings (for example, finding severity to badge tone) belong to features.
- Accessibility conventions: buttons default to `type="button"`; inputs require a visible label and wire hints and errors through `aria-describedby` and `aria-invalid`; titled cards are labelled sections; headings take an explicit semantic level; badges must state their meaning in text, not colour alone; and interactive elements show a visible focus outline.

## D-031 — Application shell, navigation and error handling

The application shell (`src/app/layout/AppLayout.tsx`) provides a skip link, a header, a sidebar on large screens, a disclosure menu on smaller screens and the single `<main id="main-content">` landmark.

- Navigation is configured in `src/app/navigation/navigation.ts`. It lists only implemented routes (PRD §5.2), so it never leads to placeholder pages.
- After client-side navigation, focus moves to `<main>`, so keyboard and screen reader users start at the new page. The mobile menu closes on navigation and on Escape, returning focus to its button.
- Document titles use React 19's `<title>` element, rendered by `PageContainer` in the form "Page · AEGIS".
- Two error boundaries: `RouteErrorPage` handles errors from pages inside the shell, so navigation stays available, and `RootErrorPage` handles failures of the shell itself and provides its own `<main>`. Technical error details appear only in development builds.

## D-032 — Design tokens

Design tokens are defined centrally in `src/index.css` using Tailwind CSS 4's `@theme`:

- Semantic colour tokens for surfaces (`canvas`, `surface`, `surface-raised`, `surface-overlay`), borders (`line`, `line-strong`), text (`fg-heading`, `fg`, `fg-muted`, `fg-subtle`), the primary accent, the focus ring, status colours (`success`, `warning`, `danger`, `info`) and a finding severity palette (`severity-critical` to `severity-info`).
- **Tailwind's default colour palette is removed** (`--color-*: initial`), so components can only use project tokens. A new colour must be added as a token.
- Radius tokens (`rounded-control`, `rounded-card`) and a content width token (`max-w-content`).
- System font stacks only: no web fonts are fetched from third parties (consistent with D-019).
- Every text and background pair meets WCAG AA (at least 4.5:1). Contrast must be re-checked when a token changes.

The severity palette carries no meaning on its own. Mapping findings to severities belongs to the vulnerability management feature. This supersedes the temporary use of the default palette described in D-028.

## D-033 — Frontend linting and formatting

**Linter: Oxlint 1.x with oxlint-tsgolint (type-aware rules). Formatter: Prettier 3 with prettier-plugin-tailwindcss.**

Evaluation (Phase 01.2.8):

- **ESLint with typescript-eslint was rejected for now.** typescript-eslint 8.72.2 supports only TypeScript below 6.1, and TypeScript 7's package no longer exposes the JavaScript compiler API (`createProgram`, `createSourceFile`) that typescript-eslint depends on. eslint-plugin-jsx-a11y also did not yet declare support for ESLint 10. Using ESLint would have required downgrading TypeScript, which was not approved.
- **Biome** ran correctly but missed a type-aware check (floating promises) in a probe file.
- **Oxlint with oxlint-tsgolint** detected every probe violation, including type-aware rules. oxlint-tsgolint is built on TypeScript 7 itself. It provides React, React Hooks, jsx-a11y, TypeScript and import rules.
- **Prettier** is the established formatter. The official Tailwind CSS plugin sorts utility classes and reads the CSS-first configuration.

Configuration is in `apps/frontend/.oxlintrc.json` and `apps/frontend/.prettierrc.json`. Scripts: `lint`, `lint:fix`, `format`, `format:check` and `check` (typecheck, lint and format check together).

This resolves D-025. D-026 (TypeScript 7) remains conditional until the testing tools are verified.

## D-034 — Overview and shell built from the approved UI design

The application shell and Overview page follow the HTML design supplied by the project owner: a collapsible sidebar with brand, navigation and workspace area; a header with search, notifications and help; and an Overview with four metric cards, risk distribution, findings trend, recent assessments and recent activity.

Approved choices:

- **No sample data.** The design's sample figures, table rows, activity entries and user name are not used. Every metric and list shows an empty state until real data exists (PRD §5.3). Reusable components in `src/components/data/` (StatCard, Sparkline, DonutChart, TrendChart, DataTable, ActivityList) accept real data and were verified with test data only.
- **Navigation shows the full structure.** The sidebar lists Overview, Assets, Assessments, Findings, Reports, Activity and Settings. Items whose pages do not exist are "planned": visible, marked "Soon", disabled and not focusable, so they never lead to placeholder pages. This amends the "implemented routes only" rule in D-031.
- **Controls without a feature are disabled, not simulated.** Search, notifications, help, "New Assessment" and the period selector are disabled with accessible names that say they are not available yet. The workspace area shows "No workspace" until authentication exists; no user menu is shown.
- **Styling** was recreated with Tailwind and design tokens (the design's stylesheet was not supplied). New tokens: `violet` (text-safe accent) and `brand-950` to `brand-300` (logo and chart lines). `brand-500` is a graphic colour only: white text on it is 3.82:1, so buttons keep `primary`.
- Charts are accessible: the donut has a text caption and a legend, and the trend chart provides a visually hidden data table.

**Open item (resolved by D-037):** the design's navigation differed from PRD §5.2. PRD §5.2 now follows the design, with a module mapping.

## D-035 — Full AEGIS UI design

The project owner supplied a complete single-file prototype (HTML, CSS and in-browser sample data) covering seven pages. The approved use:

- **Styling matches the prototype stylesheet.** Its colours, sizes, radii, gradients, card, navigation, table, badge and form styles are translated into Tailwind tokens in `src/index.css`. The prototype's layout breakpoints (1100, 1200, 1400 and 1500 px) are named theme breakpoints (`split`, `charts`, `stats4`, `stats5`).
- **All seven pages exist as real routes:** Overview, Assets, Assessments, Findings, Reports, Activity and Settings. Every navigation item is now available; the "planned" mechanism from D-034 remains for future modules.
- **No sample data and no simulated behaviour.** Metrics show "—", lists show empty states, and actions (add, import, export, new assessment, generate report, save settings) are disabled until their backend exists. Each page connects to the API in the roadmap phase that builds it.
- **The prototype file is not stored in the repository.**

Deviations from the prototype, for accessibility or to follow the approved requirements:

| Prototype | Implementation | Reason |
|---|---|---|
| Primary button gradient #2a86ff to #1a6bf0 | #226cee to #1a5fd6 | White text was 3.53:1 at the top; now at least 4.72:1 (WCAG AA) |
| Active page number #1a73f0, active settings tab #2f7dff | Primary blue | White text was 4.42:1 and 3.82:1 |
| Asset types Domain, Web App, Network, IP Address, Server; "Applications" metric; Owner column | Domain, IP address, CIDR range, Service; "CIDR Ranges" metric; no Owner column | PRD FR-ASSET-001 asset types; assets belong to the workspace |
| Assessment status "Scheduled" | "Queued" | Scheduling is Phase 09; PRD FR-JOB-002 statuses |
| Assessment types (Web App, API, Database, ...) | DNS analysis, Subdomain discovery, TCP port assessment, TLS assessment | v0.1.0 engines (SYSTEM_ARCHITECTURE §7.2) |
| "Add Finding" (manual findings) | Not included | Findings come from assessment results (PRD §3.7) |
| Report types (Executive, Technical, ...) | Format: PDF or JSON | PRD FR-REPORT-001 and FR-REPORT-002 |
| Finding status filter: Open, In Progress, Resolved | Tabs as designed; the status filter lists all six PRD lifecycle statuses | PRD FR-VULN-004 |
| Security settings: two-factor authentication, IP allowlist | Scope enforcement (always on), session expiration, login rate limiting | Only controls in the approved requirements are shown |
| Integrations: Slack, GitHub, Jira, webhooks, SIEM | Empty state referring to optional third-party lookups | Not in the approved requirements |
| Small screens: horizontal navigation strip | Menu button with disclosure navigation | Kept from D-031 (focus management, Escape to close) |

Known accessibility gap: input borders (#22345a) are 1.5:1 against card surfaces, below the 3:1 guideline for component boundaries. Resolved by D-036.

## D-036 — Form control border contrast

Form control boundaries use a dedicated `field-border` token (`#566c93`) instead of the design's `#22345a`. It applies to inputs, textareas, selects, search fields (including the header search) and the list/grid view toggle.

WCAG 2.2 success criterion 1.4.11 (non-text contrast) requires at least 3:1 for the visual boundary that identifies a control. Measured contrast of the new border:

| Adjacent colour | Before (#22345a) | After (#566c93) |
|---|---|---|
| `canvas` #050b17 (field fill, page) | 1.60:1 | 3.71:1 |
| `sidebar` #07101f (header) | 1.55:1 | 3.59:1 |
| `surface` #091426 (card bottom) | 1.50:1 | 3.48:1 |
| `surface-raised` #0c1a30 (card top) | 1.42:1 | 3.29:1 |

Other control states already met the criterion: the focus and hover border (`chart-blue`, at least 4.56:1) and the error border (`chart-red`, at least 4.63:1). Disabled controls are exempt under 1.4.11.

`line-strong` is unchanged and remains in use for non-interactive containers.

## D-037 — Workflow-based navigation

PRD §5.2 originally listed navigation by security module (Reconnaissance, Network Security, Web & API Security, System Security, Threat Intelligence, Vulnerabilities, Monitoring). The approved UI design organises navigation by user workflow: Overview, Assets, Assessments, Findings, Reports, Activity, Settings.

Analysis showed no v0.1.0 requirement is lost:

- **Renamed:** Vulnerabilities is shown as Findings, the term the PRD itself uses (FR-VULN-001).
- **Grouped:** Reconnaissance and Network Security are assessment types under Assessments; their results (subdomains, DNS records, certificates, relationships, services by host) appear on Assets.
- **Added:** Activity presents the workspace audit log that the PRD already requires (§4.1, FR-WS-003, FR-AUTH-006).
- **Deferred, unchanged:** Web & API Security (Phase 06), Threat Intelligence (Phase 07), System Security (Phase 08) and Monitoring (Phase 09) appear when implemented, as §5.2 always allowed.

PRD §5.2 was updated to the workflow navigation with a table mapping every module and requirement to its location. No functional requirement was removed or renamed. The frontend navigation already matched, so no code change was needed.

Consequences:

- **Phase 02:** Activity must be hidden from, and refused by the backend to, Analysts and Viewers, because only Owners and Admins may view the workspace audit log (FR-WS-003). Recorded in DEVELOPMENT_ROADMAP.md task 2.4; not implemented in Phase 1.2.
- **Phase 03:** assessment scope and authorization (FR-ASSET-003, FR-ASSET-004) are managed on the Assets page.

## D-038 — Dashboard metrics

PRD §5.3 originally required: total assets, active services, total findings, critical findings, recent assessments, recent activity and severity distribution. The approved design shows: total assets, assessments, open findings, critical risks, risk distribution, findings trend, recent assessments and recent activity.

PRD §5.3 was updated to the design's metrics:

- **Total findings** remain visible as the total in the risk distribution chart; the metric card shows **open findings**, which is more useful for triage.
- **Critical findings** are shown as **critical risks**: open findings with critical severity.
- **Active services** move from the dashboard to the network inventory on the Assets page (FR-NET-004), where services are listed by host. No capability is removed.
- **Assessments** and the **findings trend** are added.

All statistics must still come from real application data, with empty states until data exists.

## D-039 — Phase 1.3 bundles

Roadmap task 1.3 (Backend Foundation) is implemented in two bundles, in roadmap order:

- **Bundle 1:** initialize FastAPI on Python 3.11 (pip, venv and `pyproject.toml`); establish the modular application structure; configure API routing; implement configuration management.
- **Bundle 2:** centralized exception handling; logging; request validation; API documentation.

Out of scope for Phase 1.3: health-check endpoints (task 1.5), database and Alembic (task 1.4), full Pytest configuration and Python lint and type-check tooling (task 1.6).

## D-040 — Backend packaging, application factory and configuration

- **Packaging:** `apps/backend/pyproject.toml` with the setuptools build backend; installed with `pip install -e "apps/backend[dev]"` into the repository `.venv` (Python 3.11). The version has a single source, `app.__version__`. Dependencies use compatible version ranges; a lock-file tool is still to be chosen (task 1.6).
- **Structure:** the `app` package follows SYSTEM_ARCHITECTURE §4.1. Only the packages needed now exist (`app.api`, `app.api.v1`, `app.core`); the others are created by the tasks that need them, so there are no empty placeholder packages.
- **Application factory:** `app.main.create_app(settings)` builds the application, so tests can pass explicit settings. Run with `uvicorn app.main:create_app --factory`.
- **Routing:** `app.api.router.build_api_router()` mounts every router registered in `app.api.v1.ROUTERS` under `/api/v1`. There are no unversioned routes. The previous placeholder `main.py`, whose `/` route always reported "operational" without checking anything, was removed.
- **Configuration:** `app.core.config.Settings` (pydantic-settings) reads `AEGIS_*` environment variables and, for local development, an optional `.env` file; environment variables take precedence. Settings are immutable and validated at startup, so invalid configuration stops the application instead of running with surprises. Secure defaults: `production` environment and debug off; debug is rejected in production. Secrets are never given defaults.
- **API documentation** (`/docs`, `/redoc`, `/openapi.json`) is disabled until Bundle 2 configures it.

## D-041 — Backend test client and FastAPI's OpenTelemetry dependency

- **httpx2** replaces httpx as the development dependency behind FastAPI's TestClient. Starlette 1.10 deprecates httpx for its TestClient and imports httpx2 (BSD-3-Clause, same author, Pydantic organisation) when available.
- **opentelemetry-api** is installed because FastAPI 0.163 requires it. It is the API layer only and is inert without an SDK and exporter, which AEGIS does not install, so no telemetry is collected or sent (PRD §4.6). Adding an OpenTelemetry SDK or exporter in future requires a decision and must stay disabled by default.

## D-042 — Backend errors, logging, request validation and API documentation

Phase 1.3 Bundle 2. No new dependencies; everything uses FastAPI, Starlette, Pydantic and the Python standard library.

**Centralized exception handling** (`app/core/errors.py`)

- Every error response has one shape, `ErrorResponse`: `{"error": {"code", "message", "request_id", "details"?}}`. The request ID is also returned in the `X-Request-ID` header.
- Expected errors subclass `AppError` with a status code, a stable code and a message that is safe to show. Framework errors (404, 405 and others) use the standard reason phrase, never the exception detail.
- Unexpected exceptions return a generic 500 `internal_error` and are logged server-side with their traceback and request ID. Exception messages, tracebacks and submitted values are never returned.
- In debug mode Starlette returns its own traceback page for unexpected errors instead of calling the handler. Debug mode is rejected in production (D-040), so this cannot happen there.

**Structured logging** (`app/core/logging.py`, `app/core/request_context.py`)

- Standard-library logging to standard output, as one JSON object per line (default) or readable text (`AEGIS_LOG_FORMAT=text`). Each record has timestamp (UTC), level, logger, service, message, optional event type and request ID (SYSTEM_ARCHITECTURE §13.1). Level is set by `AEGIS_LOG_LEVEL` (default INFO).
- Every request gets an ID. A client-supplied `X-Request-ID` is reused only if it is 8–64 characters from `[A-Za-z0-9._-]`; otherwise a new one is generated, so the header cannot be used to inject content into logs.
- Each request is logged once (`http.request`): method, path without query string, status and duration; INFO below 500, ERROR from 500. Query strings and bodies are never logged, because they can carry secrets.
- Uvicorn's own logs use the same handler. Its access log is disabled because it includes query strings. HTTP-client library loggers (httpx, httpcore and their successors) are raised to WARNING because they log full URLs.
- Safety net: structured fields whose names look sensitive (password, secret, token, authorization, cookie, session, API key, credential, private key) are written as `[REDACTED]`. Log messages themselves must never contain such values.

**Request validation** (`app/schemas/base.py`, `app/core/request_limits.py`)

- Request bodies extend `RequestModel`: unknown fields are rejected and surrounding whitespace is stripped.
- Validation errors return 422 `validation_error` with one entry per problem: location, message and type only. The submitted input and validation context are dropped, so values such as passwords are never echoed.
- Request bodies larger than `AEGIS_MAX_REQUEST_BODY_BYTES` (default 1 MiB) are rejected with 413 `request_too_large`, whether the size is declared in `Content-Length` or only found while streaming.

**API documentation** (`app/main.py`)

- Swagger UI at `/api/docs` and the OpenAPI schema at `/api/openapi.json`; ReDoc is not served. Disabled in production by default; enabled in development and test. `AEGIS_API_DOCS_ENABLED` overrides the default in either direction.
- The schema documents the `ErrorResponse` format for 422 and 500 on every version 1 operation, and states the Apache-2.0 licence. "Try it out" is off by default and authorization is not persisted.
- Open item: FastAPI's Swagger UI page loads its JavaScript and CSS from `cdn.jsdelivr.net` and its favicon from `fastapi.tiangolo.com`, so opening the docs page makes the viewer's browser contact those services. The docs are off in production by default. Serving these files from the deployment would need the `swagger-ui-dist` assets (Apache-2.0) and a decision.

**Deployment hardening: server header**

Uvicorn adds a `server: uvicorn` response header at the protocol level, outside the application, so the application cannot reliably remove it. Deployments must start Uvicorn with `--no-server-header` (verified: the header is then absent). This belongs to the deployment configuration in roadmap task 1.5; no deployment files are added in Phase 1.3.

## D-043 — Database foundation

Roadmap task 1.4, implemented as one bundle. No business models are created.

**Configuration (task: Configure PostgreSQL).** The connection is configured with individual `AEGIS_DATABASE_*` settings (host, port, name, user, password, SSL mode, connect timeout and pool sizes), not a single URL string:

- The password is a `SecretStr`: hidden in `repr`, logs and settings dumps. It has no default and is required in production.
- `app.database.config.build_database_url` builds the URL with SQLAlchemy's `URL.create`, which escapes every component (no string formatting). Printing the URL hides the password.
- `sslmode` defaults to `prefer`; `verify-full` is documented for databases on untrusted networks. Each connection sets `application_name=aegis-api` and `connect_timeout` (default 5 s).
- An unset `AEGIS_DATABASE_HOST` means no database is configured. The application still starts; database-backed requests return 503.

**SQLAlchemy 2.x with psycopg 3 (task: Integrate SQLAlchemy 2.x).** `psycopg[binary]` is used because it bundles libpq, so no PostgreSQL client installation is needed. SQLAlchemy 2.1 no longer needs `greenlet` for synchronous use.

Licence review of psycopg 3.3.9 (details in THIRD_PARTY_NOTICES.md, "psycopg Licence Review"):

- **Windows wheel: completed.** `psycopg-binary` 3.3.9 for CPython 3.11 on 64-bit Windows bundles libpq 18.4 (PostgreSQL License) and OpenSSL 3.6.5 (Apache-2.0), and nothing else. Using psycopg as an unmodified, separately installed dependency is acceptable for the Apache-2.0 project. The obligations listed there apply if AEGIS ever distributes these binaries itself.
- **Linux wheel: pending.** The Linux (manylinux) wheels used in containers are built separately and may bundle additional libraries. They must be reviewed in task 1.5, before container images are built or distributed.

**Connection management (task: Establish database connection management).**

- `app/database/engine.py`: one engine per application with a `QueuePool` (size 5, overflow 10, timeout 30 s, recycle 1800 s, all configurable), `pool_pre_ping` to replace connections broken by a database restart, `hide_parameters` so bound values never appear in errors or logs, and SQL logging (`echo`) off.
- `app/database/session.py`: a `Database` object, created by `create_app`, builds the engine lazily on first use, so importing or starting the application never opens a connection. The application lifespan disposes of the pool on shutdown. `get_db_session` gives each request one session whose transaction commits when the handler returns and rolls back if it raises. Sessions use `autoflush=False` and `expire_on_commit=False`.
- `app/database/errors.py`: connection failures, timeouts and pool exhaustion (`OperationalError`, `InterfaceError`, `TimeoutError`) return 503 `database_unavailable` in the standard error format. Hosts, users, SQL and driver messages are never returned, and only the exception type is logged.
- The engine-creation log entry records host, port, database name and SSL mode, never the user or password.

**ORM foundation.** `app/database/base.py` defines `Base` (SQLAlchemy 2.x `DeclarativeBase`, typed `Mapped[...]` mappings) with:

- a constraint naming convention (`pk_`, `uq_`, `ix_`, `fk_`, `ck_`), so migrations are deterministic;
- `datetime` columns mapped to `timestamptz` and `uuid.UUID` to PostgreSQL `uuid`;
- `UUIDPrimaryKeyMixin` (random version 4 UUIDs, not guessable or enumerable) and `TimestampMixin` (`created_at` and `updated_at`, set by the database).

`app/models/__init__.py` is the model registry imported by Alembic; it is empty until Phase 02.

**Alembic (tasks: Configure Alembic; Create initial migration structure).**

- `apps/backend/alembic.ini` contains no database URL. `migrations/env.py` builds the connection from the same settings as the application and compares against `Base.metadata`, with type and server-default comparison enabled. A NullPool engine is used for migration runs. Offline SQL generation (`--sql`) works without a connection.
- Migration files are named `YYYYMMDD_<revision>_<slug>.py` (UTC dates) and use a typed template.
- The initial migration (`ccf3950ff766`, "initial migration structure") is an empty baseline that later migrations build on.

## D-044 — Disposable PostgreSQL for database tests

Database tests must never touch a developer's or production database. `tests/postgres_harness.py` creates a temporary PostgreSQL cluster with the local `initdb` and `pg_ctl` binaries:

- In a temporary directory, listening only on 127.0.0.1 on a free port, with trust authentication and durability disabled for speed.
- Started once per test session and destroyed at the end. Each database test gets its own freshly created database, dropped afterwards.
- Binaries come from `AEGIS_TEST_POSTGRES_BIN`, `PATH`, or the standard Windows installation directory. If none are found, database tests are skipped with a reason; all other tests still run.
- Tools are run with fixed argument lists, never through a shell.

No test dependency was added (such as testcontainers or pytest-postgresql). Docker-based test databases and CI provisioning belong to tasks 1.5 and 1.6.

## D-045 — Backend test configuration, linting, formatting and type checking

Roadmap tasks 1.6.1, 1.6.3 and 1.6.4. All configuration is in `apps/backend/pyproject.toml`.

**Pytest.** `--strict-markers`, `--strict-config`, `xfail_strict` and `filterwarnings = ["error"]`, so unknown markers, configuration mistakes, unexpected passes and new warnings fail the run. Tests that use the disposable PostgreSQL server are marked `database` automatically by `conftest.py`, so `pytest -m "not database"` runs the fast tests only. Setting `AEGIS_TEST_REQUIRE_POSTGRES=1` makes a missing PostgreSQL installation fail the run instead of skipping the database tests (used in CI, D-048).

**Ruff** (MIT) lints and formats Python, replacing flake8, isort and black with one tool. Line length 100 (matching Prettier), Python 3.11 syntax. Rule groups: pycodestyle (`E`, `W`), Pyflakes (`F`), import sorting (`I`), bugbear (`B`), pyupgrade (`UP`), simplify (`SIM`), bandit security rules (`S`), comprehensions (`C4`), Ruff rules (`RUF`), pytest style (`PT`), timezone-aware datetimes (`DTZ`) and no `print` (`T20`). Tests may use `assert` and fixed placeholder passwords (`S101`, `S105`, `S106`). FastAPI's `Depends`, `Query`, `Path` and `Body` are declared immutable, because FastAPI evaluates them once by design.

**mypy** (MIT) runs in `strict` mode on `app`, `migrations` and `tests`.

Changes made to existing code while introducing these tools, none of which changes behaviour:

- The exception handlers in `app/core/errors.py` used `assert isinstance(...)` only to narrow the declared `Exception` parameter for the type checker. Assertions are removed under `python -O` and flagged by the security rules, so they were replaced with `typing.cast`. FastAPI calls each handler only for the exception type it is registered for.
- `Base.type_annotation_map` keeps a single, commented `# noqa: RUF012`: SQLAlchemy reads this class attribute by name and it is never mutated.
- Two `subprocess.run` calls in the test harness carry `# noqa: S603`; they run fixed argument lists, never a shell (D-044).
- Ruff formatting was applied once to the existing code. Composite test assertions were split, so failures identify the exact condition.

pathspec, a dependency of mypy, is licensed under MPL-2.0 (file-level copyleft). It is a development tool that AEGIS does not modify or distribute, so this is acceptable.

## D-046 — Backend dependency lock file

Resolves the open lock-file question in D-040.

- `apps/backend/requirements-dev.lock` pins every runtime and development dependency to an exact version with SHA-256 hashes for all published files. It is generated by **pip-tools** 7.7 (BSD-3-Clause) from the ranges in `pyproject.toml`, which remain the source of truth. pip-tools is declared in the separate `lock` extra and is not part of the lock itself. uv was not used, consistent with D-007.
- Install with `pip install --require-hashes -r requirements-dev.lock`, then `pip install --no-deps -e .`. Hash checking rejects any file that differs from the recorded one.
- The lock is generated on Windows with Python 3.11. pip-tools drops platform markers, so the Windows-only dependencies `colorama` and `tzdata` are installed on every platform. Both are small pure-Python packages, so this is harmless; the reverse (a lock generated on Linux) would miss them on Windows.
- Verified on 2026-11-16: hash-checked installs on Windows (fresh virtual environment) and Linux (Debian bookworm container, Python 3.11.18) both produce exactly the locked set, `pip check` passes, and regenerating the lock produces an identical file.
- Not covered: the build backend (setuptools) used by the editable install is fetched by pip's build isolation and is not hash-pinned.

## D-047 — Frontend testing with Vitest; Node.js 22.22.2 or later

Roadmap task 1.6.2. Supersedes D-024 and resolves D-026.

**Tools** (all MIT): Vitest 5.1, jsdom 31, React Testing Library 16 (`@testing-library/react` with `@testing-library/dom`), `@testing-library/user-event` 14 and `@testing-library/jest-dom` 7.

- Vitest reuses `vite.config.ts` (imported from `vitest/config`), so tests use the same React and Tailwind plugins as the application. Tests live next to the code as `src/**/*.test.ts(x)`; shared setup is in `src/test/setup.ts`. Mocks and stubbed globals are restored after every test.
- `tsconfig.test.json` type-checks the tests as part of `npm run typecheck` and `npm run build`. The jest-dom matcher types are available only there, not in application code (`tsconfig.app.json` excludes tests).
- Oxlint, with type-aware rules, lints the tests like application code (D-033).
- jsdom does not implement scrolling, so `window.scrollTo` (called by React Router's `ScrollRestoration`) is stubbed in the test setup only.
- Tests use real components and the real route configuration with a memory router; no mock data.

**TypeScript 7 (D-026).** Verified with Vitest, React Testing Library and jest-dom: tests run, `tsc` type-checks the test files (including matcher argument types) and type-aware linting covers them. No downgrade to TypeScript 5 is needed, so D-026 is no longer conditional.

**Node.js.** jsdom 30 and later require Node.js 22.22.2 or later. The minimum in `apps/frontend/package.json` is therefore raised from 22.22.0 to **22.22.2**. The development and CI baseline is **22.23.5**, the current Node.js 22 LTS release (a security release), recorded in `apps/frontend/.nvmrc`. jsdom 29, which still supports Node.js 22.22.0, was rejected because it is a superseded major version.

## D-048 — Continuous integration workflow and import-boundary contracts

Roadmap task 1.6.5 and the import-linter task of 1.6. Implements D-010 and D-015.

**Workflows.**

- `.github/workflows/ci.yml` runs on every pull request, on pushes to `main` and manually. It has two jobs on `ubuntu-24.04`:
  - **Backend** (Python 3.11): hash-checked install from `requirements-dev.lock`, `pip check`, `ruff check`, `ruff format --check`, `mypy`, `lint-imports` and `pytest`.
  - **Frontend** (Node.js from `.nvmrc`): `npm ci`, typecheck, lint, format check, tests and production build.
- `.github/workflows/pr-title.yml` checks pull request titles against Conventional Commits (D-049).

**Security.**

- The token is read-only (`contents: read`) and no secrets are used.
- The workflows use `pull_request`, never `pull_request_target`, so code from forks gets no write access or secrets.
- Actions are pinned to full commit hashes with the release tag in a comment (`actions/checkout` 7.0.1, `actions/setup-python` 7.1.0, `actions/setup-node` 7.1.0). Checkout does not keep credentials.
- The pull request title is untrusted. It reaches the shell only through an environment variable and is only compared with a regular expression, never executed or echoed into workflow commands.
- Every job has a timeout. A new push cancels superseded runs of the same pull request or branch.

**PostgreSQL in CI.** CI installs the PostgreSQL 18 server binaries from the PostgreSQL project's signed apt repository, without creating a cluster or service, and the existing test harness (D-044) creates its disposable cluster on 127.0.0.1 inside the runner. Local and CI database tests use the same code path, and no option exists to point the tests at an existing server. `AEGIS_TEST_REQUIRE_POSTGRES=1` makes CI fail if the database tests cannot run (D-045). A GitHub Actions service container was rejected because the harness would have needed a way to connect to an external server, which could be pointed at a real database.

**Import-boundary contracts.** An import-linter (BSD-2-Clause) "forbidden" contract in `pyproject.toml` implements SYSTEM_ARCHITECTURE §4.5: `app.workers.assessment`, `app.netguard`, `app.contracts` and `app.modules.*.engine` must not import `app.database`, `app.models`, `app.services`, `app.api`, `sqlalchemy`, `psycopg` or `alembic`, directly or indirectly.

- import-linter refuses to run a contract that names a missing internal package, so `app.workers` (with `app.workers.assessment`), `app.netguard`, `app.contracts` and `app.services` were created as **empty packages containing only a docstring** that states their boundary. They contain no functionality; the roadmap tasks that need them fill them in. This amends D-040's rule of creating packages only when needed, for these packages only.
- `app.modules.*.engine` matches nothing yet and starts being checked automatically when the first engine package is created.
- Verified on 2026-11-16: the contract passes on the current code, and fails on deliberate violations, both direct (`app.workers.assessment` importing `sqlalchemy`) and indirect (`app.netguard` importing `app.main`, which imports `app.database` and `sqlalchemy`).

## D-049 — Pull request conventions and recommended repository settings

Roadmap task 1.6.6.

- `.github/pull_request_template.md` asks for the summary, affected modules, decisions, security implications, tests run, known limitations and a checklist (CONTRIBUTING §6).
- Issue forms for bug reports and feature requests. Blank issues are disabled, and the issue chooser directs security vulnerabilities to private vulnerability reporting.
- Pull request titles must follow Conventional Commits (CONTRIBUTING §5), checked by CI: a known type, an optional lowercase scope, an optional `!`, a summary that does not start with a capital letter or end with a period, and at most 72 characters. Squash merging makes the title the commit message on `main`.
- No commit-message hooks (commitlint, husky, pre-commit) are added; the CI title check covers the merged history without extra tooling.

**Recommended repository settings**, applied manually by a maintainer (not automated):

- Merging: allow squash merging only, using the pull request title as the commit message; delete head branches after merge.
- Branch protection (or a ruleset) on `main`: require a pull request; require the status checks "Backend (Python 3.11)", "Frontend (Node.js)" and "Conventional Commits title" to pass, with branches up to date; block force pushes and deletion.
- Actions: allow only actions pinned to a full commit hash; set the default workflow token permission to read-only; require approval for workflow runs from first-time contributors.
- Security: enable private vulnerability reporting, Dependabot alerts and secret scanning with push protection.

## D-050 — Phase 1.5 scope and Docker Compose layout

Roadmap Phase 1.5 is implemented as written in the roadmap and SYSTEM_ARCHITECTURE §6 and §12: Valkey (not Redis) as the Celery broker with ACL users per role, a Celery application skeleton with the two worker roles (D-020), the five Docker networks of §12.2, environment variables, health checks and service dependencies. No assessment tasks, authentication or scanning functionality are implemented.

- `docker-compose.yml` is the secure, production-like base. `docker-compose.dev.yml` is the development override: development settings, the API also published on `127.0.0.1:8000` with live reload of the mounted source (read-only), and automatic migrations. All security settings of the base file stay in force with the override.
- The Compose project is named `aegis`, so Docker Desktop groups the containers as `aegis` (`aegis-backend-1` and so on). Compose requires lowercase project names.
- Docker Compose is not an outbound security boundary (§12.2). Containers on the non-internal `edge` and `egress` networks can reach the internet, the local network and the host.

## D-051 — Container images

- **Backend** (`infrastructure/docker/backend.Dockerfile`): one image for the API, the migration job and both worker roles (§6.1). Multi-stage build on `python:3.11.18-slim-trixie`. Runtime dependencies are installed from `apps/backend/requirements.lock` (runtime only, generated by pip-tools like the development lock, D-046) with `--require-hashes --only-binary=:all:`, so no package can run build code. pip, setuptools and wheel are then removed from the image: nothing is installed at runtime, and this also removes the setuptools advisory found in Phase 1.6. The code is owned by root and read-only for the `aegis` user (UID 10001). No compilers, network tools such as curl, or extra system packages are installed. Image size: 324 MB.
- **Frontend** (`infrastructure/docker/frontend.Dockerfile`): built with `node:22.23.5-trixie-slim` (`npm ci --ignore-scripts`, then `npm run build`), served by `nginxinc/nginx-unprivileged:1.30.6-alpine` (UID 101). The nginx configuration is part of the image. Image size: 91 MB.
- Every base image (including PostgreSQL and Valkey in Compose) is pinned by its multi-architecture index digest, with the tag in a comment.
- Builds use the repository root as context with an allowlist ignore file per Dockerfile (`*.Dockerfile.dockerignore`): everything is excluded except the files each image needs, so `.env` files, `secrets/`, virtual environments and caches can never enter an image.
- Uvicorn runs with `--no-server-header` (resolves the D-042 deployment item; verified: no `server` header), `--no-access-log` and `--timeout-graceful-shutdown 20`. `--proxy-headers` trusts forwarding headers only from the frontend container's fixed address (`--forwarded-allow-ips=<prefix>.0.10`; Uvicorn 0.54 accepts single addresses and networks, verified in its source). nginx replaces, never appends to, `X-Forwarded-For`.
- Uvicorn re-raises the SIGTERM it received after a graceful shutdown, so a cleanly stopped API container reports exit code 143. The smoke test accepts 143 only together with Uvicorn's "Finished server process" log line.
- Images are built locally only (D-059).

## D-052 — Services, networks, frontend proxy and startup order

| Service | Networks | Published |
|---|---|---|
| frontend | edge (fixed address `<prefix>.0.10`) | `127.0.0.1:8080` |
| backend | edge, data, queue, ingest | development override only: `127.0.0.1:8000` |
| migrate (one-shot) | data | — |
| worker-internal | data, queue | — |
| worker-assessment | queue, ingest, egress | — |
| postgres | data | — |
| valkey | queue | — |

- Networks follow §12.2: `data`, `queue` and `ingest` are internal (no outbound access); `edge` and `egress` are not. Subnets are explicit (`AEGIS_SUBNET_PREFIX`, default `10.213`, one /24 per network) so they can be added to the netguard denylist. The `ingest` listener itself is Phase 03+ work; the network exists, nothing listens on it yet.
- **Frontend server:** nginx serves the built application and proxies `/api/` to the backend, so the browser uses one origin (no CORS; Phase 02 cookie sessions and CSRF protection rely on this). It sends a strict Content Security Policy (`default-src 'self'`, no inline scripts or styles; the build contains none), `X-Frame-Options: DENY`, `X-Content-Type-Options`, `Referrer-Policy: no-referrer` and `Permissions-Policy`. `server_tokens off` hides the nginx version; the `Server: nginx` header itself remains, because removing it needs a third-party module. The backend's address is resolved through Docker's DNS at request time. In development, Vite proxies `/api` to `127.0.0.1:8000` (`AEGIS_DEV_API_URL`).
- **Startup order** uses health conditions, not start order: postgres (healthy: `pg_isready` over TCP, which only the final server answers) → migrate (development: completed successfully) → backend (healthy: readiness) → frontend (healthy: the `/api/` proxy answers). Valkey (healthy: PING as the PING-only `healthcheck` ACL user) gates the backend and both workers. The worker-assessment depends only on Valkey.
- The application does not rely on the order either: the database engine and broker client are created lazily and reconnect, readiness reports the current state, and Celery retries the broker connection indefinitely.
- `init: true` (tini) is PID 1 for the backend, workers, migration job and frontend; PostgreSQL and Valkey use their images' own process handling. Stop grace periods: 30 s for the API and databases, 6 minutes for workers (longer than the 360 s hard task limit). Restart policy `unless-stopped`; the migration job never restarts.
- **Container hardening** for every service, including PostgreSQL and Valkey: non-root user, read-only root filesystem with tmpfs mounts, all capabilities dropped (none added: PostgreSQL and Valkey start directly as their own users, so their entrypoints need no capability), `no-new-privileges`, not privileged, CPU, memory and process limits, no Docker socket. Verified on the running containers (D-058).

## D-053 — Secrets and environment variables

- **Secrets are files, never environment variables or image content.** `python infrastructure/scripts/init_dev_secrets.py` (Python standard library only) creates random passwords and the Valkey ACL file in `secrets/` (gitignored). It never overwrites a file: running it again creates only what is missing. If the ACL file no longer matches the password files or the current ACL rules, it stops with instructions instead of rewriting it. Secret values are never printed. The directory is 0700; the files are 0644 because Compose bind-mounts them into containers running as other users.
- Compose passes each container only the secrets it needs, under `/run/secrets`, renamed to the setting they supply (`aegis_database_password`, `aegis_valkey_password`). The backend reads them through pydantic-settings' secret-file support, enabled only when `AEGIS_SECRETS_DIR` is set; environment variables take precedence. The assessment worker receives only its Valkey password.
- Non-secret settings are set per service in `docker-compose.yml`. Compose-level options (ports, subnet prefix, secrets directory, log level, worker concurrency) are documented in the root `.env.example`; the backend's own variables, for running it outside Docker, in `apps/backend/.env.example`. Containers never read a `.env` file, so Docker and local defaults cannot conflict.
- New backend settings: `AEGIS_VALKEY_HOST`, `_PORT`, `_DB`, `_USERNAME`, `_PASSWORD`, `_TLS`, `_CONNECT_TIMEOUT`, `_SOCKET_TIMEOUT`, `AEGIS_HEALTH_CHECK_TIMEOUT`, `AEGIS_WORKER_TASK_SOFT_TIME_LIMIT`, `AEGIS_WORKER_TASK_TIME_LIMIT`, `AEGIS_WORKER_HEARTBEAT_FILE` and `AEGIS_SECRETS_DIR`. In production, a configured Valkey host requires a username and password. Defaults remain secure (production environment, debug and documentation off).

## D-054 — PostgreSQL roles

Created once, when the data directory is first initialized, by `infrastructure/docker/postgres/initdb/10-aegis-roles.sh` (the postgres image's initialization mechanism). It never runs against an existing database and never drops anything.

- `aegis_owner` owns the `aegis` database and the `public` schema. Only the migration job uses it.
- `aegis_app` is used by the API and the internal worker. Default privileges give it `SELECT`, `INSERT`, `UPDATE` and `DELETE` on tables and `USAGE`, `SELECT` on sequences created by the owner: data access only.
- Neither role is a superuser or can create databases, roles or replication connections. `PUBLIC` has no access to the `aegis` database or the `public` schema, and cannot connect to the `postgres` database.
- The superuser (`postgres`) is refused over the network (`pg_hba.conf` reject rule); it can connect only through the local socket inside the container.
- Verified by the smoke test: the runtime role can read data but is refused `CREATE TABLE`, `DROP TABLE`, `ALTER TABLE`, `TRUNCATE` and `CREATE SCHEMA`; the owner can change the schema; the superuser cannot connect over TCP.
- Limitation: default privileges also give `aegis_app` data access to `alembic_version`.
- **Migrations** run only `alembic upgrade head`, as `aegis_owner`: automatically in development (`migrate` service before the API), explicitly in production (`docker compose --profile migrate run --rm migrate`). Nothing ever downgrades, stamps or drops.

## D-055 — Valkey and the Celery application skeleton

**Client.** kombu has no Valkey-specific transport, so Celery uses its Redis transport (`redis://`, `rediss://`) with the `redis` client library (MIT; the client is not affected by the Redis server's licence change), which also serves the readiness check. Valkey 9.1.3.

**Celery 5.7.0** (`app/workers/celery_app.py`), one factory for the API (sender) and both roles:

- JSON serialization only; pickle can never be accepted. No result backend (§2.4; results use the ingestion listener).
- Each role has its own exchange and queue namespace (`internal.*`, `assessment.*`). Task names select the queue (`aegis.internal.*`, `aegis.assessment.*`); a task matching neither cannot be sent, because the default queue is never declared and missing queues are never created.
- Remote control, events, mingle, gossip and heartbeat are disabled: they use Pub/Sub and shared keys, which the ACL users cannot access. Messages being processed are tracked under per-role keys (`<role>.unacked*`).
- Prefetch 1, soft and hard task time limits (`AEGIS_WORKER_TASK_SOFT_TIME_LIMIT`, `AEGIS_WORKER_TASK_TIME_LIMIT`, defaults 300 and 360 s), 100 tasks per child process, and the broker connection is retried indefinitely at startup and after outages.
- Workers log through the AEGIS logging configuration with their own service names (`aegis-worker-internal`, `aegis-worker-assessment`). Celery masks the broker password in its output (verified).
- No tasks exist yet. Worker availability (§12.4): remote control is disabled, so each worker's consumer touches a heartbeat file on its tmpfs while connected, and the container health check (`python -m app.workers.healthcheck`) fails when it is older than 30 s.

**ACL users** (generated into the ACL file, passwords stored as SHA-256 hashes):

| User | Commands | Keys |
|---|---|---|
| `default` | disabled | — |
| `healthcheck` | `PING` only, no password | none |
| `aegis-api` | connect, `LPUSH`, `SADD`, `SMEMBERS`, `LLEN`, `MULTI`, `EXEC` | `internal.*`, `assessment.*` and their kombu binding keys |
| `worker-internal` | connect, consumer commands (`BRPOP`, list, set, sorted-set, hash and string commands, transactions, `EVALSHA` and `SCRIPT LOAD` for kombu's mutex) | `internal.*` and its binding keys only |
| `worker-assessment` | as `worker-internal` | `assessment.*` and its binding keys only |

No user has Pub/Sub channels or administrative commands. A Lua script runs with the calling user's ACL, so `EVALSHA` gives no access beyond the user's own commands and keys. Server-wide, `DEBUG` and `MODULE` are disabled and memory is never evicted (`maxmemory-policy noeviction`); queued jobs survive restarts (append-only file on the `valkey-data` volume). Verified twice: in the planning probe, and by the smoke test against the real configuration (each role is refused the other role's queue, unacknowledged messages and bindings, and `KEYS`, `FLUSHALL`, `FLUSHDB`, `CONFIG`, `DEBUG`, `MODULE`, `ACL`, `PUBLISH` and `SHUTDOWN`; the API user cannot consume; unauthenticated clients are refused; tasks reach only their own role's worker). Known limitation (unchanged from D-011): assessment workers sharing a queue can read each other's payloads.

## D-056 — Swagger UI served from local assets

Resolves the D-042 open item. Swagger UI 5.35.0 (`swagger-ui-dist`, Apache-2.0) is vendored in `apps/backend/app/static/swagger-ui/`: `swagger-ui-bundle.js`, `swagger-ui.css`, `favicon-32x32.png`, with the package's `LICENSE`, `NOTICE` and `swagger-ui-bundle.js.LICENSE.txt` (licences of the bundled components: MIT, and DOMPurify under Apache-2.0 or MPL-2.0). `PROVENANCE.txt` records the npm tarball's sha512 (verified against the registry) and each file's SHA-256; a test checks the hashes, and `.gitattributes` keeps the files byte-for-byte.

- The files are copied from the verified tarball and never installed with npm, because the package depends on `@scarf/scarf`, an install-time analytics package (PRD §4.6).
- The documentation page (`/api/docs`, assets under `/api/docs/assets/`) is served only when documentation is enabled (development and test by default). It references only these local files, and Swagger UI's validator is disabled (`validatorUrl: null`), so opening it contacts no third party.

## D-057 — Health checks

- `GET /api/v1/health/live`: liveness. Checks no dependency, so a database or broker outage never makes an orchestrator restart a working API process. `200 {"status": "ok"}`.
- `GET /api/v1/health/ready`: readiness. PostgreSQL (`Database.ping()`) and Valkey (`Broker.ping()`) must both be reachable. `200 {"status": "ready", "checks": {"database": "ok", "broker": "ok"}}`, otherwise `503` in the standard error format, code `service_not_ready`, with one detail per unavailable dependency.
- Each probe runs in a worker thread with a time limit (`AEGIS_HEALTH_CHECK_TIMEOUT`, default 2 s); a probe that does not finish is abandoned and reported unavailable. Concurrent requests share one evaluation, reused for 1 s, so frequent probes cannot open many connections or occupy many threads while a dependency is down. Both probes use pooled connections (the engine's pool; the broker client keeps up to four connections).
- Responses name dependencies only and are never cached (`Cache-Control: no-store`). Failures are logged with the exception type only.
- Container health checks: backend `python -m app.healthcheck ready`; workers `python -m app.workers.healthcheck` (heartbeat, D-055); postgres `pg_isready`; valkey `PING`; frontend fetches `/api/v1/health/live` through its own proxy. None uses a shell.

## D-058 — Container smoke test in CI

`infrastructure/scripts/smoke_test.py` (Python standard library and the Docker CLI) starts the production-like stack as the separate Compose project `aegis-smoke`, with temporary secrets, its own subnets (`10.214`), host port (`18080`) and volumes. It runs the migration explicitly and checks more than 100 conditions: health of every service, the frontend and its API proxy, security headers, health endpoints, no Uvicorn server header, forwarding-header trust, migrations at head, PostgreSQL role permissions, worker isolation (DNS, TCP and credentials), Valkey ACLs, task routing, network membership, published ports, container security settings on the running containers, secrets absent from images, and graceful shutdown. It removes only the `aegis-smoke` containers, networks and volumes afterwards; it refuses to run under the name `aegis`.

The CI workflow runs it in a third job, "Containers (build and smoke test)", on every pull request and push to `main`. Images are never pushed or uploaded. This job should be added to the required status checks (D-049).

## D-059 — Linux psycopg wheel review; container images are not distributed

Completes the review left open by D-043. The backend image installs `psycopg-binary` 3.3.9 from the manylinux wheels pinned in the lock file (`manylinux2014_x86_64` and `manylinux_2_28_aarch64`, matched by SHA-256). Unlike the Windows wheel (libpq and OpenSSL only), the Linux wheels bundle Kerberos/GSSAPI, LDAP, SASL, keyutils and libcrypt as well. Versions were read from the binaries and from psycopg's build script at tag 3.3.9; licence texts were read from each project's source at the matching release (details and SHA-256 hashes in THIRD_PARTY_NOTICES.md, "psycopg Licence Review").

- LGPL components: psycopg (LGPL-3.0-only), keyutils (LGPL-2.0-or-later per its source; distributed with the LGPL-2.1 text) and libcrypt (glibc on x86_64, libxcrypt on aarch64; LGPL-2.1-or-later).
- Cyrus SASL's licence requires the acknowledgement "This product includes software developed by Computing Services at Carnegie Mellon University (http://www.cmu.edu/computing/)" in any redistribution.
- The wheel contains only psycopg's own licence text.

**Decision:** building and running images locally is not distribution and is allowed. **No image may be published, pushed or otherwise distributed** until a separate distribution-compliance review has added the required licence texts and notices to the images and arranged source availability for the LGPL components (and for the GPL and other packages of the Debian base image). Distribution compliance has not been achieved.

## D-060 — Phase 1.5 review corrections

Five corrections from the Phase 1.5 review. The infrastructure design is unchanged.

**1. Linux psycopg licensing reconciled (amends D-059).** Verified against the exact wheels in the lock file, their binaries and the matching upstream sources:

- keyutils: x86_64 bundles keyutils **1.5.8** (`libkeyutils.so.1.5`); aarch64 bundles keyutils **1.5.10** (package `keyutils-libs-1.5.10-9.el8`, `libkeyutils.so.1.6`). The `.so.1.6` suffix is the library API version: 1.5.10 adds the `KEYUTILS_1.6` symbol-version block, and the binaries define exactly these blocks. The earlier note "1.6" was the API version, not the package version.
- keyutils licence: the library sources (`keyutils.c`, `keyutils.h`) state "GNU Lesser General Public License … version 2 … or (at your option) any later version", upstream ships the LGPL-2.1 text, and RHEL/CentOS 8 declares `LGPLv2+`. Recorded as `LGPL-2.0-or-later` as written (Fedora's SPDX conversion uses `LGPL-2.1-or-later`); obligations are met under the LGPL-2.1 terms either way. The earlier `LGPL-2.1-or-later` was an unverified planning assumption.
- Exact aarch64 package releases (from debug-link names): `cyrus-sasl-lib-2.1.27-6.el8_5`, `keyutils-libs-1.5.10-9.el8`, `libxcrypt-4.1.1-6.el8`, `libcom_err-1.45.6-7.el8_10`. x86_64 package releases (CentOS 7) are not embedded; the upstream versions are.
- Attribution (Cyrus SASL clause 4) and source-availability obligations are unchanged and listed in THIRD_PARTY_NOTICES.md. **Distribution compliance is not achieved**: local image builds remain permitted; publishing or distributing images remains prohibited until the separate compliance review.

**2. Runtime database role has no access to migration metadata (amends D-054).** The application never uses `alembic_version`, but default privileges gave `aegis_app` row access to it. After every migration run, `migrations/env.py` revokes all privileges on the version table from every role except its owner, including `PUBLIC`, in the same transaction. The statement is idempotent, changes no data and no other grants, is included in offline SQL (`--sql`), and corrects existing databases on their next `alembic upgrade head`. Tests (against the disposable PostgreSQL cluster, with roles set up as in the deployment) prove that the runtime role cannot select, insert, update, delete, truncate or drop the version table, that the owner can still migrate and create tables, and that the runtime role keeps data access, but not schema access, to tables created by the owner. The container smoke test checks the same against the real roles.

**3. The Valkey health-check account is authenticated (amends D-055 and D-057).** The `healthcheck` ACL user has its own generated password (`secrets/valkey_healthcheck_password`, mounted only into the valkey container) and may still run only `PING`, with no keys and no channels. The container health check sends `AUTH` and `PING` to `valkey-cli` on standard input, with the password read from the secret file by the shell's `printf` builtin, so it never appears in a command line, an environment variable or the output (`OK`, `PONG`). This is the only health check that uses a shell, inside the Valkey image; valkey-cli has no option to read a password from a file. Verified: an unauthenticated `PING` and a wrong password are refused; the authenticated user can `PING` but is refused application queues, keys, `CONFIG`, `FLUSHALL`, `ACL` and `PUBLISH`; the password is not in the container's environment, command or health log.

Existing development secrets are not overwritten: `init_dev_secrets.py` adds the new password file and reports the ACL file as out of date. Delete `secrets/valkey_users.acl` (it contains only password hashes and is derived from the password files), run the script again, and recreate the valkey container.

**4. Assessment worker payload visibility is recorded as a security risk.** `docs/security/SECURITY_RISKS.md` is the security risk register. Entry SR-001 records that assessment workers sharing a queue can read each other's task payloads, including other jobs' ingestion tokens, with the current mitigations, the residual risk and future remediation options (per-worker credentials and queues, out-of-band ingestion tokens, per-worker encryption, one container per job, detection). D-011 remains accurate. AEGIS does not provide per-worker task isolation; the Celery architecture is unchanged.

**5. Routine health probes are not access-logged (amends D-057).** The health endpoints mark their normal results (200 and 503) as routine probes, and the request middleware logs marked requests at DEBUG instead of INFO. Requests that fail with an unexpected error are never marked and keep their ERROR level; other requests to the health paths (for example 404 or 405) keep normal logging. nginx does not write `GET`/`HEAD` probes answered with 200 or 503 to its access log. Preserved: dependency failures (`health.check_failed`, `health.check_timeout`, WARNING) and readiness transitions, logged once each (`health.not_ready` at WARNING with the unavailable dependencies, `health.ready` at INFO). Tests cover quiet probes, preserved failures and transitions, and unexpected errors in health endpoints.

## D-061 — Phase 2.1 authentication scope, administration and CLI

Roadmap task 2.1 implements all ten authentication requirements: registration, sign-in, secure sessions, sign-out, session expiration, session revocation, Argon2id password hashing, password reset, sign-in rate limiting, CSRF protection and HTTP-only session cookies. Browser authentication uses server-side sessions only: no JWT, no external identity provider, no hosted authentication service.

- **Accounts.** Email address (unique, normalized) and username (unique, 3 to 32 of `a-z 0-9 . _ -`, stored in lower case) are both required. An instance-administrator flag (D-018) and an active flag exist; workspace roles are roadmap 2.3.
- **Open registration** is off by default (D-018). The setting is stored in a single-row `instance_settings` table, created disabled by the migration. Successful registration signs the user in.
- **Instance administration** needed by authentication only: the CLI, plus `PUT /api/v1/admin/settings/registration` and `POST /api/v1/admin/password-resets`, and a matching section in Settings → Security that only instance administrators see. Every administration endpoint checks the flag on the server. User management (listing, deactivating, changing roles) is roadmap 2.2.
- **CLI** (`python -m app.cli`, in Compose `docker compose exec backend python -m app.cli …`): `create-admin` (the first account of an instance; no default credentials exist), `create-user`, `reset-password`, `registration show|enable|disable`, `purge-expired`. Passwords are never command-line arguments: they are read with a hidden prompt, entered twice, or from standard input with `--password-stdin`. Logs go to standard error, results to standard output; nothing secret is printed.
- New dependencies: argon2-cffi and argon2-cffi-bindings (D-062). Email addresses are validated in-house without DNS (D-063); no email library is added.

**Affects:** PRD FR-AUTH-001 to FR-AUTH-006; SYSTEM_ARCHITECTURE §9.

## D-062 — Argon2id password hashing

- argon2-cffi **25.1.0** with argon2-cffi-bindings **26.1.0**, pinned with hashes in both lock files. The bindings version is pinned exactly in `pyproject.toml` so the lock cannot move to an unreviewed release.
- Reviewed before adoption: PyPI hashes of every wheel and the sdist match the lock files; Linux wheels are `cp310-abi3` for `manylinux_2_26`/`manylinux_2_28` on x86_64 and aarch64 (plus `win_amd64`), so the container images (Debian, glibc) install a binary wheel without a compiler. The bindings statically link libargon2 from the phc-winner-argon2 reference implementation (commit `f57e61e`), licensed **CC0-1.0 OR Apache-2.0**; the wheel ships only the bindings' MIT licence, so the libargon2 licence is recorded in THIRD_PARTY_NOTICES.md. Further runtime dependencies: cffi 2.1.1 (MIT-0) and pycparser 3.12 (BSD-3-Clause). No known vulnerabilities (pip-audit).
- Parameters: the RFC 9106 low-memory profile (Argon2id, 64 MiB, 3 iterations, 4 lanes, 16-byte salt, 32-byte hash); about 65 ms per verification on the development machine. Hashes with other parameters are upgraded at the next successful sign-in.
- At most `AEGIS_PASSWORD_HASH_CONCURRENCY` (default 4) hashes run at once in a process, so concurrent sign-ins cannot exhaust the API container's 512 MiB memory limit.
- Sign-in for an unknown email address verifies the password against a dummy hash, so it takes as long as a real failure.

**Affects:** SYSTEM_ARCHITECTURE §9; THIRD_PARTY_NOTICES.md.

## D-063 — Identifiers and password policy

- Email addresses: trimmed, at most 254 characters, one `@`, a conservative local part, a domain with at least two labels converted to IDNA and the whole address lower-cased. No DNS lookups and no deliverability checks (AEGIS sends no email in v0.1.0).
- Passwords follow NIST SP 800-63B: 12 to 128 characters, no composition rules, spaces allowed and kept as typed. Passwords containing the username or the email address's local part are rejected. A common-password list is deferred (SR-006).
- Error messages for duplicates do not say whether the email address or the username is taken.

**Affects:** SYSTEM_ARCHITECTURE §9.

## D-064 — Server-side sessions

- A session token is 256 random bits (`secrets.token_urlsafe(32)`). Only its SHA-256 hash is stored (`user_sessions.token_hash`), with the user, creation time, last activity, absolute expiry, revocation time and reason, client address and a truncated user agent.
- Cookie `__Host-aegis_session`: `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/`, no `Domain`, no `Max-Age` (it ends with the browser session; the server enforces the real expiry). No endpoint returns the token in a body.
- **Expiry:** 60 minutes of inactivity (`AEGIS_SESSION_IDLE_TIMEOUT_MINUTES`) and 12 hours in any case (`AEGIS_SESSION_ABSOLUTE_TIMEOUT_HOURS`). Activity is recorded at most once a minute. Expired sessions answer 401 `session_expired`; missing, unknown or revoked ones 401 `authentication_required`.
- **Revocation:** sign-out revokes the session on the server; signing in again replaces the browser's previous session; a password reset (administrator link or CLI) revokes every session of the account; a deactivated account's sessions stop working at once. Ended sessions are deleted 7 days after they end (at sign-in, and by `purge-expired`).
- `AEGIS_COOKIE_SECURE` (default true, required in production) controls the `Secure` attribute and the `__Host-` prefix. Browsers accept `Secure` cookies from `http://localhost` and `http://127.0.0.1`, so the local stack keeps production cookie settings; this was verified in Chromium against the development stack (verified on 2026-11-17 in Chromium 158, on both loopback addresses and on the disposable smoke stack: sign-in, reload, sign-out).

**Affects:** SYSTEM_ARCHITECTURE §9.

## D-065 — CSRF protection

Deny-by-default ASGI middleware checks every `POST`, `PUT`, `PATCH` and `DELETE` under `/api/` (new endpoints are covered automatically) and refuses failures with 403 `csrf_failed`:

1. **Origin.** If present, `Origin` must be the request's own origin or one of `AEGIS_ALLOWED_ORIGINS`; `Origin: null` and `Sec-Fetch-Site: cross-site` are refused.
2. **Signed double submit.** The `X-CSRF-Token` header must equal the `__Host-aegis_csrf` cookie (same attributes as the session cookie). The frontend keeps the token in memory only; it comes from `GET /api/v1/auth/csrf` or from the sign-in response.
3. **Binding.** The token is `v1.<issued-at>.<nonce>.<HMAC-SHA-256(secret, "v1.<issued-at>.<nonce>|<binding>")>`. Before sign-in the binding is `anonymous`; after sign-in it is `session:<SHA-256 of the session cookie>`. A token is valid only with the binding of the request it arrives with, so a token from one session fails with another, and an anonymous token fails once a session exists.
4. **Age.** Tokens older than the absolute session lifetime are refused.

**Rotation:** sign-in and registration return a new session-bound token (and set its cookie); sign-out and password reset clear the CSRF cookie, and the client fetches a new anonymous token. Sign-in itself requires a valid anonymous token, which prevents login CSRF. `SameSite=Strict` is an additional layer, not the only one.

The server secret `AEGIS_SECRET_KEY` (at least 32 characters) signs the tokens and names the rate-limit counters (D-066). In Compose it is the secret file `secrets/aegis_secret_key`, created by `init_dev_secrets.py` and mounted only into the API container. It is required in production; elsewhere a temporary key is generated at start-up with a warning. Settings validation errors no longer quote their input, so a misconfigured secret never appears in an error message.

Because nginx forwards the `Host` header without the port, Compose sets `AEGIS_ALLOWED_ORIGINS` to `http://127.0.0.1:<AEGIS_HTTP_PORT>,http://localhost:<AEGIS_HTTP_PORT>` by default; deployments reached under another address set it explicitly.

**Affects:** SYSTEM_ARCHITECTURE §9, §12.

## D-066 — Distributed sign-in rate limiting

Counters live in Valkey, shared by every API process. Their names are `ratelimit:<kind>:<HMAC(secret, value)>`, so email addresses and client addresses never appear in Valkey. Every limit fails closed: if Valkey cannot be reached, sign-in, registration and password reset answer 503 `service_unavailable` (logged as `auth.rate_limiter_unavailable`) rather than run without limits. Throttled requests answer 429 `too_many_requests` with `Retry-After`, identically for existing and unknown accounts.

Limits (all configurable; window `AEGIS_RATE_LIMIT_WINDOW_SECONDS` = 15 minutes):

| Scope | Limit |
|---|---|
| Per client address | 30 failed sign-ins per window, then refused until the window ends |
| Per account and client address | 5 free failures; each further failure blocks that pair for 30, 60, 120, 240, 480 s, capped at the window |
| Per account, any address | after 20 failures in a window, at most one attempt per 10 s |
| Registration | 5 attempts per client address per hour |
| Password reset (token redemption) | 10 attempts per client address per window |

**Account denial of service (corrected by D-070).** The design above first let distributed attempts keep the account-wide delay extended: each failure re-set it, so an attacker rotating through 20 addresses blocked the owner for 3,541 of 3,600 seconds in the engineering review's simulation. D-070 changes the account-wide scope: the delay is set once per admitted attempt and is never extended by refusals, and a browser holding a valid device token is exempt from it. Per-address and per-account-and-address limits are unchanged. There is still no permanent lockout: counters expire with the window, and a successful sign-in clears that account-and-address pair.

The `aegis-api` Valkey user gains an ACL selector, `(~ratelimit:* +mget +pttl +incrby +expire +set +del +multi +exec)` (redis-py's `incr()` sends `INCRBY`; found by the smoke test): these commands work only on `ratelimit:*` keys, and the API still cannot read or change the task queues beyond sending tasks. The smoke test checks both. Existing development ACL files are reported as out of date by `init_dev_secrets.py` and are regenerated with the documented workflow (D-060 §3); passwords are kept.

Limitation: users behind one shared address (NAT, proxy) share the per-address limit (SR-005).

**Affects:** SYSTEM_ARCHITECTURE §9, §12.

## D-067 — Structured security logging for authentication

Authentication events are written as structured log records (logger `app.security`) with an `event` name: `auth.login_succeeded`, `auth.login_failed` (with `reason` and, for known accounts, `user_id`), `auth.logout`, `auth.registration_succeeded`, `auth.registration_rejected`, `auth.session_expired`, `auth.password_rehashed`, `auth.password_reset_issued`, `auth.password_reset_completed` (with `revoked_count`), `auth.password_reset_failed`, `auth.csrf_rejected` (with `reason`), `auth.rate_limited` (with `scope`), `auth.rate_limiter_unavailable`, `auth.forbidden`, `auth.ephemeral_secret_key`, `admin.registration_changed`, and the device events `auth.device_trusted`, `auth.device_revoked`, `auth.devices_revoked`, `auth.device_rejected` and `auth.account_deactivated` (D-070).

Records identify people by user ID and client address, never by email address. Passwords, session tokens, CSRF tokens, reset tokens, cookies and the secret key are never logged; the existing redaction of sensitive field names (D-042) remains as a second layer. Tests and the smoke test search the logs for every secret value used.

Persistent, queryable audit-log storage remains roadmap task 2.6; these records are its source events.

**Affects:** SYSTEM_ARCHITECTURE §9, §11.

## D-068 — Administrator password reset tokens

Implements D-012. An instance administrator issues a reset token for a user (`POST /api/v1/admin/password-resets` or Settings → Security). The token:

- is 256 random bits, stored only as a SHA-256 hash, valid for `AEGIS_PASSWORD_RESET_TOKEN_TTL_MINUTES` (60), single-use;
- replaces the user's earlier unused tokens;
- is shown once, as a link `/reset-password#token=…`. A URL fragment is never sent to a server, so the token does not reach access logs or `Referer` headers; the reset page removes it from the address bar as soon as it has read it. The administrator hands the link to the user out of band; AEGIS sends no email.

Redeeming the token (`POST /api/v1/auth/password/reset`) checks the password policy, sets the new password, marks the token used and revokes every session of the account, in one transaction. A rejected password leaves the token usable. The user is not signed in automatically. The CLI's `reset-password` sets a new password directly and also revokes every session.

**Affects:** PRD FR-AUTH-005; SYSTEM_ARCHITECTURE §9.

## D-069 — API documentation restricted to instance administrators

Amends D-042 and D-056. Until now, wherever API documentation was enabled (development and test by default), `/api/docs` and `/api/openapi.json` were readable without signing in. The schema is a complete map of the API, so it is no longer public anywhere:

- Both routes require a signed-in instance administrator: 401 `authentication_required` without a session, 403 `forbidden` for other users. Responses are `Cache-Control: no-store`. FastAPI's own public schema route is not registered.
- Documentation stays disabled in production unless `AEGIS_API_DOCS_ENABLED=true`, and even then it is admin-only.
- The vendored Swagger UI assets under `/api/docs/assets/` stay unauthenticated: they are the unmodified upstream files and contain nothing about AEGIS.
- Unchanged: every API endpoint already enforces authentication itself; the development ports (8080, 8000) listen on 127.0.0.1 only.

Tests cover anonymous (401), non-administrator (403) and administrator (200) access to both routes.

## D-070 — Two-phase sign-in rate limiting and trusted-device exemption

Amends D-066. The engineering review of 2026-11-17 found two defects in the limiter; this decision changes the account-wide scope to fix them.

**Defect 1: distributed attempts kept the account locked.** The account-wide scope blocked the account for 10 seconds after every failure, and each failure re-set the block. An attacker rotating through 20 addresses, retrying whenever the block lapsed, kept an owner who signed in from an ordinary address blocked for 98% of an hour (3,541 of 3,600 seconds in the simulation). D-066 said this could not happen.

**Defect 2: parallel attempts bypassed the limits.** Limits were checked before the password and failures were recorded afterwards, so N parallel requests all passed the check (100 of 100 admitted in the simulation).

### Algorithm

Sign-in is two-phase. `begin_login` reserves the attempt; `finish_login` releases it with its outcome. All counters are changed with atomic Valkey commands. In-flight counters use INCRBY (and the same command with a negative amount to release) and expire after 60 seconds, so a request that dies cannot leak a reservation.

1. **Reserve.** INCRBY the in-flight counters for the client address, the account-and-address pair and, unless the request is trusted (below), the account. Then read the blocks and the failure counters. The reservation comes *before* the blocks are read: a failure that completes concurrently sets its block before it releases its reservation, so an attempt that reserved after the release sees the block.
2. **Admit or refuse.** With `others` = in-flight attempts other than this one:
   - *Per address:* admitted while `failures + others < 30` in the window (a hard limit, as before).
   - *Per account and address:* refused while a block is active. Admitted if `others = 0` or `failures + others < 5`. Past the five free failures, one attempt at a time for the pair.
   - *Per account, any address (unless trusted):* refused while the account block is active; admitted if `others = 0` or `failures + others < 20`. An attempt admitted with `others = 0` past the threshold sets the account block (SET NX, 10 seconds) and is the only attempt admitted during it. Refusals and failures never re-set it.
   - A refused reservation is released at once. A refusal caused only by concurrent attempts answers 429 with a 1-second retry hint, in the same generic form as the others.
3. **Finish.** A failure increments the failure counters and, past the free failures, sets the pair's progressive block (30 seconds, doubling, capped at the window). A success clears the pair's counters and block; successes are never counted as failures. An abandoned attempt (for example after a database error) is released without counting. An attempt can be finished once.

**Why this stops the demonstrated attack.** The account-wide delay admits one attempt per 10 seconds and does not grow. A request carrying a valid device token does not compete for that attempt at all. The regression test `test_rotating_addresses_cannot_lock_out_the_account_owner` runs the attack for an hour with 20 rotating addresses while the owner signs in every second: the owner is admitted every second and the attacker stays within one attempt per delay plus the bounded burst below. `test_owner_with_a_device_token_signs_in_during_a_distributed_attack` does the same over HTTP with real client addresses.

**Why the concurrency is now safe.** The reservations are atomic and precede the checks. Fifty simultaneous attempts on one pair admit exactly the five free ones; past the free failures, exactly one; fifty attempts on one account from fifty addresses after the threshold admit exactly one. These are tested against the in-memory store and against a real Valkey server (`test_valkey_rate_limit.py`).

### Trusted-device exemption (approved 2026-11-17, with conditions)

The project owner approved the exemption on 2026-11-17, subject to the ten conditions below. Each is enforced in code and covered by tests.

1. **Only a hash is stored.** The table `trusted_devices` (migration `c4d8e2f6a7b9`) holds the SHA-256 of the device token. The token itself is never stored or logged; the smoke test checks that no token reaches the logs.
2. **Cookie.** `__Host-aegis_device`: Secure, HttpOnly, SameSite=Strict, Path=/, host-only (no `Domain`).
3. **Lifetime.** At most 30 days, fixed at issue time (`AEGIS_DEVICE_TRUST_DAYS` cannot exceed 30). Use never extends it.
4. **Invalidation.** A password change or reset (`accounts.set_password`, which the administrator's and the CLI's resets both use) revokes every device of the account. Deactivation (`accounts.deactivate`) ends the account's sessions and devices at once. No endpoint deactivates an account in v0.1.0; account management is roadmap 2.2.
5. **Independent revocation.** `DELETE /api/v1/auth/devices/{id}` revokes one device. `GET /api/v1/auth/devices` lists the user's devices with their metadata, never a token or hash.
6. **Never authenticates.** A device cookie does not sign anyone in: sessions are a separate table and cookie. A device only exempts the sign-in from the account-wide delay, and a sign-in still requires the password.
7. **Per-address and per-account-and-address limits still apply** to trusted devices (unchanged; tested).
8. **Device management is protected.** The endpoints are under `/api/`, so the CSRF middleware covers them (403 without a valid token). They require a session (401 without one), and a device of another account is reported as not found (404), so existence is not revealed.
9. **Ordinary sign-out does not revoke device trust.** Signing out ends the session only. Sign-out everywhere, which would end device trust, arrives with roadmap 2.2.
10. **Tests:** revocation, password-reset invalidation, deactivation, expiration, token replay (a copied cookie on another account, and a revoked cookie) and unauthorized management requests are covered in `test_devices.py` and `test_device_api.py`.
11. **Interface.** Settings → Security → Trusted devices lists the browsers (name from the user agent, dates, "This browser" marker), explains what trust does and does not do, and revokes one browser after an explicit confirmation. It uses the device endpoints above; the server enforces ownership. Covered by unit tests (`trustedDevices.test.tsx`) and by the browser suite (`e2e/trusted-devices.spec.ts`, 11 tests).

The exemption is limited to the account-wide sign-in delay, so a browser that holds a device still faces the per-address and per-account-and-address limits. Its residual risks are recorded in SR-009.

### Accepted limitations

- **Account counter bursts (SR-010).** The account-wide failure counter is a fixed 15-minute window. When it resets, up to 20 attempts are admitted quickly before the delay resumes. The long-run rate is one attempt per delay, plus at most 20 per window.
- **Shared addresses (SR-005)** and **browsers without a device token during an attack (SR-009)**, as above.
- A client whose attempt is refused only because others are in flight can retry every second; it still holds at most one reservation at a time.

### Pool capacity (part of this change)

Sign-in runs in a 40-thread pool and every reservation uses a Valkey connection. The API's pool held 4 connections, so a burst of concurrent sign-ins was refused with 503. The pool is now a blocking pool of 16 connections that waits up to 5 seconds (D-072).

**Affects:** SYSTEM_ARCHITECTURE §9.1; SECURITY_RISKS SR-005, SR-009, SR-010; PRD FR-AUTH-002.

## D-071 — One email normalization; lower-case database constraint

- `normalize_email` (strict) validates an address for registration and the CLI. `normalize_email_for_lookup` (never raises) is used for sign-in, for finding the account a device token belongs to, and for every rate-limit key. The lookup version calls the strict one, so there is one normalization.
- Internationalized domains are converted to IDNA: `user@Bücher.example`, `USER@BÜCHER.EXAMPLE` and `user@xn--bcher-kva.example` name the same account and share one set of counters. Before this change, sign-in did not convert the domain, so an account registered with an international domain could not sign in (finding M-2).
- Input that is not a valid address is lower-cased and stripped, or, if it contains control characters, replaced by an empty string, which matches nothing. The empty replacement fixed a defect the new tests found: a NUL character in a sign-in address reached PostgreSQL and produced a 500 response.
- Migration `b3c9d1e2f4a5` adds the CHECK constraint `ck_users_email_normalized` (`email = lower(email)`). It changes no data; if a non-normalized row existed the migration would fail and change nothing. None exists, because every write path normalizes.

**Affects:** SYSTEM_ARCHITECTURE §9.1; PRD FR-AUTH-001.

## D-072 — Reset-token cleanup, CLI operator record, startup preparation and broker pool

- **Reset tokens.** `purge-expired` also deletes reset tokens that were used or expired more than 7 days ago (the session retention period). Migration `b3c9d1e2f4a5` adds an index on `password_reset_tokens.issued_by_user_id`: it is the foreign key's column, and the foreign key's `ON DELETE SET NULL` would otherwise scan the table.
- **CLI operator.** A password reset from the command line records `operator`: the operating-system account that ran the command, as the operating system reports it. It is not verified; anyone with shell access to the server can run the command. No account is created for the operator, because none exists to record. This is the actor information FR-AUTH-005 asks for, as far as it can be known without inventing an identity. The persistent audit log (roadmap 2.6) will store it.
- **Dummy hash.** The hash that spends the time of a real check on unknown accounts is computed when hashing is configured at start-up, so the first unknown-account sign-in takes as long as every later one.
- **Broker pool.** A blocking pool of 16 connections that waits up to 5 seconds for a free one (previously 4 connections, refusing at once). A request that times out fails closed, like any broker failure.
- **Commit before responding.** The database session commits only when its dependency exits, after the route has returned. A request that followed a sign-in, sign-out, password reset or reset-link creation could therefore read the previous state. Found by the browser smoke test (a session revoked by a reset was still accepted, and a new sign-in was refused, for a few milliseconds). Each of these routes now commits before it responds, and the smoke test passed on repeated runs afterwards.
- **Corrections.** The Argon2 decision is cited as D-062 in `pyproject.toml`. The temporary-key docstring in `app/main.py` now says that sessions survive a restart (they are stored in the database), while CSRF tokens, device tokens and rate-limit counter names do not.

**Affects:** PRD FR-AUTH-005; SYSTEM_ARCHITECTURE §12.3 (broker).

## D-073 — End-to-end authentication tests with Playwright

- **Tool.** `@playwright/test` 1.64.1, pinned exactly. It was published on 2026-10-14, older than the two-week minimum the project applies to new releases; the newest stable release at the time (1.65.1, four days old) was not used. Chromium comes from `npx playwright install chromium` into the per-user Playwright cache; it is not part of the repository or of any image.
- **Files.** `apps/frontend/playwright.config.ts`; `e2e/helpers.ts` (accounts, administrator API, cookies); `e2e/stack.ts` (service steps on a disposable stack); `e2e/authentication.spec.ts` (sign-in, registration, protected routes, password reset); `e2e/trusted-devices.spec.ts` (Settings, revocation, account changes, security negatives). `tsconfig.e2e.json` type-checks them.
- **Coverage.** Authentication: sign-in and return to the requested page; failed sign-in; reload keeps the session; sign-out ends the server session; protected routes redirect; registration closed by default and enabled by an administrator; mismatched confirmation; reset link with the token removed from the address bar; a reset link used twice; a reset that signs out a session in another browser. Trusted devices: the current browser is listed without its token; another browser is revoked after confirmation and disappears; ordinary sign-out keeps the device and signing in again reuses it; a password reset revokes the account's devices; an expired device is no longer trusted (disposable stack); account deactivation ends sessions and revokes devices (disposable stack). Security: device management needs a session; revocation needs a valid CSRF token; one user cannot see or revoke another user's device; a device cookie alone does not authenticate; the device exemption keeps the per-address and account-and-address limits.
- **Not covered in the browser:** the account-wide delay being bypassed by a device during a distributed attack. Reproducing it needs twenty failures from twenty addresses, which one browser cannot produce; the backend tests do this (`test_rotating_addresses_cannot_lock_out_the_account_owner`, `test_owner_with_a_device_token_signs_in_during_a_distributed_attack`). Session expiry by inactivity or the 12-hour limit is covered by backend tests with an injected clock.
- **No real waits.** Expiry is produced by setting `expires_at` in the disposable database; no test waits for a device lifetime.
- **Accounts.** On a disposable stack the administration CLI creates accounts (`app.cli create-user`, password on standard input), so the public registration limit (five per address per hour, D-066) does not apply. Without a disposable stack, accounts are created through registration, and the suite must run on a fresh stack.
- **Where it runs.** The tests change their deployment, so they run only against a disposable stack. `infrastructure/scripts/smoke_test.py --e2e` runs them against the `aegis-smoke` project, through nginx, PostgreSQL and Valkey, with the administrator it creates. Scenarios that need a database or service step are skipped unless `AEGIS_E2E_COMPOSE_PROJECT` names a Compose project other than `aegis`, which the tests refuse. Credentials, SQL and tokens are never placed on a command line, and failure messages do not contain them.
- **Environment.** `AEGIS_E2E_BASE_URL` (default `http://127.0.0.1:8080`), `AEGIS_E2E_ADMIN_EMAIL`, `AEGIS_E2E_ADMIN_PASSWORD`, and for the service steps `AEGIS_E2E_COMPOSE_PROJECT` and `AEGIS_E2E_COMPOSE_FILE`.
- **CI (approved 2026-11-17).** The Containers job in `.github/workflows/ci.yml` sets up Node.js from `apps/frontend/.nvmrc` (the same pinned `actions/setup-node` as the frontend job), installs the locked frontend dependencies with `npm ci`, installs Chromium with `npx playwright install --with-deps chromium`, and runs `smoke_test.py --build --e2e`. The browser tests run against the disposable `aegis-smoke` project, which the job creates and removes; the development project and its volumes are never accessed. No secret is used: the administrator's credentials are generated per run and exist only in the job's memory. The workflow keeps its read-only token, its pinned action commit hashes, `persist-credentials: false`, and the 40-minute job timeout. Playwright reports and traces are not uploaded as artifacts, so that typed values cannot leave the job. A failed browser test fails the job (the smoke test exits non-zero). The workflow was checked locally by parsing it and by running the same command here; **the first GitHub Actions run (44124113383, commit e380686) failed in the Containers job at one registration test; run 44131732739 (commit 33f94ae) passed all three jobs. See D-074.**

- **Location (deviation from D-014).** D-014 places end-to-end tests in the repository's root `tests/` directory. They are in `apps/frontend/e2e/` instead, because `@playwright/test` is installed with the frontend and Node resolves it from the test file's location. This deviation needs the project owner's decision: either D-014 is amended to the frontend location, or the tests move and a link to the frontend dependencies is set up.

**Affects:** CLAUDE.md §10 (end-to-end testing); CONTRIBUTING §7; SYSTEM_ARCHITECTURE §14.5.

## D-074 — Phase 2.1 closed with one registration browser-test failure unexplained

**Decision.** Phase 2.1 (authentication) is closed. The first remote CI run for commit `e380686` failed in the Containers job: the registration test "when an administrator enables it, a visitor can register and is signed in" (`apps/frontend/e2e/authentication.spec.ts`) timed out after 30 seconds. The cause is not known. The owner chose to close the phase with this gap recorded, rather than hold it open.

**Evidence.**
- Run 44124113383 (commit `e380686`): Backend and Frontend passed; Containers failed on the browser step after 201 smoke checks and 23 passing Playwright tests. The CI error-context file was not available for analysis.
- A fresh disposable stack (`smoke_test.py --build --e2e`) passed all 202 smoke checks and all 24 Playwright tests, including the registration test.
- Repeating the registration test five times on one stack failed on the sixth registration with the intended limit (five per address per hour, D-066), which shows "Too many attempts" and fails after the 5-second assertion timeout. That is not the 30-second failure, and the limit was not changed.
- Inspection found no defect in the registration settings write (committed before the response), in `/auth/options`, or in the register route. The leading hypothesis is that the registration form never rendered (the form appears only after `/auth/options` reports registration open), so the first field waited until the test budget ended. This is not confirmed.
- Commit `33f94ae` added diagnostics to the registration tests: the `/auth/options` status and its boolean, the URL path, whether the form is shown, the visible alert text and the first line of the failure. They print on failure only and contain no credentials, email addresses, cookies or tokens; nothing is uploaded.
- Run 44131732739 (commit `33f94ae`): Backend, Frontend and Containers all passed. The Containers job's Chromium installation, Docker builds, smoke checks and browser tests all succeeded.

**Risk accepted.** A registration browser test can fail in CI for a reason not yet identified. It is not a known application defect, and the registration limits are unchanged. Registration remains closed by default, and the backend registration tests cover the endpoint independently of the browser.

**Follow-up.** If the registration test fails again, the diagnostic output identifies the failing operation and page state, and the cause should be recorded here before any change. Do not raise the test timeout or weaken the assertions as a workaround.

**Affects:** CLAUDE.md §10 (end-to-end testing); CLAUDE.md §15 (definition of done); DEVELOPMENT_ROADMAP §2.1.

## D-075 — Account management: profile, password and sessions (Phase 2.2)

**Decision.** The signed-in user can view and change their username, change their password, and see and end their sessions. The scope is the four requirements of roadmap task 2.2 and nothing else. There is no display name, no email change (no email verification exists in v0.1.0), no preferences store, and no self-deactivation or administrator user management.

- **Profile.** `GET` and `PATCH /api/v1/account/profile`. The username change requires the current password. The email address and the creation date are shown; the status is always "Active" for a signed-in user, because inactive accounts cannot sign in.
- **Password.** `POST /api/v1/account/password`. The current password is verified and the new one must differ and meet the existing policy. On success this browser's session token is rotated (the session row keeps its identifier and expiry, and the previous token stops working), every other session of the account is revoked, every trusted device is revoked (D-070), and this browser's device cookie is cleared, because its device was revoked.
- **Sessions.** `GET /api/v1/account/sessions` lists active sessions only: not revoked, not expired, and not idle. `DELETE /api/v1/account/sessions/{id}` revokes one session; revoking the current one clears the cookies, as logout does. `POST /api/v1/account/sessions/revoke-others` revokes every other session and leaves trusted devices alone (logout does not revoke them, D-070).
- **Ownership.** Every session operation is limited to the signed-in account. Another account's session, and an unknown identifier, both return `404 session_not_found`.
- **Sensitive changes are limited per account.** Username and password changes share a limit of five attempts per account in 15 minutes, every attempt counting. It is separate from the address-based sign-in limits and fails closed when Valkey is unavailable (as the other limits do).
- **Generic errors.** A wrong current password returns `current_password_incorrect`, which names no account and no value. A taken username returns `username_unavailable` and does not name the holder.
- **Logging.** `auth.password_changed`, `account.username_changed`, `auth.account_change_refused`, `auth.session_revoked`, `auth.sessions_revoked` and `auth.logout` record identifiers and counts only. No password, token, hash, address or username is logged.
- **Presentation.** Session responses carry no token, hash or IP address, and the interface shows none. Responses that hold account or session information are `no-store`. Every state-changing request needs a CSRF token (the existing middleware).
- **Storage.** No migration. The `user_sessions` and `users` tables already hold everything the feature uses.
- **Shared code.** The session and CSRF cookie helpers moved from `app/api/v1/auth.py` to `app/api/cookies.py`, unchanged in behaviour, so both route modules use one implementation.

**Accepted risks.** A signed-in user can learn whether a username is taken, by trying it (the same concern as SR-007, limited here to users who are already signed in). The stored IP address of each session is kept for the account's own records but is not shown.

**Affects:** PRD FR-AUTH-004 (User Profiles); PRD FR-AUTH-003 (session management); DECISIONS D-070 (trusted devices); DEVELOPMENT_ROADMAP §2.2.

## D-076 — Locally maintained security patch for picomatch (GHSA-fc5q-39xc-vjpf)

**This is a locally maintained remediation, not an upstream fix.** It removes the vulnerable behaviour from every copy of picomatch in the frontend's installed tree. The advisory itself stays open, and the full `npm audit` keeps reporting it, until picomatch publishes a fixed release.

**Advisory.** GHSA-fc5q-39xc-vjpf / CVE-2026-112366 (high, CVSS 7.5, CWE-1333). picomatch through 4.0.7 compiles a repeated extglob (`+(...)` or `*(...)`) whose branch nests an ambiguous quantifier into a regular expression that backtracks exponentially. The existing guard in picomatch examines only patterns with more than one branch.

**Why no upstream release.** The affected range is every published version (`<= 4.0.7`); 4.0.7 is the latest release and no patched version exists. At decision time eleven competing fix pull requests (#237, #238, #246, #257–#264) were open and unmerged, and none had been accepted by the maintainers. Every release line of Vite (6–8), Vitest (3–5) and tinyglobby requires picomatch 4, and the older majors (2.3.2, 3.0.2) were measured to be equally vulnerable, so no compatible version or replacement removes it. No maintained fork exists.

**The three affected copies.** `npm ls` shows one package (`picomatch@4.0.7`, used by Vite 8.3.8, Vitest 5.1.0, tinyglobby 0.2.17 and fdir 6.5.0). A scan of every installed JavaScript file found two more, compiled into other tools' own files and invisible to `npm ls`, `npm audit` and npm overrides: an older picomatch in Prettier 3.10.1 (`prettier/index.mjs`, reachable through Prettier's configuration API) and in Playwright 1.64.1 (`playwright/lib/matchers/expect.js`, from its bundled Jest utilities; no input path to it was found).

**Decision.** One self-contained guard (`apps/frontend/scripts/picomatch-guard.js.txt`) is added to picomatch's `analyzeRepeatedExtglob` in all three copies. A repeated extglob is reported as risky when a branch contains a star that is neither escaped, inside a bracket expression, nor the start of a nested extglob (`*(`), or when a branch is exactly one nested group whose alternatives picomatch's own multi-branch rules flag (empty, star-only or overlapping). picomatch then matches the pattern as literal text, the treatment it already gives risky multi-branch patterns.

- **picomatch package:** the official 4.0.7 tarball (integrity verified; identical to the upstream source at tag `4.0.7`) is vendored in `apps/frontend/vendor/picomatch/` with the guard and with the development fields removed from `package.json` (npm installs a linked directory's development dependencies). It replaces every `picomatch` dependency through `devDependencies` and an npm `overrides` entry. The licence is kept unchanged (THIRD_PARTY_NOTICES).
- **Bundled copies:** `scripts/picomatch-security-patch.mjs apply` (run on `postinstall`) inserts the guard. Each target is pinned to an exact package version and to the SHA-256 of its unpatched file; anything else is refused. The Docker build runs it explicitly after `npm ci --ignore-scripts`, so dependency install scripts stay disabled.
- **Verification:** `scripts/picomatch-security-patch.mjs verify` (`npm run security:picomatch`) scans every installed JavaScript file for a copy of the picomatch engine and fails unless `node_modules/picomatch` resolves to the vendored copy and the copies found are exactly the three expected ones, each guarded, at its reviewed version and matching the SHA-256 of its reviewed patched file. It runs in the frontend CI job after a clean install and in the frontend image build. Negative tests confirmed it fails for an unpatched bundle, an unexpected copy, a bundle changed after review, a non-vendored package, a removed guard and a missing package, and that `apply` refuses an unreviewed version.

**Evidence (local, Windows and Linux).**

- Exploit patterns measured in child processes with a 5-second limit: `+(*a)`, `*(*a)`, `+(**a)` and `+(*a|b)` took 0.7–1.3 s at 24 characters and were killed at 28; `+(*)`, `+(*.js)`, `+(a*b)`, `+(*[a])`, `+(*)c` and `*(a*|b)` took 0.9–4.4 s at 24; `*(W*, *)` was killed at 20; `+(@(a|aa))` took 245 ms at 30 and 1.7 s at 34. Patched, every case took under 10 ms, also at 5,000 and 50,000 characters.
- Prettier's public API with a `+(*a)` override glob: 6.1 s at a 26-character path before, 6–8 ms up to 1,000 characters after.
- 144 compilations of 36 ordinary globs (including Vite's and Vitest's defaults and AEGIS's own patterns) with four option sets produce byte-identical regular expressions before and after.
- picomatch's own test suite: 1,979 of 1,983 tests pass.
- The frontend image contains no picomatch code.

**Behaviour change.** Repeated extglobs with a bare star in a branch, or wrapping one group of overlapping alternatives, match only their literal text. The four failing upstream tests assert the old behaviour for exactly such patterns: `isMatch('abc', '+(*)c')` (in two tests), `isMatch('ax', '*(a*|b)')` and `isMatch('my/folder (Work, Accts)', '*/*(W*, *)*')`. Each of these patterns was measured to be exploitable in the original (`+(*)c` 4.0 s and `*(a*|b)` 0.9 s at 24 characters, `*(W*, *)` killed at 20), so the change is the fix itself. Keeping them working safely would need a semantics-preserving rewrite of the regular expression, which is what the unmerged upstream pull requests attempt. No AEGIS configuration, and no Vite or Vitest default, uses such a pattern.

**Remaining risks.** The full `npm audit` reports six high findings for this chain: it matches the package by name and version, and the vendored copy truthfully keeps version 4.0.7 (the version is not altered to silence it). The production audit gate (`npm audit --omit=dev --audit-level=high`) is unaffected and clean. The patch is AEGIS's own code: it has not been reviewed by the picomatch maintainers. Copies of picomatch outside the frontend project (for example in globally installed tools) are not covered.

**Maintenance.** A Prettier or Playwright upgrade stops `npm ci` until the new bundle is reviewed and the pins in `scripts/picomatch-security-patch.mjs` are updated. A Vite, Vitest or tinyglobby upgrade keeps receiving the vendored copy through the override. Recheck the advisory and the upstream pull requests at each dependency review.

**Removal.** When picomatch publishes a fixed release and Vite, Vitest, tinyglobby, Prettier and Playwright adopt it: delete `apps/frontend/vendor/picomatch/`, the `picomatch` entries in `devDependencies` and `overrides`, the `postinstall` and `security:picomatch` scripts, `scripts/picomatch-*`, the CI step, the Dockerfile lines and the `.prettierignore` and `.oxlintrc.json` entries for `vendor/`; run `npm install`; confirm the full `npm audit` no longer reports the advisory; and record the removal here.

**Affects:** `apps/frontend/package.json`, `apps/frontend/package-lock.json`, `apps/frontend/vendor/picomatch/`, `apps/frontend/scripts/picomatch-*`, `.github/workflows/ci.yml`, `infrastructure/docker/frontend.Dockerfile` (and its `.dockerignore`), THIRD_PARTY_NOTICES (Vendored Assets).

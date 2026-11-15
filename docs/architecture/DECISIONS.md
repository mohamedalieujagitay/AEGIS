# AEGIS — Decision Register

**Status:** Living document  
**Last Updated:** 2026-11-15  
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
| D-011 | Signed job payloads, per-job ingestion tokens, separate ingestion listener | 2026-11-15 | Approved |
| D-012 | Administrator and CLI password reset only in v0.1.0 | 2026-11-15 | Approved |
| D-013 | Withdrawn | 2026-11-15 | Withdrawn |
| D-014 | Root `tests/` for end-to-end tests; no `packages/` or top-level `workers/` | 2026-11-15 | Approved |
| D-015 | GitHub Actions for CI | 2026-11-15 | Approved |
| D-016 | Frontend tooling deferred until frontend implementation | 2026-11-15 | Resolved by D-021 to D-026 (data-fetching library still open) |
| D-017 | Domain verification does not authorize active assessment of resolved IPs | 2026-11-15 | Approved |
| D-018 | Instance administrator; CLI bootstrap; open registration off by default | 2026-11-15 | Approved |
| D-019 | Third-party lookups disabled by default | 2026-11-15 | Approved |
| D-020 | Two worker roles: assessment and internal | 2026-11-15 | Approved |
| D-021 | Vite 8 as the frontend build tool | 2026-11-15 | Approved |
| D-022 | React Router 8 for routing | 2026-11-15 | Approved |
| D-023 | npm as the frontend package manager | 2026-11-15 | Approved |
| D-024 | Node.js 22 LTS, version 22.22.0 or later | 2026-11-15 | Approved |
| D-025 | Template linter (oxlint) removed; linter chosen in its roadmap task | 2026-11-15 | Resolved by D-033 |
| D-026 | TypeScript 7, subject to compatibility testing | 2026-11-15 | Approved, conditional (linting and formatting verified; testing tools pending) |
| D-027 | Strict TypeScript compiler profile | 2026-11-15 | Approved |
| D-028 | Tailwind CSS 4, CSS-first, through the official Vite plugin | 2026-11-15 | Approved |
| D-029 | Frontend routing architecture | 2026-11-15 | Approved |
| D-030 | In-house UI components; no component or class-merging library | 2026-11-15 | Approved |
| D-031 | Application shell, navigation and error handling | 2026-11-15 | Approved; navigation amended by D-034 |
| D-032 | Design tokens; Tailwind default palette removed | 2026-11-15 | Approved; token values superseded by D-035 |
| D-033 | Oxlint with type-aware rules, and Prettier, for the frontend | 2026-11-15 | Approved |
| D-034 | Overview and shell built from the approved UI design, with empty states | 2026-11-15 | Approved; extended by D-035 |
| D-035 | Full AEGIS UI design: stylesheet tokens and all seven pages, with empty states | 2026-11-15 | Approved |

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

The root `tests/` directory holds Playwright end-to-end tests. The empty `packages/` and top-level `workers/` directories were removed. Workers live in `apps/backend/app/workers/`, and a shared package directory will be introduced only when a genuine shared package exists.

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

**Open item:** the design's navigation (Assets, Assessments, Findings, Reports, Activity, Settings) differs from PRD §5.2 (Assets, Reconnaissance, Network Security, Web & API Security, System Security, Threat Intelligence, Vulnerabilities, Monitoring, Reports, Settings). The PRD has not been changed; this needs a product decision.

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

Known accessibility gap: input borders (#22345a) are 1.5:1 against card surfaces, below the 3:1 guideline for component boundaries. Inputs remain identifiable by their darker fill and placeholder text; this should be revisited with the design owner.

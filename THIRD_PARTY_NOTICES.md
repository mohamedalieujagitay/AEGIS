# AEGIS — Third-Party Notices

AEGIS uses or plans to use third-party software and libraries.

This document is the dependency licensing register for AEGIS. It records each planned dependency, its licence as currently understood and its review status. Attribution notices required for distribution will be added as dependencies complete review.

## Review Status Definitions

| Status | Meaning |
|---|---|
| **Proposed** | Suggested for use. Not yet approved as part of the stack. |
| **Planned** | Approved as part of the stack. Licence review not yet completed. |
| **Reviewed** | Licence review completed for a specific version and distribution. |
| **Approved** | Reviewed and accepted for inclusion in a release. |
| **Deferred** | Not approved for the current release. Requires separate evaluation. |

**Completed licence reviews:** psycopg 3.3.9 for Windows and for Linux (see "psycopg Licence Review" below); argon2-cffi 25.1.0 and argon2-cffi-bindings 26.1.0 (see "Argon2 Licence Review" below). All other licences below are preliminary and must be verified against the exact version and distribution selected.

**Container images are built locally only.** No AEGIS image may be published, pushed or otherwise distributed until a separate distribution-compliance review is complete (DECISIONS.md D-059). Distribution compliance has not been achieved.

## Dependency Policy

Before introducing a dependency, contributors must review:

- License compatibility.
- Security history.
- Maintenance status.
- Dependency requirements, including transitive dependencies.
- Redistribution obligations.

Running a tool as an external process is not assumed to resolve licensing obligations.

## Core Technologies

| Technology | Purpose | License (preliminary) | Status | Notes |
|---|---|---|---|---|
| Python 3.11 | Backend language | PSF-2.0 | Planned | |
| FastAPI 0.163 | Backend framework | MIT | Planned | Installed in `apps/backend`. Requires `opentelemetry-api` (see Backend Packages). |
| Uvicorn 0.54 | ASGI server | BSD-3-Clause | **Approved** | Approved in the Phase 1.3 Bundle 1 review. Run with `--no-server-header` in deployments (DECISIONS.md D-042). |
| SQLAlchemy 2.1 | ORM | MIT | Planned | Installed (2.1.8) in `apps/backend`. |
| Alembic 1.20 | Database migrations | MIT | Planned | Installed (1.20.1) in `apps/backend`. |
| Celery 5.7 | Background processing | BSD-3-Clause | Planned | Installed (5.7.0, with the `redis` extra) in `apps/backend`. Transitive dependencies are listed under Backend Packages (DECISIONS.md D-055). |
| PostgreSQL 18 | Database | PostgreSQL License | Planned | Official image `postgres:18.7-trixie` in Docker Compose; see Container Images. |
| Valkey 9 | Message broker | BSD-3-Clause | Planned | Image `valkey/valkey:9.1.3-alpine`. Compatibility with Celery's Redis transport and per-role ACL users **verified** with Celery 5.7.0 and kombu 5.7.0 (DECISIONS.md D-055). |
| React | Frontend framework | MIT | Planned | |
| TypeScript 7 | Frontend language | Apache-2.0 | Planned | Installed (7.0.2). Compatibility with the linting and testing tools verified (DECISIONS.md D-026, D-033, D-047). |
| Tailwind CSS 4 | Styling | MIT | Planned | Installed through the official Vite plugin (see Frontend Packages). |
| Node.js 22 (>=22.22.2; baseline 22.23.5) | Frontend toolchain runtime | MIT | Planned | Not redistributed by AEGIS. Bundles third-party components under their own licences. Minimum raised for jsdom 31 (DECISIONS.md D-047). |
| npm | Frontend package manager | Artistic-2.0 | Planned | Bundled with Node.js. Not redistributed by AEGIS. |
| Docker Engine (Moby) | Container runtime | Apache-2.0 | Planned | Not redistributed by AEGIS. |
| Docker Compose | Service orchestration | Apache-2.0 | Planned | Not redistributed by AEGIS. |
| Docker Desktop | Container runtime on Windows and macOS | Proprietary (Docker Subscription Service Agreement) | Planned | Not redistributed by AEGIS. Free for personal use, education and small businesses; larger organisations require a paid subscription. Users are responsible for their own licence. |

### Why Valkey instead of Redis

Redis 7.4 and later are licensed under RSALv2/SSPLv1, and Redis 8 adds AGPLv3 as an option. Valkey is a BSD-3-Clause fork that is designed to be protocol-compatible with Redis. AEGIS has selected Valkey as its message broker (DECISIONS.md D-009), subject to the compatibility verification noted above.

## Python Libraries

| Library | Purpose | License (preliminary) | Status | Notes |
|---|---|---|---|---|
| psycopg 3 (`psycopg[binary]`) | PostgreSQL driver | LGPL-3.0-only | **Reviewed (Windows and Linux)** | Installed (3.3.9, with `psycopg-binary` 3.3.9) in `apps/backend` and the backend image. Used unmodified as a separately installed library. The Windows wheel bundles libpq and OpenSSL; the Linux wheels also bundle Kerberos, LDAP, SASL, keyutils and libcrypt, including **LGPL components**. See "psycopg Licence Review". |
| pydantic | Data validation | MIT | Planned | Installed (2.14.3). |
| pydantic-settings | Configuration management | MIT | Planned | Installed (2.16.3). |
| argon2-cffi 25.1 | Argon2id password hashing | MIT | **Reviewed** | Installed (25.1.0) in `apps/backend` and the backend image (DECISIONS.md D-062). See "Argon2 Licence Review". |
| argon2-cffi-bindings 26.1 | Compiled bindings to the Argon2 reference library | MIT; bundles libargon2 under CC0-1.0 OR Apache-2.0 | **Reviewed** | Installed (26.1.0), pinned exactly in `pyproject.toml`. See "Argon2 Licence Review". |
| cryptography | Ed25519 job signing | Apache-2.0 OR BSD-3-Clause | Planned | Binary wheels bundle OpenSSL; verify during review. |
| redis (redis-py) 8.1 | Client used by Celery and the readiness check to connect to Valkey | MIT | Planned | Installed (8.1.0). The client library is MIT; the Redis server's licence change does not affect it. |
| import-linter 2.16 | Architectural import contracts | BSD-2-Clause | Planned | Development dependency only. Installed (2.16) in `apps/backend` (DECISIONS.md D-048). |
| Ruff 0.17 | Python linter and formatter | MIT | Planned | Development dependency only. Installed (0.17.5); a standalone binary with no Python dependencies (DECISIONS.md D-045). |
| mypy 2.4 | Python type checker | MIT | Planned | Development dependency only. Installed (2.4.1). Requires pathspec (MPL-2.0); see Backend Packages (DECISIONS.md D-045). |
| pip-tools 7.7 | Generates the hashed backend lock file | BSD-3-Clause | Planned | Maintainer tool, declared in the `lock` extra; not part of the lock file or of any installation (DECISIONS.md D-046). |

## Backend Packages

Installed in the backend virtual environment from `apps/backend/pyproject.toml` (Python 3.11). Exact versions and hashes are pinned in `apps/backend/requirements-dev.lock` (DECISIONS.md D-046).

Runtime, required by FastAPI, pydantic-settings and Uvicorn:

- starlette (BSD-3-Clause), anyio (MIT), annotated-doc (MIT), annotated-types (MIT), pydantic-core (MIT), typing-inspection (MIT), typing-extensions (PSF-2.0), python-dotenv (BSD-3-Clause), click (BSD-3-Clause), h11 (MIT), idna (BSD-3-Clause).
- Celery and its messaging libraries (DECISIONS.md D-055): kombu (BSD-3-Clause), billiard (BSD-3-Clause), vine (BSD-3-Clause), amqp (BSD-3-Clause; required by kombu even with the Redis transport), click-didyoumean (MIT), click-repl (MIT), click-plugins (BSD-3-Clause), prompt-toolkit (BSD-3-Clause), wcwidth (MIT), python-dateutil 2.9.0.post0 (Apache-2.0 OR BSD-3-Clause; pinned by Celery), six (MIT), tzlocal (MIT), tzdata (Apache-2.0), redis (MIT).
- **opentelemetry-api (Apache-2.0)**, a required dependency of FastAPI 0.163. It is the instrumentation API only: without an OpenTelemetry SDK and exporter, which AEGIS does not install, it records and sends nothing. This is consistent with the no-telemetry requirement (PRD §4.6).

Development only, required by Pytest and httpx2:

- iniconfig (MIT), pluggy (MIT), packaging (Apache-2.0 OR BSD-2-Clause), Pygments (BSD-2-Clause), colorama (BSD-3-Clause, Windows), httpcore2 (BSD-3-Clause), truststore (MIT).

Development only, required by Ruff, mypy and import-linter (DECISIONS.md D-045, D-048):

- mypy-extensions (MIT), librt (MIT), ast-serialize (MIT), grimp (BSD-2-Clause), rich (MIT), markdown-it-py (MIT), mdurl (MIT).
- **pathspec (MPL-2.0)**, required by mypy. MPL-2.0 is a file-level copyleft licence. It is used unmodified as a development tool and is never distributed with AEGIS, so it creates no obligations for AEGIS.

Lock-file maintenance only (`lock` extra, not installed by the lock file): pip-tools (BSD-3-Clause), build (MIT), pyproject_hooks (MIT), wheel (MIT), pip (MIT), setuptools (MIT).

Password hashing, required by argon2-cffi (DECISIONS.md D-062):

- argon2-cffi-bindings (MIT, bundling libargon2 under CC0-1.0 OR Apache-2.0), cffi 2.1.1 (MIT-0), pycparser 3.12 (BSD-3-Clause).

Database, required by SQLAlchemy, Alembic and psycopg:

- Mako (MIT), MarkupSafe (BSD-3-Clause), tzdata (Apache-2.0; installed on Windows by psycopg).
- psycopg-binary (LGPL-3.0-only) bundles libpq 18.4 (PostgreSQL License) and OpenSSL 3.6.5 (Apache-2.0) in the Windows wheel; see "psycopg Licence Review".

Build only: setuptools (MIT).

Exact versions and hashes: `apps/backend/requirements.lock` (runtime, used by the backend image) and `apps/backend/requirements-dev.lock` (development and CI). pip, setuptools and wheel are removed from the backend image (DECISIONS.md D-051).

## psycopg Licence Review

Engineering review of the installed packages, not legal advice. Reviewed on 2026-11-15.

**Scope:** `psycopg` 3.3.9 and `psycopg-binary` 3.3.9, wheel for CPython 3.11 on 64-bit Windows (`cp311-win_amd64`).

| Component | Version (measured) | Licence | Copyright | Licence text in the wheel |
|---|---|---|---|---|
| psycopg (Python code) | 3.3.9 | LGPL-3.0-only | Daniele Varrazzo and contributors | Yes |
| psycopg-binary (compiled extension) | 3.3.9 | LGPL-3.0-only | Daniele Varrazzo and contributors | Yes (same text) |
| libpq, bundled | 18.4 (build and runtime) | PostgreSQL License | PostgreSQL Global Development Group; Regents of the University of California | No |
| OpenSSL (libssl-3, libcrypto-3), bundled | 3.6.5 | Apache-2.0 | The OpenSSL Project Authors | No |

Findings:

- The bundled libraries form a closed set: libpq depends only on the bundled OpenSSL, and OpenSSL only on Windows system libraries. No Kerberos, LDAP, zlib or iconv library is bundled.
- AEGIS uses psycopg unmodified, as a separately installed package loaded through Python's import mechanism. AEGIS's own code remains Apache-2.0, which is compatible with this use of an LGPL-3.0 library.

Obligations:

- **Current distribution (source code only):** AEGIS declares psycopg as a dependency and users install it from PyPI. AEGIS does not distribute psycopg, libpq or OpenSSL, so their redistribution obligations do not apply to AEGIS.
- **If AEGIS distributes these binaries** (for example in a published container image):
  - LGPL-3.0 (psycopg): state prominently that psycopg is used and is covered by the LGPL; include the GPL-3.0 and LGPL-3.0 texts; keep psycopg replaceable (a separately installed package satisfies this); and provide the corresponding source of the distributed psycopg version (for example its source distribution), as required for conveying object code.
  - PostgreSQL License (libpq): keep the copyright notice and permission paragraph with every copy.
  - Apache-2.0 (OpenSSL): include a copy of the licence and keep its notices.
  - The libpq and OpenSSL licence texts are not in the wheel; AEGIS must supply them itself.
- **If psycopg is modified** (not planned): the modified source must be made available under the LGPL-3.0.

### Linux wheels (backend container image)

Reviewed on 2026-11-16 (DECISIONS.md D-059); keyutils licence and package versions reconciled on 2026-11-16 (D-060). Engineering review, not legal advice.

**Scope:** `psycopg-binary` 3.3.9 for CPython 3.11, the two Linux wheels the backend image can install, both pinned by SHA-256 in `apps/backend/requirements.lock`:

- `psycopg_binary-3.3.9-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` (`0953c1b9…be99`), used on x86-64 hosts;
- `psycopg_binary-3.3.9-cp311-cp311-manylinux_2_27_aarch64.manylinux_2_28_aarch64.whl` (`9f6f4108…83aa`), used on ARM64 hosts.

**Method.** Each wheel was unpacked and its `psycopg_binary.libs/` inspected: dynamic dependencies and SONAMEs (`readelf -d`), defined symbol versions (`readelf -V`), version strings, the debug-link file names (`.gnu_debuglink`, which on the AlmaLinux 8 build image carry the exact package release), and the runtime libpq version reported by psycopg. Build-time versions were checked against psycopg's own build script at tag 3.3.9 (`tools/ci/build_libpq.sh`), which builds libpq, OpenSSL, MIT Kerberos and OpenLDAP from source and takes Cyrus SASL, keyutils, libcrypt and e2fsprogs' com_err from the build image's system packages (manylinux2014: CentOS 7; manylinux_2_28: AlmaLinux 8). Licence texts were read from each project's source at the matching release; their SHA-256 hashes are listed so the texts can be retrieved and compared.

| Component (bundled library) | x86_64 version | aarch64 version | Version evidence | Licence (from the source) | Licence text source (SHA-256) |
|---|---|---|---|---|---|
| psycopg, psycopg-binary | 3.3.9 | 3.3.9 | wheel metadata | LGPL-3.0-only | `LICENSE.txt` in the wheel |
| libpq (`libpq.so.5.18`) | 18.6 | 18.6 | runtime and build version 180006 | PostgreSQL License | `COPYRIGHT` at `REL_18_6` (`3d6af92f…fdfd`) |
| OpenSSL (`libssl.so.3`, `libcrypto.so.3`) | 3.5.9 | 3.5.9 | version string | Apache-2.0 | `LICENSE.txt` at `openssl-3.5.9` (`7d5450cb…9e7a`) |
| MIT Kerberos / GSSAPI (`libgssapi_krb5`, `libkrb5`, `libk5crypto`, `libkrb5support`, `libcom_err.so.3`) | 1.22.2 | 1.22.2 | `KRB5_BRAND` string; build script | MIT Kerberos licence (BSD-style, with additional notices for included components) | `NOTICE` at `krb5-1.22.2-final` (`d37fcb88…605e`) |
| OpenLDAP (`libldap`, `liblber`) | 2.6.16 | 2.6.16 | build script; soname 2.0.200 | OpenLDAP Public License 2.8 (OLDAP-2.8) | `LICENSE` and `COPYRIGHT` at `OPENLDAP_REL_ENG_2_6_16` (`310fe25c…e569`, `5b4dfc20…b14c`) |
| Cyrus SASL (`libsasl2.so.3.0.0`) | 2.1.26 (CentOS 7 package; release not embedded) | 2.1.27, package `cyrus-sasl-lib-2.1.27-6.el8_5` | version string; aarch64 debug link | CMU licence (BSD-style, 4 clauses; **clause 4 requires an acknowledgement**) | `COPYING` at `cyrus-sasl-2.1.26` and `cyrus-sasl-2.1.27` (identical, `9d6e5d16…0d4b`) |
| keyutils library (`libkeyutils.so.1.5` on x86_64, `libkeyutils.so.1.6` on aarch64) | 1.5.8 (CentOS 7 package; release not embedded) | 1.5.10, package `keyutils-libs-1.5.10-9.el8` | version strings `keyutils-1.5.8` / `keyutils-1.5.10`; aarch64 debug link `libkeyutils.so.1.6-1.5.10-9.el8.aarch64.debug`. The `.so.1.5`/`.so.1.6` suffix is the library API version, not the package version: keyutils 1.5.10 adds the `KEYUTILS_1.6` symbol-version block (`version.lds`), and the Makefile names the library after the last block. The binaries define exactly `KEYUTILS_0.3` to `_1.5` (x86_64) and `_0.3` to `_1.6` (aarch64). | **LGPL, version 2 or (at your option) any later version.** The library's only sources, `keyutils.c` and `keyutils.h`, say "GNU Lesser General Public License … either version 2 of the License, or (at your option) any later version" in both releases (unchanged in current upstream). Upstream ships the LGPL **2.1** text; the RHEL/CentOS 8 package declares `LGPLv2+`. SPDX: `LGPL-2.0-or-later` as written; Fedora's SPDX conversion records `LGPL-2.1-or-later`, because the "Lesser" licence exists only from version 2.1. AEGIS records `LGPL-2.0-or-later` and meets its obligations under the LGPL-2.1 terms, which the "or later" grant permits; the obligations are the same under either reading. | `LICENCE.LGPL` at `v1.5.8` and `v1.5.10` (identical LGPL-2.1 text, `0d15593e…c521`); `keyutils.c` (`4c34f646…11bf`, `71e8565e…c184`); spec files declare `License: GPLv2+ and LGPLv2+` (the GPL part covers the command-line tools, which are not bundled) |
| libcrypt (`libcrypt.so.1`) | glibc 2.17 (symbol versions `GLIBC_*`; manylinux2014 baseline) | libxcrypt 4.1.1, package `libxcrypt-4.1.1-6.el8` (symbol version `XCRYPT_2.0`) | symbol versions; aarch64 debug link `libcrypt.so.1.1.0-4.1.1-6.el8.aarch64.debug` | **LGPL-2.1-or-later** (glibc `crypt/crypt.c`; libxcrypt `LICENSING`: overall LGPL-2.1-or-later, some files BSD or public domain) | glibc `COPYING.LIB` at `glibc-2.17` (`ca0061fc…0532`); libxcrypt `COPYING.LIB` and `LICENSING` at `v4.1.1` (`dc626520…e551`, `eaa47c6e…6d98`) |
| com_err from e2fsprogs (`libcom_err.so.2.1`) | CentOS 7 package (version not embedded) | 1.45.6, package `libcom_err-1.45.6-7.el8_10` | aarch64 debug link `libcom_err.so.2.1-1.45.6-7.el8_10.aarch64.debug` | MIT-style permission notice ("MIT Student Information Processing Board"); e2fsprogs `NOTICE`: lib/et is under an MIT-style licence | `lib/et/com_err.c` and `NOTICE` at `v1.45.6` (`873d31d8…db0ab`, `5da5ef15…9020`) |

Not bundled (provided by the image): glibc (`libc`, `libm`, `libdl`, `libpthread`, `libresolv`) and zlib (`libz.so.1`).

Findings:

- The bundled set is closed: every `NEEDED` entry resolves to a bundled library or to glibc and zlib from the base image.
- The wheel contains **only psycopg's LGPL-3.0 text**. None of the bundled libraries' licence texts or notices are included.
- libpq and OpenSSL versions differ from the Windows wheel (18.6 and 3.5.9 on Linux; 18.4 and 3.6.5 on Windows).
- The x86_64 wheel's system libraries come from CentOS 7 packages, which are no longer maintained upstream. Their exact package releases (Cyrus SASL, keyutils, glibc, e2fsprogs) are not embedded in the binaries; the upstream versions are.
- Reconciliation (D-060): an earlier planning note said keyutils was `LGPL-2.1-or-later` and the aarch64 version was "1.6". Both came from assumptions, not evidence: the licence statement in the source is "version 2 or later" (see the table), and "1.6" is the library's API version (`libkeyutils.so.1.6`) of keyutils **1.5.10**.

Obligations:

- **Local image building and running (current use):** building images on a developer's or operator's own machine and running them there does not convey the software to anyone, so the redistribution obligations below are not triggered. This is the only use permitted now.
- **Image distribution (not permitted until the distribution-compliance review, D-059).** Publishing, pushing or otherwise conveying an image that contains these wheels would require at least:
  - **LGPL components** (psycopg: LGPL-3.0-only; keyutils: LGPL version 2 or later, complied with under LGPL-2.1; libcrypt: LGPL-2.1-or-later): notices that the libraries are used and covered by the LGPL, the licence texts (LGPL-2.1, LGPL-3.0 and GPL-3.0), the ability to replace them (shared libraries and a separately installed Python package satisfy this), and the **complete corresponding source** of the exact distributed versions, either alongside the image or through a written offer. For the CentOS 7 and AlmaLinux 8 libraries this means the matching source packages (for aarch64: `keyutils-1.5.10-9.el8`, `libxcrypt-4.1.1-6.el8`; for x86_64: the CentOS 7 `keyutils-1.5.8` and `glibc-2.17` source packages used by the manylinux2014 image), and for psycopg its 3.3.9 source distribution.
  - **Cyrus SASL (CMU licence):** reproduce the copyright notice, conditions and disclaimer in the documentation, and retain the acknowledgement: "This product includes software developed by Computing Services at Carnegie Mellon University (http://www.cmu.edu/computing/)."
  - **MIT Kerberos:** reproduce the copyright notices, conditions and disclaimers of `NOTICE`, including those of its included components.
  - **OpenLDAP (OLDAP-2.8):** retain the copyright statements and notices, and reproduce the licence in the documentation.
  - **libpq (PostgreSQL License), com_err (MIT-style):** keep the copyright notices and permission paragraphs.
  - **OpenSSL (Apache-2.0):** include the licence and keep its notices.
  - The Debian base image's own packages (some GPL-licensed) carry similar source-availability obligations (see Container Images).
- **If psycopg is modified** (not planned): the modified source must be made available under the LGPL-3.0.

**Status:** findings recorded; **distribution compliance is not achieved**. The required texts, notices and source arrangements are not part of the images.

## Vendored Assets

| Asset | Purpose | License | Status | Notes |
|---|---|---|---|---|
| Swagger UI 5.35.0 (`swagger-ui-dist`) | API documentation page | Apache-2.0 | Planned | Three files vendored in `apps/backend/app/static/swagger-ui/` with the package's `LICENSE`, `NOTICE` ("swagger-ui, Copyright 2020-2021 SmartBear Software Inc.") and `swagger-ui-bundle.js.LICENSE.txt` (bundled components: MIT, and DOMPurify under Apache-2.0 or MPL-2.0). Served only when API documentation is enabled. Copied from the npm tarball (integrity verified); the package's `@scarf/scarf` install-time analytics dependency is never installed (DECISIONS.md D-056). |
| picomatch 4.0.7, patched | Glob matching for the frontend build and test tools (Vite, Vitest, tinyglobby, fdir) | MIT | **Reviewed** | Vendored in `apps/frontend/vendor/picomatch/` with the package's unchanged `LICENSE` ("Copyright (c) 2017-present, Jon Schlinkert."). Copied from the npm tarball (integrity verified; identical to the upstream source at tag `4.0.7`) with a local security patch for GHSA-fc5q-39xc-vjpf / CVE-2026-112366 and the development fields removed from `package.json`; see `vendor/picomatch/AEGIS-PATCH.md` and DECISIONS.md D-076. A development and build dependency only: nothing from it is in the frontend image. The same patch is applied at install time to the copies of picomatch bundled in Prettier 3.10.1 and Playwright 1.64.1 (both MIT, not redistributed by AEGIS). |

## Frontend Packages

Versions as installed in `apps/frontend/package-lock.json`.

| Package | Purpose | License (preliminary) | Status | Notes |
|---|---|---|---|---|
| react 19.3.1 | UI library | MIT | Planned | Shipped in the production bundle. |
| react-dom 19.3.1 | React DOM renderer | MIT | Planned | Shipped in the production bundle. |
| scheduler 0.28.0 | React dependency | MIT | Planned | Transitive; shipped in the production bundle. |
| vite 8.3.8 | Build tool and development server | MIT | Planned | Development only. |
| @vitejs/plugin-react 6.3.0 | React support for Vite | MIT | Planned | Development only. |
| @types/react, @types/react-dom, @types/node | Type definitions | MIT | Planned | Development only. |
| react-router 8.5.1 | Routing | MIT | Planned | Shipped in the production bundle. |
| @remix-run/route-pattern 0.22.1 | React Router dependency | MIT | Planned | Transitive; shipped in the production bundle. |
| cookie-es 3.1.1 | React Router dependency | MIT | Planned | Transitive; shipped in the production bundle. |
| tailwindcss 4.3.5 | Utility-first CSS framework | MIT | Planned | Development only. Generates CSS at build time; only the generated CSS is shipped. |
| @tailwindcss/vite 4.3.5 | Official Tailwind CSS integration for Vite | MIT | Planned | Development only. |
| oxlint 1.93.0 | Linter | MIT | Planned | Development only. Platform-specific binaries (`@oxlint/binding-*`, MIT); bundled components to be verified during review. |
| oxlint-tsgolint 7.0.2007 | Type-aware lint rules for Oxlint, built on TypeScript 7 | MIT | Planned | Development only. Platform-specific binaries (`@oxlint-tsgolint/*`, MIT); bundled components to be verified during review. |
| prettier 3.10.1 | Code formatter | MIT | Planned | Development only. |
| prettier-plugin-tailwindcss 0.8.1 | Tailwind CSS class sorting for Prettier | MIT | Planned | Development only. |
| vitest 5.1.0 | Test runner | MIT | Planned | Development only (DECISIONS.md D-047). |
| jsdom 31.0.1 | Browser environment for tests | MIT | Planned | Development only. Requires Node.js 22.22.2 or later. |
| @testing-library/react 16.3.3, @testing-library/dom 10.4.2 | Component tests | MIT | Planned | Development only. |
| @testing-library/user-event 14.6.12 | Simulated user interaction in tests | MIT | Planned | Development only. |
| @testing-library/jest-dom 7.0.1 | DOM assertions for tests | MIT | Planned | Development only. |

Transitive development dependencies (build time only, not shipped in the production bundle):

- rolldown, postcss, picomatch, tinyglobby, fdir, nanoid, csstype, undici-types and the platform-specific TypeScript and rolldown binaries: MIT or Apache-2.0.
- source-map-js: BSD-3-Clause. picocolors: ISC. detect-libc: Apache-2.0. tslib: 0BSD.
- Tailwind CSS build dependencies: @tailwindcss/node, @tailwindcss/oxide and its platform-specific binaries, enhanced-resolve, jiti, magic-string, tapable and @jridgewell/*: MIT.
- graceful-fs: BlueOak-1.0.0 (Blue Oak Model License, a permissive licence).
- **lightningcss (MPL-2.0)**, a CSS transformer used by Vite and Tailwind CSS. MPL-2.0 is a file-level copyleft licence. It is used unmodified as a build tool and is not included in the shipped bundle. **Requires licence review.**
- Some optional WebAssembly fallback packages (`@emnapi/*`) are pre-release versions. They are not installed on Windows, macOS or Linux x64.

Transitive test dependencies (development only, never shipped; 62 packages added with the testing tools):

- MIT: Vitest internals (@vitest/mocker, @vitest/spy, chai, tinybench, tinyexec, std-env, obug, es-module-lexer, why-is-node-running and their type packages), jsdom internals (parse5, parse5-parser-stream, data-urls, whatwg-url, whatwg-mimetype, tr46, w3c-xmlserializer, html-encoding-sniffer, decimal.js, undici, tldts, tldts-core, @exodus/bytes, bcp-47, bcp-47-match, is-alphabetical, is-alphanumerical, is-decimal, is-potential-custom-element-name, punycode, xmlchars, @adobe/css-tools, css.escape), Testing Library internals (dom-accessibility-api, pretty-format, react-is, lz-string, dequal, redent, strip-indent, indent-string, min-indent, ansi-regex, ansi-styles, @babel/code-frame, @babel/helper-validator-identifier, @babel/runtime, js-tokens), and estree-walker, assertion-error.
- Apache-2.0: aria-query, expect-type, xml-name-validator. BSD-2-Clause: entities, webidl-conversions. BSD-3-Clause: tough-cookie. ISC: saxes. BlueOak-1.0.0: lru-cache.

## Testing Tools

| Tool | Purpose | License (preliminary) | Status | Notes |
|---|---|---|---|---|
| Pytest 9.2 | Backend tests | MIT | Planned | Development dependency only. Installed in `apps/backend`; configured in `pyproject.toml` (DECISIONS.md D-045). |
| httpx2 2.16 | HTTP client used by the FastAPI/Starlette TestClient | BSD-3-Clause | **Approved** | Approved in the Phase 1.3 Bundle 1 review. Development dependency only. Starlette 1.10 deprecates `httpx` for its TestClient in favour of `httpx2` (same author, Pydantic organisation). |
| Vitest 5.1 | Frontend unit and component tests | MIT | Planned | Development dependency only. Installed in `apps/frontend`; see Frontend Packages (DECISIONS.md D-047). |
| React Testing Library 16, user-event 14, jest-dom 7 | Frontend component tests | MIT | Planned | Development dependencies only; see Frontend Packages. |
| jsdom 31 | Browser environment for frontend tests | MIT | Planned | Development dependency only. |
| Playwright | End-to-end tests | Apache-2.0 | Planned | Development dependency only. Downloaded browser binaries carry their own licences. |
| Playwright (`@playwright/test` 1.64.1) | End-to-end browser tests | Apache-2.0 | Planned | Development dependency of `apps/frontend`, pinned exactly (DECISIONS.md D-073). Chromium is downloaded by `npx playwright install chromium` into the developer's cache; it is not part of the repository or any image. |

## Continuous Integration

Used only on GitHub-hosted runners (DECISIONS.md D-048). Nothing here is distributed with AEGIS.

| Component | Purpose | License | Status | Notes |
|---|---|---|---|---|
| actions/checkout 7.0.1 | Check out the repository | MIT | Planned | Pinned to commit `3d3c42e5aac5ba805825da76410c181273ba90b1`. |
| actions/setup-python 7.1.0 | Install Python 3.11 | MIT | Planned | Pinned to commit `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0`. |
| actions/setup-node 7.1.0 | Install Node.js | MIT | Planned | Pinned to commit `949feb2413d6458794dcd2491c4babbbce0c15c1`. |
| PostgreSQL 18 (apt.postgresql.org) | Server binaries for the disposable test cluster | PostgreSQL License | Planned | Installed on the CI runner only, from the PostgreSQL project's signed apt repository. |

## Container Images

All images are pinned by digest in `docker-compose.yml` and the Dockerfiles (DECISIONS.md D-051). AEGIS publishes no images (D-059); the images below are pulled by users from their publishers, and AEGIS's own images are built locally from them.

| Image | Purpose | License (preliminary) | Status | Notes |
|---|---|---|---|---|
| `postgres:18.7-trixie` (Docker Official Image) | Database | PostgreSQL License, plus Debian package licences | Planned | Used as published; not redistributed by AEGIS. |
| `valkey/valkey:9.1.3-alpine` (Valkey project) | Message broker | BSD-3-Clause, plus Alpine package licences | Planned | Used as published; not redistributed by AEGIS. |
| `python:3.11.18-slim-trixie` (Docker Official Image) | Base of the backend image | PSF-2.0, plus Debian package licences | Planned | The Debian base includes GPL-licensed packages. **If AEGIS publishes images built on it, source-availability obligations for those packages apply** and must be addressed before publishing. |
| `node:22.23.5-trixie-slim` (Docker Official Image) | Build stage of the frontend image only | MIT, plus Debian package licences | Planned | Not part of the final frontend image. |
| `nginxinc/nginx-unprivileged:1.30.6-alpine` (NGINX, Inc.) | Base of the frontend image | BSD-2-Clause (nginx), plus Alpine package licences | Planned | Same publication caveat as the Python base. |

## Argon2 Licence Review

Reviewed on 2026-11-17 for argon2-cffi 25.1.0 and argon2-cffi-bindings 26.1.0, the versions in both lock files (DECISIONS.md D-062).

- **argon2-cffi 25.1.0:** pure Python, MIT. Pure-Python wheel; the PyPI hash matches the lock files.
- **argon2-cffi-bindings 26.1.0:** MIT (the only licence file in the wheel). Wheels are `cp310-abi3` for `manylinux_2_26`/`manylinux_2_28` on x86_64 and aarch64, and `win_amd64`; every hash in the lock files matches PyPI. The backend image (Debian, glibc) installs the binary wheel; no compiler is needed.
- **libargon2 (bundled):** the bindings compile the Argon2 reference implementation (phc-winner-argon2, git submodule at commit `f57e61e`) into the extension module. Upstream licence: **CC0-1.0 OR Apache-2.0**, at the user's choice. The wheel does not include this licence text. AEGIS relies on the Apache-2.0 option, which is compatible with AEGIS's licence; the attribution below is the required notice when the library is distributed, for example in an image.
- **cffi 2.1.1:** MIT-0. **pycparser 3.12:** BSD-3-Clause.
- pip-audit reports no known vulnerabilities for these versions.

Attribution: *Argon2 reference implementation, Copyright 2015 Daniel Dinu, Dmitry Khovratovich, Jean-Philippe Aumasson and Samuel Neves, dual licensed under CC0 1.0 and the Apache License 2.0 (https://github.com/P-H-C/phc-winner-argon2).*

## Not Yet Selected

The following have not been chosen and are therefore not listed as dependencies:

- DNS library (Phase 03).
- PDF generation library (Phase 05).
- Frontend data-fetching library.

## Security Assessment Integrations

| Tool | License | Status | Notes |
|---|---|---|---|
| Nmap | Nmap Public Source License (NPSL) | Deferred | The NPSL addresses software designed to execute Nmap and parse its results. Not bundled or integrated in the MVP. |
| Scapy | GPL-2.0 | Deferred | Not included in the MVP. |
| OWASP ZAP | Apache-2.0 | Deferred | Candidate for an optional, isolated integration after v0.1.0. |

## License Verification

The licences listed above are preliminary references.

The exact licence and redistribution obligations must be verified against the selected dependency version and distribution before release.

This document must be updated whenever dependencies are added, removed or upgraded.

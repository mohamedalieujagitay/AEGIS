# picomatch 4.0.7 — AEGIS security patch

This directory is the published `picomatch@4.0.7` package with one security fix.
It replaces every `picomatch` dependency of the frontend through the `overrides`
entry in `apps/frontend/package.json`. It is a development and build dependency
(Vite, Vitest, tinyglobby, fdir); nothing from it ships in the frontend image,
which contains only the built files.

## Why

GHSA-fc5q-39xc-vjpf / CVE-2026-112366: picomatch through 4.0.7 compiles a
repeated extglob (`+(...)` or `*(...)`) whose branch contains a bare `*` into a
regular expression with a nested unbounded quantifier. Matching it against a
short crafted string backtracks exponentially and blocks the event loop. The
guard that picomatch has for this only examines patterns with more than one
branch, so `+(*a)`, `+(*)` and `+(*.js)` are not caught. No fixed release exists
(`4.0.7` is the latest; the upstream fix pull requests are unmerged).

## Source

- Tarball: `https://registry.npmjs.org/picomatch/-/picomatch-4.0.7.tgz`
- Integrity (verified before patching):
  `sha512-qcJu88Q2IWqJsDD529JKMdwGm/dvInW4HvQnRwiH9JtihJvzGOscDtHE3x1pBKeUOTysQ8kVmLnJ2kJu7yhcGA==`
- The library files are identical to the upstream source at tag `4.0.7`.
- Licence: MIT, unchanged (`LICENSE`).

## Changes from the published package

1. `lib/parse.js`: one guard inserted before the final `return { risky: false };`
   of `analyzeRepeatedExtglob`. The exact text is
   `apps/frontend/scripts/picomatch-guard.js.txt`. A repeated extglob is reported
   as risky when a branch:
   - contains a star that is neither escaped, inside a bracket expression, nor the
     start of a nested extglob (`*(`), for example `+(*a)`; or
   - is exactly one nested group whose alternatives picomatch's own multi-branch
     rules flag (empty, star-only or overlapping), for example `+(@(a|aa))`.
   picomatch then matches it as literal text: the treatment it already gives the
   risky multi-branch patterns.
2. `package.json`: the `devDependencies`, `scripts` and `verb` fields are
   removed. npm installs the development dependencies of a linked directory, and
   these are only needed to develop picomatch itself.

No other file is changed.

## Behaviour difference

Patterns with a bare star inside a repeated extglob, and repeated extglobs that
wrap one group of overlapping alternatives, no longer act as extglobs: `+(*)c`,
`*(a*|b)`, `*/*(W*, *)*` and `+(@(a|aa))` match only their literal text. These
are the shapes that backtrack exponentially. Four of the 1,983 tests in picomatch's
own suite assert the old behaviour for such patterns and fail with this patch;
the other 1,979 pass. AEGIS's own configuration contains no such pattern.

## The bundled copies

Prettier and Playwright bundle an older copy of picomatch inside their own files,
which no npm override can replace. `scripts/picomatch-security-patch.mjs apply`
(run on `postinstall`) inserts the same guard into them; each file is pinned to
an exact package version and the SHA-256 of the unpatched file, so an upgrade is
refused until it has been reviewed.

## Verification

`npm run security:picomatch` scans every installed JavaScript file for a copy of
the picomatch engine. It fails unless `node_modules/picomatch` resolves to this
directory and the copies found are exactly the expected three (this package and
the two bundles), each carrying the guard, at its reviewed version and matching
the SHA-256 of its reviewed patched file. CI runs it after every clean install.

## Removal

When picomatch publishes a fixed release that Vite, Vitest, Prettier and
Playwright adopt, delete this directory, the `picomatch` entries in
`devDependencies` and `overrides`, the `postinstall` and `security:picomatch`
scripts and `scripts/picomatch-*`, then run `npm install`.

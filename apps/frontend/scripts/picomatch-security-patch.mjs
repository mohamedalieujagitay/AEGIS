/**
 * Security patch for GHSA-fc5q-39xc-vjpf / CVE-2026-112366 (picomatch <= 4.0.7).
 *
 * picomatch has no fixed release. AEGIS installs a patched copy of 4.0.7 for the
 * `picomatch` package (vendor/picomatch, through an npm override) and applies the
 * same guard to the two copies that Prettier and Playwright bundle inside their
 * own files, which no npm override can replace.
 *
 *   node scripts/picomatch-security-patch.mjs apply    patches the pinned bundles (postinstall)
 *   node scripts/picomatch-security-patch.mjs verify   fails unless every copy is the reviewed, patched one
 *
 * Each bundle is pinned to an exact package version, to the SHA-256 of its
 * unpatched file (checked before patching) and to the SHA-256 of the patched
 * file (checked by `verify`). Any other version or content is refused: an
 * upgrade has to be reviewed and the pins updated, never patched blindly.
 * See docs/architecture/DECISIONS.md D-076.
 */
import { createHash } from 'node:crypto'
import { readFileSync, readdirSync, realpathSync, writeFileSync } from 'node:fs'
import { dirname, join, relative, sep } from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'

/** Report a line of output; this is a command-line tool. */
const say = (text) => process.stdout.write(`${text}\n`)
const warn = (text) => process.stderr.write(`${text}\n`)

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const MODULES = join(ROOT, 'node_modules')
const MARKER = 'AEGIS security patch for GHSA-fc5q-39xc-vjpf'
// The guard ends with one blank line, which separates it from the code after it.
const GUARD = `${readFileSync(join(ROOT, 'scripts', 'picomatch-guard.js.txt'), 'utf8')
  .replace(/\r\n/g, '\n')
  .trimEnd()}\n\n`

const BUNDLES = [
  {
    pkg: 'prettier',
    version: '3.10.1',
    file: 'index.mjs',
    sha256: 'efa4ff19afa80e7e5531273138ffe61dd0749d36c14a5299dfc742d5e2363171',
    patched: 'cd4ce0c0d5e164c5d21997e8e1ee11ebb90694dd872e6e550796f61279efaa23',
  },
  {
    pkg: 'playwright',
    version: '1.64.1',
    file: 'lib/matchers/expect.js',
    sha256: '0e5d49c2c2b2fb2a20f60726153cb0bd109d0124394029035f43497a82b05eed',
    patched: '1f113dbf986084ca15d6ba552690f167368ed1a4d7130c3140a91cfb0ce2da60',
  },
]

/** The vendored, patched picomatch 4.0.7 (vendor/picomatch/AEGIS-PATCH.md). */
const VENDORED = {
  file: join('vendor', 'picomatch', 'lib', 'parse.js'),
  patched: 'b4af7ed9cdb204ce8034358ac10820b3486db7dc1b679688444a6062c0b80c53',
}

function sha256(text) {
  return createHash('sha256').update(text).digest('hex')
}

const DEFINITION = /analyzeRepeatedExtglob = \(body, [\w$]+\) => \{/g

/**
 * Insert the guard before the final `return { risky: false };` of
 * analyzeRepeatedExtglob, where `branches` is in scope. Works for the 4.0.7
 * source and for the older picomatch that the bundles contain (parameter names
 * may be renamed by the bundler); refuses anything else.
 */
function insertGuard(source, label) {
  const matches = [...source.matchAll(DEFINITION)]
  if (matches.length !== 1) {
    throw new Error(
      `${label}: expected one analyzeRepeatedExtglob definition, found ${matches.length}`,
    )
  }
  const start = matches[0].index
  const lineStart = source.lastIndexOf('\n', start) + 1
  const indent = /^\s*/.exec(source.slice(lineStart, start))[0]
  const end = source.indexOf(`\n${indent}};`, start)
  const anchor = end < 0 ? -1 : source.lastIndexOf('return { risky: false };', end)
  const body = source.slice(start, end)
  if (end < 0 || anchor < start || !body.includes('const branches = ')) {
    throw new Error(`${label}: the expected structure of analyzeRepeatedExtglob was not found`)
  }
  const anchorLine = source.lastIndexOf('\n', anchor) + 1
  const inner = source.slice(anchorLine, anchor)
  const guard = GUARD.split('\n')
    .map((line) => (line ? inner + line.replace(/^ {2}/, '') : line))
    .join('\n')
  return source.slice(0, anchorLine) + guard + source.slice(anchorLine)
}

function apply() {
  for (const target of BUNDLES) {
    const directory = join(MODULES, target.pkg)
    const { version } = JSON.parse(readFileSync(join(directory, 'package.json'), 'utf8'))
    if (version !== target.version) {
      throw new Error(
        `${target.pkg} ${version} is not the reviewed version ${target.version}: review its bundled picomatch and update the pins in ${relative(ROOT, fileURLToPath(import.meta.url))}`,
      )
    }
    const file = join(directory, target.file)
    const source = readFileSync(file, 'utf8')
    if (source.includes(MARKER)) {
      say(`${target.pkg} ${version}: bundled picomatch already patched`)
      continue
    }
    const digest = sha256(source)
    if (digest !== target.sha256) {
      throw new Error(
        `${relative(ROOT, file)} is not the reviewed file (sha256 ${digest}); not patched`,
      )
    }
    writeFileSync(file, insertGuard(source, relative(ROOT, file)))
    say(`${target.pkg} ${version}: bundled picomatch patched`)
  }
}

/** A copy of the picomatch engine: its regex constants or its extglob analysis. */
const ENGINE = /POSIX_REGEX_SOURCE|analyzeRepeatedExtglob/

/** Every installed JavaScript file that contains a copy of the picomatch engine. */
function findCopies(directory, found = []) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name)
    if (entry.isDirectory()) {
      findCopies(path, found)
    } else if (/\.(c|m)?js$/.test(entry.name) && ENGINE.test(readFileSync(path, 'utf8'))) {
      found.push(path)
    }
  }
  return found
}

function normalise(text) {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .join('\n')
}

function count(haystack, needle) {
  return haystack.split(needle).length - 1
}

/**
 * Fails unless:
 * - node_modules/picomatch resolves to the vendored copy;
 * - every installed copy of the engine defines analyzeRepeatedExtglob with the guard;
 * - the copies found are exactly the expected ones (the vendored package and the
 *   two pinned bundles), each at its reviewed version and patched SHA-256.
 * Any other engine copy, guarded or not, is reported: it has not been reviewed.
 */
function verify() {
  const guard = normalise(GUARD)
  const copies = [...new Set([...findCopies(MODULES), ...findCopies(join(ROOT, 'vendor'))])]
  const problems = []
  const resolved = realpathSync(join(MODULES, 'picomatch'))
  if (!resolved.endsWith(`${sep}vendor${sep}picomatch`)) {
    problems.push(`node_modules/picomatch resolves to ${resolved}, not vendor/picomatch`)
  }

  const expected = new Map([[join(ROOT, VENDORED.file), VENDORED.patched]])
  for (const target of BUNDLES) {
    const directory = join(MODULES, target.pkg)
    const { version } = JSON.parse(readFileSync(join(directory, 'package.json'), 'utf8'))
    if (version !== target.version) {
      problems.push(`${target.pkg} ${version} is not the reviewed version ${target.version}`)
    }
    expected.set(join(directory, target.file), target.patched)
  }

  let engines = 0
  const seen = new Set()
  for (const file of copies) {
    const source = readFileSync(file, 'utf8')
    const definitions = [...source.matchAll(DEFINITION)].length
    const label = relative(ROOT, file)
    if (definitions === 0) {
      // A constants-only module of the vendored package is fine; anything else is an unknown engine.
      if (!file.startsWith(join(ROOT, 'vendor', 'picomatch'))) {
        problems.push(`${label}: picomatch engine without analyzeRepeatedExtglob (unknown version)`)
      }
      continue
    }
    engines += definitions
    const guarded = count(normalise(source), guard)
    say(`  ${label}: ${definitions} definition(s), ${guarded} guarded`)
    if (guarded !== definitions) {
      problems.push(`${label}: ${definitions - guarded} unguarded copy(ies) of picomatch`)
    }
    if (!expected.has(file)) {
      problems.push(`${label}: unexpected copy of picomatch (not reviewed)`)
      continue
    }
    seen.add(file)
    const digest = sha256(source)
    if (digest !== expected.get(file)) {
      problems.push(`${label}: content differs from the reviewed patched file (sha256 ${digest})`)
    }
  }
  for (const file of expected.keys()) {
    if (!seen.has(file)) {
      problems.push(`${relative(ROOT, file)}: expected copy of picomatch not found`)
    }
  }
  say(`picomatch engine copies found: ${engines} (expected ${expected.size})`)
  if (problems.length > 0) {
    for (const problem of problems) {
      warn(`UNPATCHED: ${problem}`)
    }
    process.exit(1)
  }
  say('every installed copy of picomatch is the reviewed, patched copy')
}

const command = process.argv[2]
if (command === 'apply') {
  apply()
} else if (command === 'verify') {
  verify()
} else {
  warn('usage: node scripts/picomatch-security-patch.mjs apply|verify')
  process.exit(2)
}

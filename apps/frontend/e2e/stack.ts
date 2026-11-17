import { spawn } from 'node:child_process'

/**
 * Operations the browser tests cannot perform through the web interface:
 * creating accounts without public registration, expiring a trusted device
 * and deactivating an account. They run inside the stack's own containers,
 * with fixed program arguments (never a shell), and only when the environment
 * names a Compose project. The smoke test sets it for its disposable stack.
 *
 * Passwords and SQL are passed on standard input, never on a command line.
 */
export interface Stack {
  project: string
  composeFile: string
}

/** The stack the tests may change, if the environment names one. */
export function disposableStack(): Stack | undefined {
  const project = process.env['AEGIS_E2E_COMPOSE_PROJECT']
  const composeFile = process.env['AEGIS_E2E_COMPOSE_FILE']
  if (!project || !composeFile) {
    return undefined
  }
  if (project === 'aegis') {
    // The developer's own stack holds real data; never a test target.
    throw new Error('AEGIS_E2E_COMPOSE_PROJECT must not name the development project "aegis"')
  }
  return { project, composeFile }
}

interface Output {
  code: number | null
  stdout: string
  stderr: string
}

function compose(stack: Stack, service: string, args: string[], stdin?: string): Promise<Output> {
  return new Promise((resolve, reject) => {
    const child = spawn(
      'docker',
      ['compose', '-p', stack.project, '-f', stack.composeFile, 'exec', '-T', service, ...args],
      { stdio: ['pipe', 'pipe', 'pipe'], env: process.env, windowsHide: true },
    )
    let stdout = ''
    let stderr = ''
    child.stdout.on('data', (chunk: Buffer) => (stdout += chunk.toString('utf8')))
    child.stderr.on('data', (chunk: Buffer) => (stderr += chunk.toString('utf8')))
    child.on('error', reject)
    child.on('close', (code) => resolve({ code, stdout, stderr }))
    child.stdin.end(stdin ?? '')
  })
}

async function mustSucceed(output: Output, what: string): Promise<string> {
  if (output.code !== 0) {
    // stderr from the CLI and from psql never contains the input that was sent.
    throw new Error(`${what} failed (exit ${output.code}): ${output.stderr.trim().slice(-500)}`)
  }
  return output.stdout
}

/** Create an account with the administration CLI (no public registration, no rate limit). */
export async function createAccountWithCli(
  stack: Stack,
  account: { email: string; username: string; password: string },
): Promise<void> {
  const output = await compose(
    stack,
    'backend',
    [
      'python',
      '-m',
      'app.cli',
      'create-user',
      '--email',
      account.email,
      '--username',
      account.username,
      '--password-stdin',
    ],
    `${account.password}\n`,
  )
  await mustSucceed(output, 'create-user')
}

/**
 * Run SQL against the disposable database. ``vars`` are passed to psql with -v
 * and referenced in the SQL as :'name', so values are quoted by psql, not by us.
 */
export async function runSql(
  stack: Stack,
  sql: string,
  vars: Record<string, string> = {},
): Promise<string> {
  const variables = Object.entries(vars).flatMap(([name, value]) => ['-v', `${name}=${value}`])
  const output = await compose(
    stack,
    'postgres',
    [
      'psql',
      '--username=postgres',
      '--dbname=aegis',
      '--tuples-only',
      '--no-align',
      '-v',
      'ON_ERROR_STOP=1',
      ...variables,
      '-f',
      '-',
    ],
    sql,
  )
  return mustSucceed(output, 'database statement')
}

/** Deactivate an account with the service function the application itself uses (D-070). */
export async function deactivateAccount(stack: Stack, email: string): Promise<void> {
  const script = [
    'import sys',
    'from app.core.clock import utcnow',
    'from app.core.config import get_settings',
    'from app.core.identity import normalize_email',
    'from app.database.session import Database',
    'from app.services import accounts',
    'database = Database(get_settings())',
    'with database.session() as db:',
    '    user = accounts.find_user_by_email(db, normalize_email(sys.argv[1]))',
    '    if user is None:',
    '        raise SystemExit("no such account")',
    '    accounts.deactivate(db, user, utcnow())',
    'database.dispose()',
  ].join('\n')
  const output = await compose(stack, 'backend', ['python', '-c', script, email])
  await mustSucceed(output, 'deactivate')
}
